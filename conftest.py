"""Test-only environment. Production defaults are secure (DEBUG off), so the
test run supplies its own throwaway key and plain-HTTP mode explicitly."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-" + "x" * 50)
os.environ.setdefault("DJANGO_HTTPS", "false")
