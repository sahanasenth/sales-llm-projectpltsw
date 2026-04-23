import pytest
from rest_framework.test import APIClient
from sales.models import Enquiry

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestEnquiryAPIEdgeCases:
    
    def test_valid_post_request(self, api_client):
        # QA TestCase 1: Valid POST
        payload = {
            "name": "ENQ-API-001",
            "phone_no": "9999999999",
            "vehicle_name": "R15"
        }
        res = api_client.post("/api/enquiry/", payload, format="json")
        assert res.status_code == 201
        assert res.data["name"] == "ENQ-API-001"

    def test_missing_required_fields(self, api_client):
        # QA TestCase 2: Missing 'name' which is the primary key
        payload = {
            "phone_no": "9999999999",
            "vehicle_name": "Yamaha"
        }
        res = api_client.post("/api/enquiry/", payload, format="json")
        assert res.status_code == 400
        assert "name" in res.data # Should flag field as required

    def test_invalid_field_format(self, api_client):
        # QA TestCase 3: Data too long for constraint (phone limit is 10)
        payload = {
            "name": "ENQ-API-002",
            "phone_no": "12345678901234567890" # 20 chars
        }
        res = api_client.post("/api/enquiry/", payload, format="json")
        assert res.status_code == 400

    def test_empty_request_body(self, api_client):
        # QA TestCase 4: Robustness against empty input
        res = api_client.post("/api/enquiry/", {}, format="json")
        assert res.status_code == 400

    def test_wrong_data_types(self, api_client):
        # QA TestCase 5: Sending strings to DecimalField
        payload = {
            "name": "ENQ-API-003",
            "down_payment": "Not a Number"
        }
        res = api_client.post("/api/enquiry/", payload, format="json")
        assert res.status_code == 400
        assert "down_payment" in res.data

    def test_get_when_no_data_exists(self, api_client):
        # QA TestCase 6: Empty state arrays
        res = api_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 0

    def test_get_after_multiple_inserts(self, api_client):
        # QA TestCase 7: Verification of returned list
        Enquiry.objects.create(name="T1")
        Enquiry.objects.create(name="T2")
        res = api_client.get("/api/enquiry/")
        assert res.status_code == 200
        assert len(res.data) == 2
