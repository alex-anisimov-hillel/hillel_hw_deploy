"""Health-check endpoints for Docker / load balancers / uptime monitors.

* ``/health/``       - liveness: the process is up and serving requests.
                       Touches no external service, so it never flaps because
                       of a database or Redis hiccup.
* ``/health/ready/`` - readiness: PostgreSQL and the Redis cache answer.
                       Returns 503 (with the failing component) otherwise.
"""

import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


def _check_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def _check_cache():
    cache.set("healthcheck", "ok", timeout=5)
    if cache.get("healthcheck") != "ok":
        raise RuntimeError("cache round-trip failed")


@require_safe
@never_cache
def liveness(request):
    """The app is running."""
    return JsonResponse({"status": "ok"})


@require_safe
@never_cache
def readiness(request):
    """The app can reach its dependencies (database and cache)."""
    checks = {}
    for name, check in (("database", _check_database), ("cache", _check_cache)):
        try:
            check()
        except Exception:  # any failure means "not ready"
            logger.exception("Health check failed: %s", name)
            checks[name] = "error"
        else:
            checks[name] = "ok"

    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "error", "checks": checks},
        status=200 if healthy else 503,
    )
