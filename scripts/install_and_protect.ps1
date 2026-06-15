<#
Install GitHub CLI (if possible) and enable branch protection for `main`.
Usage: Run in PowerShell as your user. The script will:
  - Try to install `gh` via `winget` or `choco` if available.
  - Prompt you to run `gh auth login` if not authenticated.
  - Call the GitHub API via `gh` to enable protection on `main`.

Note: `gh auth login` must be completed interactively. The script does not store tokens.
#>

$ErrorActionPreference = 'Stop'
$repo = 'mohmamed-elashri/Gym_Assistant_System'

function Install-GH {
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        Write-Host "gh already installed." -ForegroundColor Green
        return $true
    }

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing GitHub CLI via winget..."
        winget install --id GitHub.cli -e --source winget
    }
    elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing GitHub CLI via Chocolatey..."
        choco install gh -y
    }
    else {
        Write-Host "No supported installer found (winget/choco). Please install GitHub CLI manually:" -ForegroundColor Yellow
        Write-Host "https://github.com/cli/cli/releases"
        return $false
    }

    return (Get-Command gh -ErrorAction SilentlyContinue) -ne $null
}

if (-not (Install-GH)) {
    Write-Host "Failed to install gh. Exiting." -ForegroundColor Red
    exit 1
}

# Check authentication
$authExit = 0
try {
    gh auth status > $null 2>&1
    $authExit = $LASTEXITCODE
} catch { $authExit = $LASTEXITCODE }

if ($authExit -ne 0) {
    Write-Host "gh not authenticated. Starting interactive 'gh auth login'..." -ForegroundColor Yellow
    gh auth login
}

Write-Host "Enabling branch protection on $repo (branch: main)" -ForegroundColor Cyan

$body = @{
    required_status_checks = @{ strict = $true; contexts = @() }
    enforce_admins = $true
    required_pull_request_reviews = @{ dismiss_stale_reviews = $true }
} | ConvertTo-Json -Depth 10

$tmp = New-TemporaryFile
$tmpPath = $tmp.FullName
$body | Out-File -FilePath $tmpPath -Encoding utf8

try {
    gh api --method PUT -H "Accept: application/vnd.github+json" "/repos/$repo/branches/main/protection" --input $tmpPath
    Write-Host "Branch protection applied." -ForegroundColor Green
} catch {
    Write-Host "Failed to apply branch protection:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
} finally {
    Remove-Item $tmpPath -ErrorAction SilentlyContinue
}
