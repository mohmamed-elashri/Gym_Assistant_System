"""Settings used only by the test run (pytest-django).

Production defaults are secure (DEBUG off, key required), so the tests supply
their own throwaway key and plain-HTTP mode before loading the real settings.
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-" + "x" * 50)
os.environ.setdefault("DJANGO_HTTPS", "false")

from .settings import *  # noqa: E402,F401,F403
