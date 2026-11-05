$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$repo = "Anthony0815/jingsai"

$cred = "protocol=https`nhost=github.com`n`n" | git credential fill 2>$null
$raw = ($cred | Where-Object { $_ -like "password=*" } | Select-Object -First 1)
if (-not $raw) { throw "no credential" }
$token = $raw.Substring(9)

$headers = @{
  Authorization = "Bearer $token"
  "User-Agent"  = "dsh-push"
  Accept        = "application/vnd.github+json"
}
$api = "https://api.github.com/repos/$repo"

function PostJson($url, $obj) {
  $json = $obj | ConvertTo-Json -Depth 20 -Compress
  return Invoke-RestMethod $url -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($json)) -ContentType "application/json; charset=utf-8"
}

$files = Get-ChildItem $root -Recurse -File -Force | Where-Object {
  $rel = $_.FullName.Substring($root.Length + 1) -replace "\\", "/"
  $rel -notmatch "^\.git/" -and $rel -notmatch "^shots/" -and $rel -notmatch "__pycache__" -and $rel -notmatch "^logs/" -and
    $rel -notmatch "^aliyun-fc/.*\.zip$" -and $rel -notmatch "\.zip$"
}

$ref = Invoke-RestMethod "$api/git/ref/heads/main" -Headers $headers
$baseCommit = Invoke-RestMethod "$api/git/commits/$($ref.object.sha)" -Headers $headers
$baseTree = $baseCommit.tree.sha

$entries = @()
foreach ($f in $files) {
  $rel = $f.FullName.Substring($root.Length + 1) -replace "\\", "/"
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.FullName))
  $blob = PostJson "$api/git/blobs" @{ content = $b64; encoding = "base64" }
  $entries += @{ path = $rel; mode = "100644"; type = "blob"; sha = $blob.sha }
}

$baseEntries = @{}
try {
  $bt = Invoke-RestMethod "$api/git/trees/$($baseTree)?recursive=1" -Headers $headers
  foreach ($e in $bt.tree) { if ($e.type -eq "blob") { $baseEntries[$e.path] = $e } }
} catch { }
$localPaths = @{}
foreach ($e in $entries) { $localPaths[$e.path] = $true }
foreach ($k in $baseEntries.Keys) {
  if (-not $localPaths.ContainsKey($k)) {
    $e = $baseEntries[$k]
    $entries += @{ path = $k; mode = $e.mode; type = "blob"; sha = $e.sha }
  }
}

$tree = PostJson "$api/git/trees" @{ base_tree = $baseTree; tree = $entries }

$d = Get-Content (Join-Path $root "data/notices.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$msg = "chore: 同步官方通知 " + $d.generatedAt
$commit = PostJson "$api/git/commits" @{ message = $msg; tree = $tree.sha; parents = @($ref.object.sha) }
if ($commit.sha -eq $ref.object.sha) { Write-Output "no change"; return }

Invoke-RestMethod "$api/git/refs/heads/main" -Method Patch -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes((@{ sha = $commit.sha; force = $true } | ConvertTo-Json -Compress))) -ContentType "application/json; charset=utf-8" | Out-Null
Write-Output ("pushed " + $commit.sha + " (" + $d.counts.total + " items)")
