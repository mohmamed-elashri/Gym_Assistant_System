# Key Rotation & Secrets Management

This document explains how to safely rotate API keys and add secrets to GitHub for this project.

## Overview
- We detected sensitive keys in the local `.env` file. Those keys have been archived locally under `C:\Users\mr501\env_backups\`.
- Do **not** store secrets in the repository. Use GitHub Secrets for CI and environment variables for local development.

## High-level steps to rotate keys
1. Identify the provider for each key (OpenRouter, Google/Gemini, others shown in `.env`).
2. Log in to the provider dashboard and revoke the compromised key(s).
3. Create a new key and limit its scope and IP/hostname restrictions if available.
4. Add the new key to GitHub Secrets (see below) and to your local `.env` only when necessary.
5. Test the service with the new key.
6. Remove old keys from any config, CI, or developer machines.

## Provider-specific links
- OpenRouter: https://openrouter.ai/keys
- Google Cloud / API keys: https://console.cloud.google.com/apis/credentials
- Gemini / Google generative AI: https://console.cloud.google.com/apis/credentials (same place)

## Add secrets to GitHub (recommended)
1. Go to your repository on GitHub: `https://github.com/mohmamed-elashri/Gym_Assistant_System`
2. Settings → Secrets and variables → Actions → New repository secret
3. Add a secret with the name used by the code, e.g. `GEMINI_KEY_1`, `OPENROUTER_KEY_1`, `DJANGO_SECRET_KEY`.
4. Update your CI workflow to read the secret via `secrets.NAME`.

### Using GitHub CLI (`gh`)
If you have `gh` installed and authenticated with an account that has repo admin access, you can add secrets from your machine:

```bash
# Login once: gh auth login
# Add a secret
gh secret set GEMINI_KEY_1 --body "<new-key-value>" --repo mohmamed-elashri/Gym_Assistant_System
```

For multiple secrets, use a small script (example below).

## Example PowerShell helper (local)
Save as `scripts/add_github_secrets.ps1` and run after installing and authenticating `gh`.

```powershell
param(
  [string]$repo = 'mohmamed-elashri/Gym_Assistant_System'
)

$secrets = @{
  'DJANGO_SECRET_KEY' = (Read-Host 'DJANGO_SECRET_KEY (enter value)' -AsSecureString);
  'GEMINI_KEY_1' = (Read-Host 'GEMINI_KEY_1 (enter value)' -AsSecureString);
  'OPENROUTER_KEY_1' = (Read-Host 'OPENROUTER_KEY_1 (enter value)' -AsSecureString);
}

foreach ($name in $secrets.Keys) {
  $val = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secrets[$name]))
  gh secret set $name --body $val --repo $repo
}
```

## Protecting the `main` branch (recommended)
- Go to Settings → Branches → Add rule
- Branch name pattern: `main`
- Check: Require pull request reviews before merging, Require status checks to pass, Include admins (optional)

## Post-rotation checklist
- Confirm CI tests pass using the new keys.
- Remove any keys left in local machines and instruct teammates to rotate their local `.env` copies.
- Monitor usage in provider dashboards for unusual activity.

---
If you want, I can:
- Create `scripts/add_github_secrets.ps1` in the repo now.
- Attempt to add secrets via `gh` if you authenticate locally (I will prompt you to run `gh auth login`).
- Enable Branch Protection rules (I will provide exact UI steps or use the GitHub API if you provide a PAT).

Tell me which of these you'd like next.