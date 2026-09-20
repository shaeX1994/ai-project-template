# Validate rules, documentation, and todo consistency.
$ErrorActionPreference = "Stop"
python (Join-Path $PSScriptRoot "ai.py") check @args
exit $LASTEXITCODE
