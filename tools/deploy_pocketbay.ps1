#requires -version 5.1
<#
Deploy the built single-file page to a PocketBay project (default 3681).

  powershell -NoProfile -ExecutionPolicy Bypass -File tools\deploy_pocketbay.ps1 -ProjectId 3681

Token lookup order: -Token  ->  %USERPROFILE%\.pocketbay\token.txt  ->  $env:POCKETBAY_TOKEN
Create the token at: pocketbay.com -> avatar menu -> API tokens (shown only once).

Uploads a zip that contains ONLY index.html (CSS/JS/data inlined), so the
platform never has to resolve assets/app.js or tools/app.js again.

Exit signal: prints POCKETBAY_DEPLOY_OK on success, POCKETBAY_DEPLOY_FAILED otherwise.
No `exit` calls, so it is safe to call from another script.
#>
param(
    [string]$Token = "",
    [int]$ProjectId = 3681,
    [string]$Root = "",
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

if (-not $Root) { $Root = Split-Path $PSScriptRoot -Parent }
$index = Join-Path $Root "index.html"
if (-not (Test-Path $index)) {
    Write-Output "POCKETBAY_DEPLOY_FAILED index.html not found: $index"
    return
}

if (-not $Token) {
    $tokenFile = Join-Path $env:USERPROFILE ".pocketbay\token.txt"
    if (Test-Path $tokenFile) { $Token = (Get-Content $tokenFile -Raw).Trim() }
}
if (-not $Token) { $Token = $env:POCKETBAY_TOKEN }
if (-not $Token) {
    Write-Output "POCKETBAY_DEPLOY_FAILED no API token (pocketbay.com -> avatar -> API tokens)"
    return
}

$stage = Join-Path $env:TEMP ("pb_deploy_" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $stage | Out-Null
Copy-Item $index (Join-Path $stage "index.html")

$zip = Join-Path $env:TEMP "pocketbay-site.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($stage, $zip, [IO.Compression.CompressionLevel]::Optimal, $false)

$base = "https://pocketbay.com/api/projects/$ProjectId"
Write-Output ("uploading index.html ({0:N0} KB) to project {1}" -f ((Get-Item $zip).Length / 1024), $ProjectId)

$resp = & curl.exe -s -S -X POST -H "Authorization: Bearer $Token" -F "file=@$zip" "$base/deploy" 2>&1
Write-Output ("deploy response: " + ($resp -join " "))

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$state = "unknown"
$raw = ""
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 6
    $raw = & curl.exe -s -S -H "Authorization: Bearer $Token" "$base/deploy/status" 2>&1
    try { $st = ($raw -join "`n") | ConvertFrom-Json } catch { continue }
    $state = "$($st.status)/$($st.phase)"
    Write-Output ("status={0} phase={1} stage={2}" -f $st.status, $st.phase, (($st.stage_events) -join ">"))
    if ($st.phase -eq "success" -and $st.status -in @("running", "success")) { break }
    if ($st.status -in @("failed", "error") -or $st.phase -eq "failed") { break }
}

Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue

if ($state -like "*/success" -or $state -like "success/*") {
    Write-Output "POCKETBAY_DEPLOY_OK $state"
} else {
    Write-Output ("POCKETBAY_DEPLOY_FAILED " + $state)
}
