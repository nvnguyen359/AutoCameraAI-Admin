param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Chay tien trinh Build EXE & Update Version len GitHub..." -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($Message)) {
    python build_and_release.py
} else {
    python build_and_release.py "$Message"
}

