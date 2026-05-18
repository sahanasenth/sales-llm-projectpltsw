from django.contrib import admin
from django.urls import path, include
from sales.views import home

urlpatterns = [
    # Health-check / landing
    path('', home),

    # Django admin panel
    path('admin/', admin.site.urls),

    # Existing CRM APIs (publicly accessible — AllowAny set on each view)
    path('api/', include('sales.urls')),

    # JWT Authentication routes
    #   POST  /api/token/           → Login
    #   POST  /api/token/refresh/   → Refresh access token
    #   POST  /api/token/verify/    → Verify token
    #   POST  /api/logout/          → Logout (blacklist refresh token)
    #   POST  /api/register/        → Register new user
    #   GET   /api/profile/         → Protected user profile
    #   PATCH /api/profile/         → Update profile
    path('api/', include('authentication.urls')),
]
