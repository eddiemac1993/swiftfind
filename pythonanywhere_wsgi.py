import os
import sys
from pathlib import Path

project_home = Path("/home/YOUR_PYTHONANYWHERE_USERNAME/SchoolProcure")
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolprocure.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
