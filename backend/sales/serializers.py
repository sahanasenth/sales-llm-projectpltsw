from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Enquiry, Appointment, Feedback, Profile
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


def _role_from_user(user):
    if user.is_superuser:
        return "admin"
    try:
        return user.profile.role
    except Profile.DoesNotExist as exc:
        raise serializers.ValidationError("User profile is missing role information.") from exc

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        role = _role_from_user(user)
        token['role'] = role
        token['username'] = user.username
        return token


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = RefreshToken(attrs['refresh'])
        user_id = refresh.get('user_id') or refresh.get('user')
        if not user_id:
            raise serializers.ValidationError("Refresh token is missing the user identifier.")

        User = get_user_model()
        try:
            user = User.objects.select_related('profile').get(pk=user_id)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Refresh token user no longer exists.") from exc

        access = refresh.access_token
        access['role'] = _role_from_user(user)
        access['username'] = user.username
        data['access'] = str(access)
        return data

class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
