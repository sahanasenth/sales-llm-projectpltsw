from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from .models import Enquiry, Appointment, Feedback
from .serializers import EnquirySerializer, AppointmentSerializer, FeedbackSerializer, MyTokenObtainPairSerializer
from .permissions import IsDirector, IsSalesManager, IsAdmin

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

def home(request):
    return JsonResponse({
        "message": "Sales CRM backend is running"
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    profile = getattr(request.user, 'profile', None)
    role = 'admin' if request.user.is_superuser else getattr(profile, 'role', None)
    if not role:
        return Response(
            {"detail": "User profile is missing role information."},
            status=status.HTTP_403_FORBIDDEN
        )
    return Response({
        "username": request.user.username,
        "role": role,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_enquiries(request):
    enquiries = Enquiry.objects.all().order_by('-id')
    serializer = EnquirySerializer(enquiries, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def get_appointments(request):
    appointments = Appointment.objects.all().order_by('-id')
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def get_feedback(request):
    feedback_records = Feedback.objects.all().order_by('-id')
    serializer = FeedbackSerializer(feedback_records, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_feedback(request):
    data = request.data.copy()

    incoming_id = data.get('id')
    if not incoming_id:
        return Response(
            {"id": ["This field is required."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    data['feedback_id'] = incoming_id

    serializer = FeedbackSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirector])
def get_revenue_report(request):
    # Derived metrics from existing models (no fabricated monetary values)
    total_enquiries = Enquiry.objects.count()
    total_appointments = Appointment.objects.count()
    total_feedback = Feedback.objects.count()

    conversion_rate = 0
    if total_enquiries > 0:
        conversion_rate = round((total_appointments / total_enquiries) * 100, 2)

    # Breakdown by lead temperature and source
    temp_breakdown = list(
        Enquiry.objects.values('temperature').annotate(count=Count('id')).order_by('-count')
    )
    source_breakdown = list(
        Enquiry.objects.values('source').annotate(count=Count('id')).order_by('-count')
    )

    report = {
        'total_enquiries': total_enquiries,
        'total_appointments': total_appointments,
        'total_feedback': total_feedback,
        'conversion_rate_percent': conversion_rate,
        'temperature_breakdown': temp_breakdown,
        'source_breakdown': source_breakdown,
    }
    return Response(report)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_audit_logs(request):
    # Return recent admin LogEntry records from Django admin
    entries = LogEntry.objects.select_related('user').order_by('-action_time')[:100]
    logs = []
    for e in entries:
        logs.append({
            'timestamp': e.action_time.strftime('%Y-%m-%d %H:%M:%S'),
            'user': e.user.username if e.user else None,
            'action_flag': e.get_action_flag_display() if hasattr(e, 'get_action_flag_display') else e.action_flag,
            'object': e.object_repr,
            'change_message': e.change_message,
        })
    return Response(logs)


from .services import process_chat_query, get_chatbot_instance

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDirector])
def chat_api(request):
    query = request.data.get('query')
    if not query:
        return Response({
            "error": "Missing 'query' in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        response_data = process_chat_query(query)
        # Return format expected by Platinum_Sales_Chatbot index.html
        return Response({
            "answer": response_data["response"],
            "intent": response_data["metadata"]["intent"],
            "elapsed": response_data["metadata"]["latency_seconds"]
        }, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({
            "error": f"Internal Server Error: {str(exc)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_api(request):
    """Returns the health status of the chatbot."""
    try:
        instance = get_chatbot_instance()
        import test as chatbot_test_module
        llm_ready = getattr(chatbot_test_module, "_llm_ready", False)
        return Response({
            "status": "ok",
            "chatbot_ready": instance is not None,
            "llm_ready": llm_ready
        }, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({
            "status": "error",
            "chatbot_ready": False,
            "message": str(exc)
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggestions_api(request):
    """Returns pre-defined query suggestions."""
    suggestions = [
        "Show all enquiries",
        "Who gave bad feedback?",
        "All cancelled appointments",
        "Show ENQ001 full details",
        "Returning customers",
        "Customers from Chennai",
        "Who hasn't taken a test ride?",
        "Show me new leads",
        "What's Divya's feedback?",
        "Is Arjun's appointment confirmed?",
        "What car did Sneha enquire about?",
        "Show good feedback customers",
        "All completed appointments",
        "Payment type breakdown",
    ]
    return Response({"suggestions": suggestions}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDirector])
def reset_chat_api(request):
    """Resets the chatbot conversation history."""
    try:
        instance = get_chatbot_instance()
        if instance and hasattr(instance, 'history'):
            instance.history.clear()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
