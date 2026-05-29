from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Enquiry, Appointment, Feedback, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


class CustomUserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_role', 'is_staff')

    def get_role(self, obj):
        return getattr(getattr(obj, 'profile', None), 'role', '')
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Enquiry)
admin.site.register(Appointment)
admin.site.register(Feedback)
