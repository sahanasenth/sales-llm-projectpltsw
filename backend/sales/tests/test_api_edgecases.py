import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from sales.models import Enquiry

@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_user(username="testuser", password="password")
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.mark.django_db
class TestEnquiryAPIEdgeCases:
    
    def test_valid_post_request(self, auth_client):
        # QA TestCase 1: Valid POST using frontend key 'id' mapped to 'enquiry_id'
        payload = {
            "id": "ENQ-API-001",
            "customer": "Rithwik",
            "vehicle": "R15",
            "temperature": "Hot",
            "status": "Submitted",
            "date": "2026-05-23",
            "source": "Walk-in"
        }
        res = auth_client.post("/api/enquiry/create/", payload, format="json")
        assert res.status_code == 201
        assert res.data["enquiry_id"] == "ENQ-API-001"
        assert res.data["customer"] == "Rithwik"

    def test_missing_required_fields(self, auth_client):
        # QA TestCase 2: Missing 'customer' field which is required
        payload = {
            "id": "ENQ-API-002",
            "vehicle": "Yamaha",
            "temperature": "Hot",
            "status": "Submitted",
            "date": "2026-05-23",
            "source": "Walk-in"
        }
        res = auth_client.post("/api/enquiry/create/", payload, format="json")
        assert res.status_code == 400
        assert "customer" in res.data # Should flag field as required

    def test_empty_request_body(self, auth_client):
        # QA TestCase 4: Robustness against empty input
        res = auth_client.post("/api/enquiry/create/", {}, format="json")
        assert res.status_code == 400

    def test_get_when_no_data_exists(self, auth_client):
        # QA TestCase 6: Empty state arrays
        res = auth_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 0

    def test_get_after_multiple_inserts(self, auth_client):
        # QA TestCase 7: Verification of returned list
        Enquiry.objects.create(
            enquiry_id="T1", customer="C1", vehicle="V1", 
            temperature="Hot", status="Submitted", date="2026-05-23", source="Walk-in"
        )
        Enquiry.objects.create(
            enquiry_id="T2", customer="C2", vehicle="V2", 
            temperature="Warm", status="Submitted", date="2026-05-23", source="Phone"
        )
        res = auth_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 2

    def test_unauthenticated_request_fails(self):
        # Verify that accessing protected endpoints without a token returns 401 Unauthorized
        client = APIClient()
        res = client.get("/api/enquiry/")
        assert res.status_code == 401
