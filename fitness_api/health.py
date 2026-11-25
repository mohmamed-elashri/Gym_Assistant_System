"""Liveness and readiness probes."""

from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:  # noqa: BLE001 - report any database failure as not ready
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
