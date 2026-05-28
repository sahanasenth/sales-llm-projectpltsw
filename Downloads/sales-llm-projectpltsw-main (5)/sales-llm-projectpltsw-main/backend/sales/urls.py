from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView
from .views import (
    get_enquiries,
    create_enquiry,
    get_appointments,
    create_appointment,
    get_feedback,
    create_feedback,
    chat_api,
    health_api,
    suggestions_api,
    reset_chat_api,
    UserRegistrationView
)

urlpatterns = [

    path('enquiry/', get_enquiries, name='get_enquiries'),
    path('enquiry/create/', create_enquiry, name='create_enquiry'),

    path('appointment/', get_appointments, name='get_appointments'),
    path('appointment/create/', create_appointment, name='create_appointment'),

    path('feedback/', get_feedback, name='get_feedback'),
    path('feedback/create/', create_feedback, name='create_feedback'),

    path('chat/', chat_api, name='chat_api'),

    path('health/', health_api, name='health_api'),

    path('suggestions/', suggestions_api, name='suggestions_api'),

    path('reset/', reset_chat_api, name='reset_chat_api'),

    path('register/', UserRegistrationView.as_view(), name='user-registration'),

    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]