import pytest
from sales.models import Enquiry, Appointment, Feedback
from datetime import date

@pytest.mark.django_db
class TestSalesModels:
    
    def test_create_enquiry(self):
        """Unit test to verify Enquiry model constraints and data save."""
        enquiry = Enquiry.objects.create(
            enquiry_id="ENQ001",
            customer="John Doe",
            vehicle="FZ-S",
            temperature="Hot",
            status="New Lead",
            date=date(2026, 5, 26),
            source="Walk-in"
        )
        assert enquiry.enquiry_id == "ENQ001"
        assert enquiry.customer == "John Doe"
        assert enquiry.vehicle == "FZ-S"
        assert enquiry.status == "New Lead"

    def test_create_appointment(self):
        """Verify Appointment creation."""
        appointment = Appointment.objects.create(
            appointment_id="APP001",
            customer="John Doe",
            vehicle="FZ-S",
            status="Scheduled",
            date=date(2026, 5, 27),
            time="10:00 AM"
        )
        assert appointment.appointment_id == "APP001"
        assert appointment.customer == "John Doe"
        assert appointment.time == "10:00 AM"

    def test_create_feedback(self):
        """Verify Feedback model."""
        feedback = Feedback.objects.create(
            feedback_id="FB001",
            enquiry_id="ENQ001",
            customer="John Doe",
            vehicle="FZ-S",
            status="Submitted",
            date=date(2026, 5, 28)
        )
        assert feedback.feedback_id == "FB001"
        assert feedback.customer == "John Doe"
        assert feedback.status == "Submitted"
