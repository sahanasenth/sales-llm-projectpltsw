# =============================================================
#  core/wsgi.py
#  WSGI (Web Server Gateway Interface) entry point.
#  Used by production servers like Gunicorn to serve the app.
#  Command: gunicorn core.wsgi:application
# =============================================================

import os
from django.core.wsgi import get_wsgi_application

# Tell Django which settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
