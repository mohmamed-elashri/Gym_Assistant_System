<#
Helper script to add repository secrets to GitHub using `gh`.
Usage:
  1. Install GitHub CLI: https://cli.github.com/
  2. Run `gh auth login` and authenticate with an account that has admin access to the repo.
  3. Run this script: `.
ecipes\add_github_secrets.ps1` or `pwsh ./scripts/add_github_secrets.ps1`

The script tries to read keys from a local `.env` file in the project root. If a key is present, it prompts for confirmation to add it to GitHub.
#>
param(
    [string]$Repo = 'mohmamed-elashri/Gym_Assistant_System',
    [string]$EnvPath = "..\ .env"
)

# Move to script directory
Set-Location -Path $PSScriptRoot

# Helper: prompt yes/no
function Ask-YesNo($prompt) {
    $r = Read-Host "$prompt (y/n)";
    return $r -eq 'y' -or $r -eq 'Y'
}

# Load .env into a hashtable
$envFile = Join-Path $PSScriptRoot '..' '.env'
$vars = @{}
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z0-9_]+)\s*=\s*(.*)') {
            $k = $matches[1]; $v = $matches[2];
            $vars[$k] = $v.Trim('"')
        }
    }
}

# Common keys to set (update as needed)
$keys = @(
    'DJANGO_SECRET_KEY',
    'GEMINI_KEY_1','GEMINI_KEY_2','GEMINI_KEY_3',
    'OPENROUTER_KEY_1','OPENROUTER_KEY_2',
    'OPENROUTER_KEY_3','OPENROUTER_KEY_4'
)

foreach ($k in $keys) {
    $val = $null
    if ($vars.ContainsKey($k) -and -not [string]::IsNullOrWhiteSpace($vars[$k])) {
        Write-Host "Found $k in local .env"
        if (Ask-YesNo "Add $k to GitHub Secrets with the value from local .env?") {
            $val = $vars[$k]
        }
    } else {
        if (Ask-YesNo "Do you want to provide a value for $k now to add as secret?") {
            $val = Read-Host "$k (enter value)"
        }
    }

    if ($val) {
        Write-Host "Setting secret $k for repo $Repo"
        gh secret set $k --body $val --repo $Repo
    }
}

Write-Host "Done. Verify secrets at: https://github.com/$Repo/settings/secrets/actions"