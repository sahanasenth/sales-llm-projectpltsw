import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from sales.models import Enquiry, Profile

@pytest.fixture
def authenticated_client():
    User = get_user_model()
    user = User.objects.create_user(username="salesexecutive", password="salespassword")
    profile = Profile.objects.get(user=user)
    profile.role = 'sales'
    profile.save()
    
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestEnquiryAPIEdgeCases:
    
    def test_valid_post_request(self, authenticated_client):
        # Valid POST request with current model fields
        payload = {
            "id": "ENQ-API-001",
            "customer": "John Doe",
            "vehicle": "Yamaha R15",
            "temperature": "Hot",
            "status": "New Lead",
            "date": "2026-05-28",
            "source": "Walk-in"
        }
        res = authenticated_client.post("/api/enquiry/create/", payload, format="json")
        assert res.status_code == 201
        assert res.data["enquiry_id"] == "ENQ-API-001"
        assert res.data["customer"] == "John Doe"

    def test_missing_required_fields(self, authenticated_client):
        # Missing 'id' which is required by create_enquiry view
        payload = {
            "customer": "John Doe",
            "vehicle": "Yamaha R15",
            "temperature": "Hot",
            "status": "New Lead",
            "date": "2026-05-28",
            "source": "Walk-in"
        }
        res = authenticated_client.post("/api/enquiry/create/", payload, format="json")
        assert res.status_code == 400
        assert "id" in res.data

    def test_get_when_no_data_exists(self, authenticated_client):
        # Verify empty state
        res = authenticated_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 0

    def test_get_after_multiple_inserts(self, authenticated_client):
        # Verify retrieving list
        Enquiry.objects.create(
            enquiry_id="T1",
            customer="John Doe",
            vehicle="R15",
            temperature="Hot",
            status="New Lead",
            date="2026-05-28",
            source="Walk-in"
        )
        Enquiry.objects.create(
            enquiry_id="T2",
            customer="Jane Doe",
            vehicle="FZ",
            temperature="Warm",
            status="Closed",
            date="2026-05-28",
            source="Online"
        )
        res = authenticated_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 2
