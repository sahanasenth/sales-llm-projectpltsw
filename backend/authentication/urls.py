from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import LoginView, LogoutView, RegisterView, ProfileView, RoleAssignmentView

# ─────────────────────────────────────────────────────────────
#  URL map (all prefixed with /api/ in sales_project/urls.py)
#
#  Method   URL                   View               Auth Required
#  ──────   ───────────────────   ────────────────   ─────────────
#  POST     /api/token/           LoginView          No
#  POST     /api/token/refresh/   TokenRefreshView   No (uses refresh token)
#  POST     /api/token/verify/    TokenVerifyView    No (verifies a token)
#  POST     /api/logout/          LogoutView         Yes (access token)
#  POST     /api/register/        RegisterView       No
#  GET      /api/profile/         ProfileView        Yes (access token)
#  PATCH    /api/profile/         ProfileView        Yes (access token)
# ─────────────────────────────────────────────────────────────

urlpatterns = [
    # Login → returns access + refresh tokens
    path('token/', LoginView.as_view(), name='token_obtain_pair'),

    # Exchange refresh token for a new access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Verify whether a token is still valid
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Blacklist refresh token (server-side logout)
    path('logout/', LogoutView.as_view(), name='logout'),

    # Create a new user account
    path('register/', RegisterView.as_view(), name='register'),

    # View or update the authenticated user's profile
    path('profile/', ProfileView.as_view(), name='profile'),

    # Director-only role assignment
    path('users/<int:user_id>/role/', RoleAssignmentView.as_view(), name='assign_role'),
]
