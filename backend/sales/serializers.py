from rest_framework import serializers
from .models import Enquiry, Appointment, Feedback


class EnquirySerializer(serializers.ModelSerializer):

    class Meta:
        model = Enquiry
        fields = '__all__'

    def validate_temperature(self, value):

        allowed = ['Hot', 'Warm', 'Cold']

        if value not in allowed:
            raise serializers.ValidationError(
                "Temperature must be Hot, Warm, or Cold."
            )

        return value

    def validate_status(self, value):

        allowed = ['Submitted', 'Draft', 'Closed']

        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid enquiry status."
            )

        return value


class AppointmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appointment
        fields = '__all__'

    def validate_status(self, value):

        allowed = [
            'Scheduled',
            'Pending',
            'Completed'
        ]

        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid appointment status."
            )

        return value


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = '__all__'

    def validate_status(self, value):

        allowed = [
            'Submitted',
            'Draft',
            'Closed'
        ]

        if value not in allowed:
            raise serializers.ValidationError(
                "Invalid feedback status."
            )

        return value
