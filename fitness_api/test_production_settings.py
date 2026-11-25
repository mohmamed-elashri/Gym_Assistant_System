"""Production settings must be hardened when DEBUG is off and HTTPS is on."""

import importlib
import os
import sys

import pytest


def _load(monkeypatch, **env):
    for key in (
        "DJANGO_DEBUG",
        "DJANGO_HTTPS",
        "DJANGO_SECRET_KEY",
        "DJANGO_HSTS_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("gym_config.settings", None)
    return importlib.import_module("gym_config.settings")


@pytest.fixture(autouse=True)
def _restore_settings():
    yield
    os.environ.pop("DJANGO_DEBUG", None)
    os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-" + "x" * 50)
    os.environ.setdefault("DJANGO_HTTPS", "false")
    sys.modules.pop("gym_config.settings", None)
    importlib.import_module("gym_config.settings")


def test_https_hardening_on_in_production(monkeypatch):
    s = _load(monkeypatch, DJANGO_DEBUG="false", DJANGO_SECRET_KEY="x" * 50)
    assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE
    assert s.SECURE_SSL_REDIRECT is True
    assert s.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_https_hardening_can_be_disabled_for_local_http(monkeypatch):
    s = _load(
        monkeypatch,
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY="x" * 50,
        DJANGO_HTTPS="false",
    )
    assert not getattr(s, "SECURE_SSL_REDIRECT", False)


def test_debug_mode_has_no_forced_https(monkeypatch):
    s = _load(monkeypatch, DJANGO_DEBUG="true")
    assert not getattr(s, "SECURE_SSL_REDIRECT", False)


def test_production_refuses_insecure_default_key(monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured):
        _load(monkeypatch, DJANGO_DEBUG="false")


def test_debug_is_off_by_default(monkeypatch):
    s = _load(monkeypatch, DJANGO_SECRET_KEY="x" * 50)
    assert s.DEBUG is False


def test_fails_closed_without_secret_key_by_default(monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    with pytest.raises(ImproperlyConfigured):
        _load(monkeypatch)
