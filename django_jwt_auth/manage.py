#!/usr/bin/env python
# =============================================================
#  manage.py
#  Django's command-line utility for administrative tasks.
#
#  Common commands:
#    python manage.py runserver         → Start dev server
#    python manage.py makemigrations    → Create migration files
#    python manage.py migrate           → Apply migrations to DB
#    python manage.py createsuperuser   → Create admin user
#    python manage.py shell             → Open Django shell
# =============================================================

import os
import sys


def main():
    """Run administrative tasks."""

    # Point Django to our settings module inside the 'core' package
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
