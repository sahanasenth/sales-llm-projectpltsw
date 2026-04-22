# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import EnquiryViewSet, CustomerViewSet, AppointmentViewSet, FeedbackViewSet

# router = DefaultRouter()
# router.register(r'enquiry', EnquiryViewSet)
# router.register(r'customer', CustomerViewSet)
# router.register(r'appointment', AppointmentViewSet)
# router.register(r'feedback', FeedbackViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
# ]

from django.urls import path
from .views import get_enquiries, create_enquiry

urlpatterns = [
    path('enquiry/', get_enquiries),
    path('enquiry/create/', create_enquiry),
]



