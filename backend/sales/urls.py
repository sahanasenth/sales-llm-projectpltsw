from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnquiryViewSet, CustomerViewSet, AppointmentViewSet, FeedbackViewSet

router = DefaultRouter()
router.register(r'enquiry', EnquiryViewSet)
router.register(r'customer', CustomerViewSet)
router.register(r'appointment', AppointmentViewSet)
router.register(r'feedback', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
