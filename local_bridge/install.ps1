param([switch]$ReplaceToken)
$ErrorActionPreference = "Stop"

$localDir = Join-Path $env:LOCALAPPDATA "pku-lectures"
$secretPath = Join-Path $localDir "github-token.dpapi"
$nodePathFile = Join-Path $localDir "node-path.txt"
$runPath = Join-Path $PSScriptRoot "run.ps1"
$taskName = "PKU Lectures - WeRSS Bridge"

New-Item -ItemType Directory -Force -Path $localDir | Out-Null
$nodePath = (Get-Command node -ErrorAction Stop).Source
$nodePath | Set-Content -LiteralPath $nodePathFile -Encoding UTF8

if ($ReplaceToken -or -not (Test-Path -LiteralPath $secretPath)) {
    Write-Host "Paste the GitHub token and press Enter. The token will not be displayed:"
    $secureToken = Read-Host -AsSecureString
    $secureToken | ConvertFrom-SecureString | Set-Content -LiteralPath $secretPath -Encoding UTF8
}
else {
    Write-Host "Using the encrypted GitHub token already stored for this Windows user."
}

$action = New-ScheduledTaskAction `
    -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runPath`""

$triggers = @(
    New-ScheduledTaskTrigger -Daily -At "08:27"
)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description "Send new WeRSS articles to pku-lectures GitHub Issues; max 10 per day." `
    -Force | Out-Null

Write-Host "The token is encrypted for the current Windows user. The scheduled task is ready."
Write-Host "Running the first check..."
& $runPath
