# =============================================================
#  core/asgi.py
#  ASGI (Async Server Gateway Interface) entry point.
#  Used by async-capable servers like Uvicorn / Daphne.
#  Command: uvicorn core.asgi:application --reload
# =============================================================

import os
from django.core.asgi import get_asgi_application

# Tell Django which settings module to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()
