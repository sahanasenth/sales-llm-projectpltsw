from rest_framework import serializers
from .models import Enquiry, Appointment, Feedback


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'

    def to_internal_value(self, data):
        data = dict(data)
        if 'id' in data and 'enquiry_id' not in data:
            val = data.pop('id')
            data['enquiry_id'] = val[0] if isinstance(val, list) else val
        return super().to_internal_value(data)

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

    def to_internal_value(self, data):
        data = dict(data)
        if 'id' in data and 'appointment_id' not in data:
            val = data.pop('id')
            data['appointment_id'] = val[0] if isinstance(val, list) else val
        return super().to_internal_value(data)

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'

    def to_internal_value(self, data):
        data = dict(data)
        if 'id' in data and 'feedback_id' not in data:
            val = data.pop('id')
            data['feedback_id'] = val[0] if isinstance(val, list) else val
        if 'enquiryId' in data and 'enquiry_id' not in data:
            val = data.pop('enquiryId')
            data['enquiry_id'] = val[0] if isinstance(val, list) else val
        return super().to_internal_value(data)
