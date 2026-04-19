import pytest
from sales.models import Enquiry, Customer, Appointment, Feedback

@pytest.mark.django_db
class TestSalesModels:
    
    def test_create_enquiry(self):
        # Unit test to verify Enquiry model constraints and data save
        enquiry = Enquiry.objects.create(
            name="ENQ-001",
            phone_no="9876543210",
            vehicle_name="R15",
            down_payment=5000.00
        )
        assert enquiry.name == "ENQ-001"
        assert enquiry.phone_no == "9876543210"
        assert enquiry.down_payment == 5000.00

    def test_create_customer(self):
        # Verify Customer links to Enquiry correctly
        enquiry = Enquiry.objects.create(name="ENQ-002")
        customer = Customer.objects.create(
            name="John Doe",
            phone_no="1234567890",
            email="johndoe@example.com",
            address="123 Main St",
            enquiry=enquiry
        )
        assert customer.name == "John Doe"
        assert customer.enquiry.name == "ENQ-002"

    def test_create_appointment(self):
        # Verify Appointment creation and relationships
        enquiry = Enquiry.objects.create(name="ENQ-003")
        appointment = Appointment.objects.create(
            name="APT-001",
            sales_enquiry_id=enquiry,
            vehicle_name="FZ-X",
            date="2026-05-19"
        )
        assert appointment.name == "APT-001"
        assert appointment.sales_enquiry_id.name == "ENQ-003"
        assert str(appointment.date) == "2026-05-19"

    def test_create_feedback(self):
        # Verify Feedback model
        enquiry = Enquiry.objects.create(name="ENQ-004")
        feedback = Feedback.objects.create(
            name="FB-001",
            sales_enquiry_id=enquiry,
            customer="Jane Doe",
            vehicle_name="Fascino"
        )
        assert feedback.name == "FB-001"
        assert feedback.customer == "Jane Doe"
