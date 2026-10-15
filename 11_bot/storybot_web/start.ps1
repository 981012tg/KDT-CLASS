$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:PYTHONPATH = "$PSScriptRoot/.packages;$projectRoot"
& "$projectRoot/.venv/Scripts/python.exe" -m uvicorn storybot_web.main:app --host 127.0.0.1 --port 8001
