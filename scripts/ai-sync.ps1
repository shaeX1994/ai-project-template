# Generate model entry points from .ai/. Pass --check to fail on drift instead of writing.
$ErrorActionPreference = "Stop"
python (Join-Path $PSScriptRoot "ai.py") sync @args
exit $LASTEXITCODE
