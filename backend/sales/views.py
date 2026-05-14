from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Enquiry, Appointment, Feedback
from .serializers import EnquirySerializer, AppointmentSerializer, FeedbackSerializer


def home(request):
    return JsonResponse({
        "message": "Sales CRM backend is running"
    })


@api_view(['GET'])
def get_enquiries(request):
    enquiries = Enquiry.objects.all().order_by('-id')
    serializer = EnquirySerializer(enquiries, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_enquiry(request):
    data = request.data.copy()

    incoming_id = data.get('id')
    if not incoming_id:
        return Response({"id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

    data['enquiry_id'] = incoming_id

    serializer = EnquirySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_appointments(request):
    appointments = Appointment.objects.all().order_by('-id')
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_appointment(request):
    data = request.data.copy()

    incoming_id = data.get('id')
    if not incoming_id:
        return Response({"id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

    data['appointment_id'] = incoming_id

    serializer = AppointmentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_feedback(request):
    feedback_records = Feedback.objects.all().order_by('-id')
    serializer = FeedbackSerializer(feedback_records, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_feedback(request):
    data = request.data.copy()

    incoming_id = data.get('id')
    if not incoming_id:
        return Response({"id": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

    data['feedback_id'] = incoming_id

    serializer = FeedbackSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from .services import process_chat_query

@api_view(['POST'])
def chat_api(request):
    query = request.data.get('query')
    if not query:
        return Response({
            "status": "error",
            "message": "Missing 'query' in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = process_chat_query(query)
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({
            "status": "error",
            "message": f"Internal Server Error: {str(exc)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
