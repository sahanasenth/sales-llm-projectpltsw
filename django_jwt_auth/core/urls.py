# =============================================================
#  core/urls.py
#  Root URL configuration — the "table of contents" of the API.
#
#  All app-level routes are registered here using include().
#  This keeps each app responsible for its own URL patterns.
# =============================================================

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ── Django Admin Panel ────────────────────────────────────
    # Access at: http://127.0.0.1:8000/admin/
    # Create a superuser to log in: python manage.py createsuperuser
    path('admin/', admin.site.urls),

    # ── Authentication & Profile APIs ─────────────────────────
    # All routes defined in authentication/urls.py are mounted here.
    # Prefix: /api/
    # This gives us:
    #   POST  /api/token/          → Login (get access + refresh tokens)
    #   POST  /api/token/refresh/  → Get new access token using refresh token
    #   POST  /api/token/verify/   → Verify if an access token is still valid
    #   POST  /api/logout/         → Blacklist refresh token (logout)
    #   GET   /api/profile/        → Protected profile endpoint
    path('api/', include('authentication.urls')),
]
