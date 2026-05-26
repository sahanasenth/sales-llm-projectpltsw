import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(username, role, password="Password123"):
        return get_user_model().objects.create_user(
            username=username,
            password=password,
            role=role,
        )

    return _make_user


@pytest.fixture
def auth_client(api_client, make_user):
    def _auth_client(role, username=None):
        user = make_user(username or role, role)
        api_client.force_authenticate(user=user)
        return api_client

    return _auth_client
