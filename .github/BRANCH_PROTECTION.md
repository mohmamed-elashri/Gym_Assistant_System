# Protecting the `main` Branch (Guide)

To protect the `main` branch on GitHub (recommended):

1. Go to your repository: https://github.com/mohmamed-elashri/Gym_Assistant_System
2. Click `Settings` → `Branches` → `Add rule`.
3. Set the **Branch name pattern** to `main`.
4. Recommended options to enable:
   - Require pull request reviews before merging (set required number of reviews as desired)
   - Require status checks to pass before merging (select the CI checks from Actions)
   - Require branches to be up to date before merging
   - Include administrators (optional—but recommended for enforced protection)
   - Require signed commits (optional)
5. Save changes.

Alternatively, use GitHub API or `gh` to create branch protection rules. Example using `gh` (requires repo admin permissions):

```bash
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/mohmamed-elashri/Gym_Assistant_System/branches/main/protection \
  -f required_status_checks.contexts='["python-tests"]' \
  -f enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true
```

Replace `python-tests` with the name of your workflow status check (see Actions tab).
