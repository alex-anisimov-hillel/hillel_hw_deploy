import pytest
from django.core.cache import cache
from django.db import connection


def test_liveness_needs_no_database(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_liveness_is_not_cached(client):
    assert "no-cache" in client.get("/health/")["Cache-Control"]


def test_health_rejects_unsafe_methods(client):
    assert client.post("/health/").status_code == 405
    assert client.post("/health/ready/").status_code == 405


@pytest.mark.django_db
def test_readiness_ok(client):
    response = client.get("/health/ready/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "cache": "ok"},
    }


@pytest.mark.django_db
def test_readiness_503_when_database_down(client, monkeypatch):
    def broken_cursor(*args, **kwargs):
        raise RuntimeError("db is down")

    monkeypatch.setattr(connection, "cursor", broken_cursor)

    response = client.get("/health/ready/")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["checks"] == {"database": "error", "cache": "ok"}


@pytest.mark.django_db
def test_readiness_503_when_cache_down(client, monkeypatch):
    def broken_set(*args, **kwargs):
        raise RuntimeError("redis is down")

    monkeypatch.setattr(cache, "set", broken_set)

    response = client.get("/health/ready/")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "ok", "cache": "error"}
