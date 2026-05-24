import pytest
from datetime import date
from sales.models import Enquiry, Appointment, Feedback

@pytest.mark.django_db
class TestSalesModels:
    
    def test_create_enquiry(self):
        # Verify Enquiry model fields and data persistence
        enquiry = Enquiry.objects.create(
            enquiry_id="ENQ001",
            customer="Rithwik",
            vehicle="Fascino",
            temperature="Hot",
            status="Submitted",
            date=date.today(),
            source="Walk-in"
        )
        assert enquiry.enquiry_id == "ENQ001"
        assert enquiry.customer == "Rithwik"
        assert enquiry.vehicle == "Fascino"
        assert enquiry.temperature == "Hot"
        assert enquiry.status == "Submitted"

    def test_create_appointment(self):
        # Verify Appointment model creation
        appointment = Appointment.objects.create(
            appointment_id="APP001",
            customer="Rithwik",
            vehicle="Fascino",
            status="Scheduled",
            date=date.today(),
            time="10:00 AM"
        )
        assert appointment.appointment_id == "APP001"
        assert appointment.customer == "Rithwik"
        assert appointment.vehicle == "Fascino"
        assert appointment.status == "Scheduled"
        assert appointment.time == "10:00 AM"

    def test_create_feedback(self):
        # Verify Feedback model creation
        feedback = Feedback.objects.create(
            feedback_id="FB001",
            enquiry_id="ENQ001",
            customer="Rithwik",
            vehicle="Fascino",
            status="Submitted",
            date=date.today()
        )
        assert feedback.feedback_id == "FB001"
        assert feedback.enquiry_id == "ENQ001"
        assert feedback.customer == "Rithwik"
        assert feedback.vehicle == "Fascino"
        assert feedback.status == "Submitted"
