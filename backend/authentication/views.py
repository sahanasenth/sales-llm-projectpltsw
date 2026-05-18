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
#  Creates a JWT token pair for any given user.
# ─────────────────────────────────────────────────────────────
def generate_tokens_for_user(user):
    """
    Generate a new JWT access + refresh token pair for the given user.

    RefreshToken.for_user(user) is a SimpleJWT method that:
      1. Creates a new RefreshToken linked to this user
      2. Embeds user_id into the token payload
      3. Signs it with the SECRET_KEY using HS256
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ─────────────────────────────────────────────────────────────
#  LoginView  — POST /api/token/
#  Permission: AllowAny (this IS the login endpoint)
# ─────────────────────────────────────────────────────────────
class LoginView(APIView):
    """
    Authenticates a user and returns JWT access + refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Login failed. Please check your credentials.",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']
        tokens = generate_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

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
#  LogoutView  — POST /api/logout/
#  Permission: IsAuthenticated (must send valid access token)
#
#  Blacklists the refresh token so it can no longer be used
#  to generate new access tokens (server-side logout).
# ─────────────────────────────────────────────────────────────
class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.
    Requires: Authorization: Bearer <access_token>
    Body:      { "refresh": "<refresh_token>" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
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
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "success": True,
                    "message": "Successfully logged out. Token has been invalidated."
                },
                status=status.HTTP_200_OK
            )

        except TokenError as e:
            return Response(
                {
                    "success": False,
                    "message": "Logout failed.",
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# ─────────────────────────────────────────────────────────────
#  RegisterView  — POST /api/register/
#  Permission: AllowAny (no token needed to create an account)
# ─────────────────────────────────────────────────────────────
class RegisterView(APIView):
    """
    Creates a new user account and returns JWT tokens immediately.
    After registration the user is automatically logged in.
    """
    permission_classes = [AllowAny]

    def post(self, request):
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

        user = serializer.save()
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
#  ProfileView  — GET/PATCH /api/profile/
#  Permission: IsAuthenticated (PROTECTED — requires Bearer token)
# ─────────────────────────────────────────────────────────────
class ProfileView(APIView):
    """
    Returns or updates the authenticated user's profile.

    Protected endpoint:
      Client must send:  Authorization: Bearer <access_token>
      JWTAuthentication middleware decodes the token and sets request.user.
      Missing/invalid token returns 401 Unauthorized automatically.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/profile/ — return user profile."""
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
        """PATCH /api/profile/ — partial update of profile fields."""
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
