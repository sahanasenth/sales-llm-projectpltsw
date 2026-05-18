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
#    5. The view then uses SimpleJWT to mint tokens for that user
# ─────────────────────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials.
    Supports login by username OR email.
    """

    username = serializers.CharField(
        required=True,
        help_text="Enter your username or email address."
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Enter your password."
    )

    def validate(self, data):
        """
        Called automatically after field-level validation passes.
        Verifies credentials against the database.
        """
        username = data.get('username')
        password = data.get('password')

        # Support login via email — swap email for username before authenticate()
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"username": "No account found with this email address."}
                )

        # Django's authenticate() handles password hash comparison internally
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors": "Invalid credentials. Please check your username and password."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "This account has been deactivated. Contact support."}
            )

        # Attach the authenticated user so the view can access it
        data['user'] = user
        return data


# ─────────────────────────────────────────────────────────────
#  UserProfileSerializer
#  Converts a Django User object → JSON for API responses.
#  IMPORTANT: 'password' is intentionally excluded for security.
# ─────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the authenticated user's profile data.
    Only exposes safe, non-sensitive fields — never the password hash.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'date_joined',
            'last_login',
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────
#  RegisterSerializer
#  Validates and creates a new user account.
#  Password is hashed by Django's create_user() — never stored plain.
# ─────────────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user registration with password confirmation.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
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

    def validate_email(self, value):
        """Ensure email is unique across all users."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """Ensure both password fields match."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """
        Create a new user securely using create_user() which hashes
        the password before storing. Never use create() directly for users.
        """
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )
        return user
