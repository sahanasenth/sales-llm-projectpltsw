import pytest
from django.contrib.auth import get_user_model
from sales.models import Enquiry, Appointment, Feedback, Profile

@pytest.mark.django_db
class TestSalesModels:
    
    def test_create_profile(self):
        # Verify Profile creation and relationships
        User = get_user_model()
        user = User.objects.create_user(username="testuser", password="testpassword")
        profile = Profile.objects.get(user=user)
        assert profile.role == 'sales'
        profile.role = 'director'
        profile.save()
        assert profile.role == 'director'

    def test_create_enquiry(self):
        # Unit test to verify Enquiry model fields and save
        enquiry = Enquiry.objects.create(
            enquiry_id="ENQ001",
            customer="John Doe",
            vehicle="Yamaha R15",
            temperature="Hot",
            status="New Lead",
            date="2026-05-28",
            source="Walk-in"
        )
        assert enquiry.enquiry_id == "ENQ001"
        assert enquiry.customer == "John Doe"
        assert enquiry.vehicle == "Yamaha R15"

    def test_create_appointment(self):
        # Verify Appointment creation
        appointment = Appointment.objects.create(
            appointment_id="APP001",
            customer="John Doe",
            vehicle="Yamaha R15",
            status="Scheduled",
            date="2026-05-28",
            time="10:00 AM"
        )
        assert appointment.appointment_id == "APP001"
        assert appointment.customer == "John Doe"
        assert appointment.time == "10:00 AM"

    def test_create_feedback(self):
        # Verify Feedback model
        feedback = Feedback.objects.create(
            feedback_id="FB001",
            enquiry_id="ENQ001",
            customer="John Doe",
            vehicle="Yamaha R15",
            status="Completed",
            date="2026-05-28"
        )
        assert feedback.feedback_id == "FB001"
        assert feedback.customer == "John Doe"
