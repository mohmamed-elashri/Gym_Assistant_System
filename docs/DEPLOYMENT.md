# Deployment readiness

Status: **not deployed anywhere.** This page records what is in place, what was
checked, and what is still missing before a real deployment. Nothing here claims
a production deployment, load test or uptime.

## What is in the repository

| Item | State | Evidence |
| --- | --- | --- |
| Container image | `Dockerfile`: Python 3.12 slim, non-root user, gunicorn (2 workers) | built in the CI `docker` job |
| Local stack | `docker-compose.yml`: web + PostgreSQL 16, healthchecks, required `POSTGRES_PASSWORD` | CI `docker` job |
| Secure defaults | `DJANGO_DEBUG` defaults to off; app refuses to start without `DJANGO_SECRET_KEY` | PR #11 |
| HTTPS hardening | secure cookies, SSL redirect, optional HSTS, proxy header (`DJANGO_HTTPS`, `DJANGO_HSTS_SECONDS`, `DJANGO_BEHIND_PROXY`) | PR #10 |
| Authentication | session auth + CSRF on all API endpoints | PR #12 |
| Logging | JSON lines on stdout, `LOG_LEVEL` | PR #13 |
| Health probes | `/api/health/live/` (process) and `/api/health/ready/` (database) | `fitness_api/health.py` |
| CI | lint, tests (3.11, 3.12), mypy, coverage, Bandit, pip-audit, docker | `.github/workflows/ci.yml` |

## Required environment

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | required, unique per environment |
| `DJANGO_ALLOWED_HOSTS` | comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain` origins |
| `POSTGRES_*` | database settings (see `docker-compose.yml`) |
| `GEMINI_KEY_*` / `OPENROUTER_KEY_*` | at least one, for the chat and plan features |
| `DJANGO_HTTPS`, `DJANGO_HSTS_SECONDS` | keep HTTPS on in production; raise HSTS only once HTTPS works everywhere |

Do not commit `.env`. Rotate keys as described in `docs/KEY_ROTATION.md`.

## Known gaps before a real deployment

1. **Static files.** Gunicorn does not serve static files and no static-file
   middleware (for example WhiteNoise) or CDN is configured, so with
   `DEBUG` off the admin and any local static assets need a reverse proxy or
   `collectstatic` plus a file server. Not implemented.
2. **ML models.** The shipped models are synthetic demonstrations
   (`docs/MODEL_PROVENANCE.md`). They are not suitable for real fitness or
   health guidance.
3. **Migrations at start.** Compose runs `migrate` on every start. For more than
   one replica, run migrations as a separate release step.
4. **No TLS termination, domain, backups, monitoring or alerting** are set up.
5. **Rate limits** are Django REST framework throttles per process (default
   30/min anonymous, 120/min users); they are not shared across workers.
6. **OpenAPI schema is thin.** The three API views have no serializers, so drf-spectacular warns that it cannot describe their request/response bodies and the Swagger page shows no schemas.
7. **Dependency updates:** five Dependabot PRs are open and unreviewed.

## Pre-deploy checklist

- [ ] Unique `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` set
- [ ] TLS terminated at a proxy that sets `X-Forwarded-Proto`
- [ ] `python manage.py check --deploy` reviewed (with a real key and HTTPS on, the only security warning I saw was `SECURE_HSTS_SECONDS`, which is opt-in)
- [ ] Static files served (gap 1)
- [ ] `GET /api/health/ready/` returns 200 against the real database
- [ ] Database backups and a restore test
- [ ] Logs collected from stdout
- [ ] CI green on the commit being deployed
