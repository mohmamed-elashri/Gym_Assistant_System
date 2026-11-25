# Free demo deployment on Render

This deploys the app as a Render free web service from the Dockerfile. It is a demo, not production.

## What to expect

- Cost: free instance, no payment method needed. Do not add a card, so nothing can be billed.
- The service sleeps after 15 minutes without traffic and takes about a minute to wake up.
- The filesystem is wiped on every restart, so the SQLite database (user accounts) resets. The free Render Postgres database expires after 30 days, so this blueprint does not use it.
- Models are the synthetic demonstration models trained at build time (see MODEL_PROVENANCE.md).
- The AI chat needs a Gemini or OpenRouter key. None is set, so chat answers fall back to the built-in responses. Never put keys in the repository.
- Sign-up is open to anyone with the URL. Requests are throttled (30/min anonymous, 120/min signed in). `/api/docs/` is public.

Sources: https://render.com/docs/free

## Steps

1. Sign in at https://render.com (the GitHub login is fine).
2. New > Blueprint, connect the GitHub repository `Gym_Assistant_System`, and pick the `render.yaml` in the default branch.
3. Render shows one web service, `gym-assistant-demo`, on the Free plan, and creates `DJANGO_SECRET_KEY` automatically. Nothing to type or paste.
4. Click Apply. The first build takes a few minutes (it installs dependencies and trains the models).
5. When it is live, open `https://<service-name>.onrender.com/landing/`. If Render gives the service a different hostname pattern, the `onrender.com` wildcard in `render.yaml` still covers it.
6. Check `https://<service-name>.onrender.com/api/health/live/` returns success, create an account and try the predictor.
7. Send the URL to whoever maintains the README so the live link is added.

To remove it: Render dashboard > the service > Settings > Delete Web Service.

## Not verified

This blueprint has not been run on Render yet. In particular, memory use of one gunicorn worker on the 512 MB free instance and the first-build time are untested.
