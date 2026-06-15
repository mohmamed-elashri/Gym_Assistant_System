#!/usr/bin/env pwsh

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$env:DJANGO_SETTINGS_MODULE = "gym_config.settings"
& ".\.venv\Scripts\python.exe" manage.py check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& ".\.venv\Scripts\python.exe" -m pytest fitness_api/ -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& ".\.venv\Scripts\python.exe" manage.py test fitness_api.tests -v 1
