from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        DIRECTOR = 'director', 'Director'
        MANAGER = 'manager', 'Manager'
        SALES_EXECUTIVE = 'sales_executive', 'Sales Executive'

    ROLE_PERMISSIONS = {
        Role.DIRECTOR.value: [
            'manage_users',
            'assign_roles', 
            'view_all_sales',
            'manage_enquiries',
            'manage_appointments',
            'manage_feedback',
            'view_reports',
        ],
        Role.MANAGER.value: [
            'view_team_sales',
            'manage_enquiries',
            'manage_appointments',
            'manage_feedback',
            'view_reports',
        ],
        Role.SALES_EXECUTIVE.value: [
            'view_assigned_sales',
            'create_enquiry',
            'update_enquiry',
            'manage_appointments',
            'add_feedback',
        ],
    }

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SALES_EXECUTIVE,
    )

    @property
    def role_code(self):
        return self.role.value if hasattr(self.role, 'value') else self.role

    @property
    def role_label(self):
        return self.get_role_display()

    @property
    def permissions(self):
        return self.ROLE_PERMISSIONS.get(self.role_code, [])

    def has_role_permission(self, permission):
        return permission in self.permissions
