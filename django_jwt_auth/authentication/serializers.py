# =============================================================
#  authentication/serializers.py
#
#  Serializers serve two purposes in DRF:
#    1. DESERIALIZATION  → Validate incoming JSON request data
#    2. SERIALIZATION    → Convert Python objects to JSON for responses
#
#  Think of them as Django Forms for APIs.
# =============================================================

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


# ─────────────────────────────────────────────────────────────
#  LoginSerializer
#  Validates the incoming login credentials (username + password).
#
#  Flow:
#    1. Client sends POST /api/token/ with {username, password}
#    2. DRF passes the data to this serializer
#    3. validate() is called → authenticates against the DB
#    4. If valid, returns the authenticated User object
#    5. The view then uses SimplJWT to mint tokens for that user
# ─────────────────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials.
    Supports login by username OR email.
    """

    # ── Input Fields ─────────────────────────────────────────
    username = serializers.CharField(
        required=True,
        help_text="Enter your username or email address."
    )
    password = serializers.CharField(
        required=True,
        write_only=True,           # Password is NEVER included in response output
        style={'input_type': 'password'},
        help_text="Enter your password."
    )

    # ── Object-level Validation ──────────────────────────────
    def validate(self, data):
        """
        Called automatically after field-level validation passes.
        We use it to verify credentials against the database.

        Steps:
          1. Extract username & password from validated data
          2. Check if username is actually an email → look up username
          3. Call Django's authenticate() → verifies password hash
          4. Check if account is active
          5. Attach user to validated_data so the view can use it
        """
        username = data.get('username')
        password = data.get('password')

        # ── Support login via email ───────────────────────────
        # If the input looks like an email, find the matching username first
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username   # swap email → username for authenticate()
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"username": "No account found with this email address."}
                )

        # ── Authenticate against the database ─────────────────
        # Django's authenticate() handles password hash comparison internally.
        # It returns a User object if credentials are valid, else None.
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid credentials. Please check your username and password."}
            )

        # ── Check if account is active ────────────────────────
        # Admins can deactivate accounts (is_active=False) to block access.
        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "This account has been deactivated. Contact support."}
            )

        # ── Attach the authenticated user to validated data ───
        # The view accesses this as: serializer.validated_data['user']
        data['user'] = user
        return data


# ─────────────────────────────────────────────────────────────
#  UserProfileSerializer
#  Converts a Django User object → JSON for API responses.
#
#  Used by:  GET /api/profile/
#  Returns: Safe, public user data — never the password hash.
# ─────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the authenticated user's profile data.

    ModelSerializer automatically generates fields from the model.
    We explicitly list only the fields we want to expose.
    IMPORTANT: 'password' is intentionally excluded for security.
    """

    class Meta:
        model = User

        # Only expose safe, non-sensitive fields
        fields = [
            'id',           # Unique user ID (integer)
            'username',     # Login username
            'email',        # Email address
            'first_name',   # First name
            'last_name',    # Last name
            'is_staff',     # Is the user an admin?
            'date_joined',  # Account creation timestamp
            'last_login',   # Last successful login timestamp
        ]

        # All fields are read-only — this serializer is for output only
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────
#  RegisterSerializer
#  Validates and creates a new user account.
#
#  Used by:  POST /api/register/
#  Flow: validates → creates User → Django hashes password automatically
# ─────────────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.

    Key security feature: password is write_only — it is NEVER
    returned in any API response. Django's create_user() method
    automatically hashes the password using PBKDF2+SHA256 before
    storing it in the database. Plain text is never stored.
    """

    # ── Extra password fields ─────────────────────────────────
    password = serializers.CharField(
        write_only=True,           # Never included in response
        min_length=8,              # Basic length validation
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters."
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Repeat the same password for confirmation."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    # ── Field-level email validation ──────────────────────────
    def validate_email(self, value):
        """Ensure email is unique across all users."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    # ── Object-level validation ───────────────────────────────
    def validate(self, data):
        """Ensure both password fields match."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    # ── Object creation ───────────────────────────────────────
    def create(self, validated_data):
        """
        Create a new user securely.

        We pop password2 (not needed for DB) and use create_user()
        instead of create() because create_user() hashes the password
        before saving. Using create() directly would store plain text!
        """
        validated_data.pop('password2')   # Remove confirm-password field

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],  # Hashed internally by create_user()
        )
        return user
