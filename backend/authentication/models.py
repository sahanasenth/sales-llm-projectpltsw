# No custom models needed for this project.
# Django's built-in User model is sufficient.
#
# Django's AbstractUser already provides:
#   - username, email, first_name, last_name
#   - password (stored as a HASHED string — never plain text)
#   - is_active, is_staff, is_superuser
#   - date_joined, last_login
#
# If you need custom fields (e.g., phone, avatar), create a
# custom model that extends AbstractUser:
#
#   from django.contrib.auth.models import AbstractUser
#   class CustomUser(AbstractUser):
#       phone = models.CharField(max_length=15, blank=True)
#
#   Then in settings.py add:
#     AUTH_USER_MODEL = 'authentication.CustomUser'
