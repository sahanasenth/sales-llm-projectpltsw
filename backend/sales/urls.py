from django.urls import path
from .views import (
    get_enquiries,
    create_enquiry,
    get_appointments,
    create_appointment,
    get_feedback,
    create_feedback,
    chat_api
)

urlpatterns = [
    path('enquiry/', get_enquiries, name='get_enquiries'),
    path('enquiry/create/', create_enquiry, name='create_enquiry'),

    path('appointment/', get_appointments, name='get_appointments'),
    path('appointment/create/', create_appointment, name='create_appointment'),

    path('feedback/', get_feedback, name='get_feedback'),
    path('feedback/create/', create_feedback, name='create_feedback'),

    path('chat/', chat_api, name='chat_api'),
]
