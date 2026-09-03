$ErrorActionPreference = "Stop"
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

$localDir = Join-Path $env:LOCALAPPDATA "pku-lectures"
$secretPath = Join-Path $localDir "github-token.dpapi"
$nodePathFile = Join-Path $localDir "node-path.txt"
$logPath = Join-Path $localDir "bridge.log"
$bridgePath = Join-Path $PSScriptRoot "bridge.mjs"

New-Item -ItemType Directory -Force -Path $localDir | Out-Null

$stage = "initialization"
try {
    $stage = "checking local files"
    if (-not (Test-Path -LiteralPath $secretPath)) {
        throw "GitHub token is not configured. Run install.ps1 first."
    }
    if (-not (Test-Path -LiteralPath $nodePathFile)) {
        throw "Node.js path is not configured. Run install.ps1 again."
    }
    $nodePath = (Get-Content -LiteralPath $nodePathFile -Raw).Trim().TrimStart([char]0xFEFF)
    if (-not (Test-Path -LiteralPath $nodePath)) {
        throw "Node executable not found: $nodePath"
    }
    if (-not (Test-Path -LiteralPath $bridgePath)) {
        throw "Bridge script not found: $bridgePath"
    }
    $stage = "reading encrypted token"
    $encryptedToken = (Get-Content -LiteralPath $secretPath -Raw).Trim()
    $stage = "decrypting token"
    $secureToken = $encryptedToken | ConvertTo-SecureString
    $stage = "opening secure token"
    $tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    try {
        $env:PKU_LECTURES_GITHUB_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
        $stage = "running bridge"
        & $nodePath $bridgePath 2>&1 | Tee-Object -FilePath $logPath -Append
        if ($LASTEXITCODE -ne 0) {
            throw "Bridge exited with code $LASTEXITCODE."
        }
    }
    finally {
        Remove-Item Env:\PKU_LECTURES_GITHUB_TOKEN -ErrorAction SilentlyContinue
        if ($tokenPointer) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
        }
    }
}
catch {
    "$(Get-Date -Format s) [$stage] $($_.Exception.Message)" | Tee-Object -FilePath $logPath -Append
    exit 1
}
