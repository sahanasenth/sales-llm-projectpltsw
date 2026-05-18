from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Configuration class for the authentication application.

    - default_auto_field: Use BigAutoField (64-bit int) as the default
      primary key type for all models in this app.
    - name: Must match the app directory name and the entry in INSTALLED_APPS.
    - verbose_name: Human-readable name shown in the Django Admin panel.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Authentication & Authorization'
