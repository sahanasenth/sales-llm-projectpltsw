# from rest_framework import viewsets
# from .models import Enquiry, Customer, Appointment, Feedback
# from .serializers import EnquirySerializer, CustomerSerializer, AppointmentSerializer, FeedbackSerializer

# class EnquiryViewSet(viewsets.ModelViewSet):
#     queryset = Enquiry.objects.all()
#     serializer_class = EnquirySerializer

# class CustomerViewSet(viewsets.ModelViewSet):
#     queryset = Customer.objects.all()
#     serializer_class = CustomerSerializer

# class AppointmentViewSet(viewsets.ModelViewSet):
#     queryset = Appointment.objects.all()
#     serializer_class = AppointmentSerializer

# class FeedbackViewSet(viewsets.ModelViewSet):
#     queryset = Feedback.objects.all()
#     serializer_class = FeedbackSerializer

# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Enquiry
# from .serializers import EnquirySerializer


# # GET all enquiries
# @api_view(['GET'])
# def get_enquiries(request):
#     enquiries = Enquiry.objects.all().order_by('-id')
#     serializer = EnquirySerializer(enquiries, many=True)
#     return Response(serializer.data)


# # POST new enquiry
# @api_view(['POST'])
# def create_enquiry(request):
#     data = request.data.copy()

#     # Map frontend "id" → backend "enquiry_id"
#     data['enquiry_id'] = data.get('id')

#     serializer = EnquirySerializer(data=data)

#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Enquiry
from .serializers import EnquirySerializer


def home(request):
    return JsonResponse({
        "message": "Sales CRM backend is running",
        "endpoints": {
            "get_enquiries": "/api/enquiry/",
            "create_enquiry": "/api/enquiry/create/"
        }
    })


@api_view(['GET'])
def get_enquiries(request):
    enquiries = Enquiry.objects.all().order_by('-id')
    serializer = EnquirySerializer(enquiries, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_enquiry(request):
    data = request.data.copy()
    data['enquiry_id'] = data.get('id')

    serializer = EnquirySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)