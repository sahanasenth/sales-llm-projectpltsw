# =============================================================
#  authentication/urls.py
#
#  URL patterns for the 'authentication' app.
#  These are prefixed with /api/ in core/urls.py.
#
#  Full URL map:
#  ─────────────────────────────────────────────────────────────
#  Method   URL                   View                   Auth Required
#  ──────   ───────────────────   ────────────────────   ─────────────
#  POST     /api/token/           LoginView              No
#  POST     /api/token/refresh/   TokenRefreshView       No (uses refresh token)
#  POST     /api/token/verify/    TokenVerifyView        No (verifies a token)
#  POST     /api/logout/          LogoutView             Yes (access token)
#  POST     /api/register/        RegisterView           No
#  GET      /api/profile/         ProfileView            Yes (access token)
#  PATCH    /api/profile/         ProfileView            Yes (access token)
#  ─────────────────────────────────────────────────────────────
# =============================================================

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import LoginView, LogoutView, RegisterView, ProfileView

urlpatterns = [

    # ── Authentication Endpoints ──────────────────────────────

    # POST /api/token/
    # Accepts: { username, password }
    # Returns: { access, refresh, user }
    path('token/', LoginView.as_view(), name='token_obtain_pair'),

    # POST /api/token/refresh/
    # Accepts: { refresh: "<refresh_token>" }
    # Returns: { access: "<new_access_token>", refresh: "<new_refresh_token>" }
    # Note: SimplJWT's built-in view handles this automatically.
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # POST /api/token/verify/
    # Accepts: { token: "<any_token>" }
    # Returns: 200 OK if valid, 401 if expired or invalid
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # POST /api/logout/
    # Accepts: { refresh: "<refresh_token>" }
    # Blacklists the refresh token to prevent further use
    path('logout/', LogoutView.as_view(), name='logout'),

    # ── User Management Endpoints ─────────────────────────────

    # POST /api/register/
    # Accepts: { username, email, first_name, last_name, password, password2 }
    # Returns: { tokens, user }
    path('register/', RegisterView.as_view(), name='register'),

    # GET  /api/profile/  → View profile    (requires Bearer token)
    # PATCH /api/profile/ → Update profile  (requires Bearer token)
    path('profile/', ProfileView.as_view(), name='profile'),
]
