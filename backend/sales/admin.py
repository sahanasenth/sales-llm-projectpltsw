from django.contrib import admin
from .models import Enquiry, Appointment, Feedback

admin.site.register(Enquiry)
admin.site.register(Appointment)
admin.site.register(Feedback)