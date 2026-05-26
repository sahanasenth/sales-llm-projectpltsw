from django.contrib import admin
from django.urls import path, include
from sales.views import home, CustomTokenObtainPairView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('', home),

    path('admin/', admin.site.urls),

    path('api/', include('sales.urls')),

    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
