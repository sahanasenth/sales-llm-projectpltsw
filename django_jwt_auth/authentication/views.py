# =============================================================
#  authentication/views.py
#
#  Views define WHAT each API endpoint does when called.
#  We use class-based views (CBVs) throughout for:
#    - Clean structure & separation of concerns
#    - Easy override of HTTP method handlers (get/post/put/delete)
#    - Better DRF integration (generics, mixins)
#
#  Endpoints implemented here:
#    POST  /api/token/         → Login → returns access + refresh tokens
#    POST  /api/token/refresh/ → Exchange refresh token for new access token
#    POST  /api/token/verify/  → Verify if a token is still valid
#    POST  /api/logout/        → Blacklist refresh token (server-side logout)
#    POST  /api/register/      → Create a new user account
#    GET   /api/profile/       → Return the authenticated user's profile (PROTECTED)
# =============================================================

from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import LoginSerializer, UserProfileSerializer, RegisterSerializer


# ─────────────────────────────────────────────────────────────
#  Helper: generate_tokens_for_user()
#  A utility function that creates a JWT token pair for any user.
#
#  Returns:
#    {
#      "refresh": "<refresh_token_string>",
#      "access":  "<access_token_string>"
#    }
# ─────────────────────────────────────────────────────────────
def generate_tokens_for_user(user):
    """
    Generate a new JWT access + refresh token pair for the given user.

    RefreshToken.for_user(user) is a SimplJWT method that:
      1. Creates a new RefreshToken linked to this user
      2. Embeds user_id into the token payload
      3. Signs it with the SECRET_KEY using HS256

    We then derive the access token from the refresh token object.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),           # Long-lived → stored securely by client
        'access': str(refresh.access_token),  # Short-lived → sent in Authorization header
    }


# ─────────────────────────────────────────────────────────────
#  LoginView
#  POST /api/token/
#
#  Accepts: { "username": "...", "password": "..." }
#  Returns: { "access": "...", "refresh": "...", "user": {...} }
#
#  Permission: AllowAny → No token required (it's the login endpoint!)
# ─────────────────────────────────────────────────────────────
class LoginView(APIView):
    """
    Authenticates a user and returns JWT access + refresh tokens.

    This is the entry point of the JWT flow:
      1. Client sends credentials
      2. We validate them using LoginSerializer
      3. If valid, we generate tokens and return them
      4. Client stores tokens and sends access token in future requests
    """

    # Override global permission → login must be accessible without a token
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST /api/token/

        Steps:
          1. Pass request.data to LoginSerializer for validation
          2. If invalid → 400 with error details
          3. If valid → extract authenticated user from validated_data
          4. Generate JWT tokens for that user
          5. Return tokens + user profile in a clean JSON response
        """

        # ── Step 1: Validate incoming data ────────────────────
        # Pass 'context' so the serializer can access the request if needed
        serializer = LoginSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            # Return 400 Bad Request with field-level error messages
            return Response(
                {
                    "success": False,
                    "message": "Login failed. Please check your credentials.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── Step 2: Extract the validated user ────────────────
        # LoginSerializer.validate() sets data['user'] = authenticated User object
        user = serializer.validated_data['user']

        # ── Step 3: Generate JWT tokens ───────────────────────
        tokens = generate_tokens_for_user(user)

        # ── Step 4: Serialize user profile for the response ───
        user_data = UserProfileSerializer(user).data

        # ── Step 5: Return success response ───────────────────
        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "tokens": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh'],
                },
                "user": user_data
            },
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────────────────────
#  LogoutView
#  POST /api/logout/
#
#  Accepts: { "refresh": "<refresh_token>" }
#  Returns: { "success": true, "message": "Logged out." }
#
#  Permission: IsAuthenticated → Must send valid access token
#
#  HOW LOGOUT WORKS WITH JWT:
#  JWT tokens are stateless — the server doesn't "remember" them.
#  Simply deleting the token on the client side is NOT secure because
#  the refresh token could still be used to generate new access tokens.
#
#  Solution: Token Blacklisting
#  We add the refresh token to a database blacklist. SimplJWT checks
#  the blacklist before honoring any token rotation requests.
#  This requires 'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS.
# ─────────────────────────────────────────────────────────────
class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.

    After calling this endpoint:
      - The refresh token can no longer be used to generate new access tokens
      - Existing access tokens expire naturally (within 15 minutes)
      - The client should also delete both tokens from local storage
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST /api/logout/
        Expects: { "refresh": "<refresh_token_string>" }
        """
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required for logout.",
                    "error": "Missing 'refresh' field in request body."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse and blacklist the token
            # This stores the token's JTI (JWT ID) in the OutstandingToken table
            token = RefreshToken(refresh_token)
            token.blacklist()   # Adds to BlacklistedToken table

            return Response(
                {
                    "success": True,
                    "message": "Successfully logged out. Token has been invalidated."
                },
                status=status.HTTP_200_OK
            )

        except TokenError as e:
            # Token is already blacklisted, expired, or invalid
            return Response(
                {
                    "success": False,
                    "message": "Logout failed.",
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────────────────────
#  RegisterView
#  POST /api/register/
#
#  Accepts: { username, email, first_name, last_name, password, password2 }
#  Returns: { success, message, user, tokens }
#
#  Permission: AllowAny → No token needed to create an account
# ─────────────────────────────────────────────────────────────
class RegisterView(APIView):
    """
    Creates a new user account and returns JWT tokens immediately.

    After registration, the user is automatically "logged in" —
    they receive tokens so they don't need to call /api/token/ again.

    Security:
      - Password hashed by Django's create_user() (PBKDF2 + SHA256 + salt)
      - Plain text password is NEVER stored or returned
      - Email uniqueness is validated in RegisterSerializer
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST /api/register/"""

        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Registration failed. Please fix the errors below.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the user — password is hashed inside serializer.create()
        user = serializer.save()

        # Auto-generate tokens so user is immediately authenticated
        tokens = generate_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response(
            {
                "success": True,
                "message": f"Account created successfully. Welcome, {user.username}!",
                "tokens": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh'],
                },
                "user": user_data
            },
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────────────────────
#  ProfileView
#  GET /api/profile/
#
#  Returns: The authenticated user's profile data as JSON
#
#  Permission: IsAuthenticated ← PROTECTED ENDPOINT
#
#  HOW PROTECTION WORKS:
#  1. Client sends request with header:
#       Authorization: Bearer <access_token>
#  2. JWTAuthentication middleware intercepts the request
#  3. It decodes the token, validates the signature & expiry
#  4. If valid → sets request.user = authenticated User object
#  5. If invalid/missing → returns 401 Unauthorized automatically
#  6. IsAuthenticated permission then checks request.user.is_authenticated
# ─────────────────────────────────────────────────────────────
class ProfileView(APIView):
    """
    Returns the authenticated user's profile.

    This is an example of a PROTECTED endpoint — it can only be
    accessed with a valid JWT access token in the Authorization header.

    Unauthorized access returns:  401 Unauthorized
    Authorized access returns:    200 OK + user profile JSON
    """

    # IsAuthenticated is already the global default (set in settings.py)
    # We're being explicit here for clarity and documentation purposes
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET /api/profile/

        request.user is automatically set by JWTAuthentication
        when a valid access token is provided.
        We simply serialize it and return.
        """

        # request.user = the authenticated User object (set by JWT middleware)
        serializer = UserProfileSerializer(request.user)

        return Response(
            {
                "success": True,
                "message": "Profile retrieved successfully.",
                "user": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        """
        Handle PATCH /api/profile/
        Allows partial update of profile fields (first_name, last_name, email).
        """

        # partial=True → allows updating only some fields, not all
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Profile update failed.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "user": serializer.data
            },
            status=status.HTTP_200_OK
        )
