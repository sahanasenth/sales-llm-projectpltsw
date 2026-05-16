# =============================================================
#  authentication/admin.py
#
#  Registers models with the Django Admin panel.
#  Access the admin at: http://127.0.0.1:8000/admin/
#  (Create a superuser first: python manage.py createsuperuser)
#
#  We use Django's default UserAdmin which provides:
#    - List view of all users
#    - Search & filter by username, email, is_staff, is_active
#    - In-line password change (uses hashing, never plain text)
#    - Group and permission management
# =============================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# The default User model is already registered by Django's auth app.
# We unregister and re-register it to customize the display if needed.

# Unregister the default registration
admin.site.unregister(User)


# ── Custom UserAdmin ──────────────────────────────────────────
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Customized User admin display.

    list_display: Columns shown in the user list view
    list_filter:  Filter panel on the right side
    search_fields: Fields searched when using the search bar
    ordering:    Default sort order
    """

    # Columns shown in the user list table
    list_display = [
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'date_joined',
    ]

    # Filters shown in the right sidebar
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']

    # Fields searched by the search bar
    search_fields = ['username', 'email', 'first_name', 'last_name']

    # Default sort: newest users first
    ordering = ['-date_joined']

    # Make ID visible but read-only
    readonly_fields = ['date_joined', 'last_login']
