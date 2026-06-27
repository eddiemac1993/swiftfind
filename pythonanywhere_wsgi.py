import os
import sys
from pathlib import Path

project_home = Path.home() / "SchoolProcure"
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault(
    "DJANGO_ALLOWED_HOSTS",
    f"{Path.home().name}.pythonanywhere.com,{Path.home().name}.eu.pythonanywhere.com,localhost,127.0.0.1",
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolprocure.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
