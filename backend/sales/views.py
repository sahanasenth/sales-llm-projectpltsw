from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from authentication.permissions import HasRolePermission

from .models import Enquiry, Appointment, Feedback
from .services import process_chat_query
from .serializers import (
    EnquirySerializer,
    AppointmentSerializer,
    FeedbackSerializer
)



# ─────────────────────────────────────────────
# Home API
# ─────────────────────────────────────────────
def home(request):
    return JsonResponse({
        "message": "Sales CRM backend is running"
    })


# ─────────────────────────────────────────────
# Enquiry APIs
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any(
        'view_all_sales',
        'view_team_sales',
        'view_assigned_sales',
    ),
])
def get_enquiries(request):
    enquiries = Enquiry.objects.all().order_by('-id')
    serializer = EnquirySerializer(enquiries, many=True)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any('manage_enquiries', 'create_enquiry'),
])
def create_enquiry(request):

    serializer = EnquirySerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ─────────────────────────────────────────────
# Appointment APIs
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any(
        'view_all_sales',
        'view_team_sales',
        'view_assigned_sales',
    ),
])
def get_appointments(request):
    appointments = Appointment.objects.all().order_by('-id')
    serializer = AppointmentSerializer(appointments, many=True)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any('manage_appointments'),
])
def create_appointment(request):

    serializer = AppointmentSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ─────────────────────────────────────────────
# Feedback APIs
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any('manage_feedback', 'add_feedback'),
])
def get_feedback(request):
    feedback_records = Feedback.objects.all().order_by('-id')
    serializer = FeedbackSerializer(feedback_records, many=True)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any('manage_feedback', 'add_feedback'),
])
def create_feedback(request):

    serializer = FeedbackSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ─────────────────────────────────────────────
# Chat API
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([
    IsAuthenticated,
    HasRolePermission.require_any('view_reports'),
])
def chat_api(request):

    query = request.data.get('query')

    if not query:
        return Response(
            {
                "status": "error",
                "message": "Missing 'query' in request body."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        response_data = process_chat_query(query)

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )

    except Exception as exc:

        return Response(
            {
                "status": "error",
                "message": f"Internal Server Error: {str(exc)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
