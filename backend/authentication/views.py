from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .permissions import IsDirector
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    RoleAssignmentSerializer,
    UserProfileSerializer,
)

User = get_user_model()


def get_role_identity(user):
    return {
        'code': user.role_code,
        'label': user.role_label,
        'permissions': user.permissions,
    }


def get_auth_identity(user):
    role_identity = get_role_identity(user)
    return {
        'authenticated': True,
        'role': role_identity,
        'permissions': role_identity['permissions'],
    }


def generate_tokens_for_user(user):
    """
    Generate a new JWT access + refresh token pair for the given user.
    """
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role_code
    refresh['role_label'] = user.role_label
    refresh['permissions'] = user.permissions

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


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
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data['user']
        tokens = generate_tokens_for_user(user)
        auth_identity = get_auth_identity(user)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "tokens": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh'],
                },
                "auth": auth_identity,
                "role": auth_identity['role'],
                "permissions": auth_identity['permissions'],
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required for logout.",
                    "error": "Missing 'refresh' field in request body.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response(
                {
                    "success": False,
                    "message": "Logout failed.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Successfully logged out. Token has been invalidated.",
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    Creates a new user account and returns JWT tokens immediately.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Registration failed. Please fix the errors below.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = generate_tokens_for_user(user)
        auth_identity = get_auth_identity(user)

        return Response(
            {
                "success": True,
                "message": f"Account created successfully. Welcome, {user.username}!",
                "tokens": {
                    "access": tokens['access'],
                    "refresh": tokens['refresh'],
                },
                "auth": auth_identity,
                "role": auth_identity['role'],
                "permissions": auth_identity['permissions'],
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(APIView):
    """
    Returns or updates the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Profile retrieved successfully.",
                "user": UserProfileSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Profile update failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class RoleAssignmentView(APIView):
    """
    Assigns a role to a user. Only Directors can change roles.
    """
    permission_classes = [IsAuthenticated, IsDirector]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "User not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RoleAssignmentSerializer(user, data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Role assignment failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        return Response(
            {
                "success": True,
                "message": f"Role updated successfully for {user.username}.",
                "role": get_role_identity(user),
                "permissions": user.permissions,
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
