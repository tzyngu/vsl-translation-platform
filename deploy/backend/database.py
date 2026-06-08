import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))
load_dotenv(ROOT / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vsl_frontend.settings")


def setup_django() -> None:
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def database_health() -> dict:
    setup_django()
    from django.conf import settings
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "ok", "database": settings.DATABASES["default"]["NAME"], "engine": "postgresql"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc), "engine": "postgresql"}


setup_django()
