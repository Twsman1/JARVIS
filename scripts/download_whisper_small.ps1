param(
  [string]$OutDir = "models/whisper-small",
  [string]$Repo = "Systran/faster-whisper-small",
  [string]$Revision = "main"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Download-File([string]$Url, [string]$DestPath) {
  Ensure-Dir (Split-Path -Parent $DestPath)
  Write-Host "Downloading $Url -> $DestPath"
  Invoke-WebRequest -Uri $Url -OutFile $DestPath -UseBasicParsing
}

Write-Host "== Jarvis Whisper Offline Downloader =="
Write-Host "Repo: $Repo  Revision: $Revision"
Write-Host "OutDir: $OutDir"

Ensure-Dir $OutDir

# Get model file list from Hugging Face API
$apiUrl = "https://huggingface.co/api/models/$Repo?revision=$Revision"
Write-Host "Fetching file list: $apiUrl"
$modelInfo = Invoke-RestMethod -Uri $apiUrl -Method GET

if (-not $modelInfo.siblings) {
  throw "Could not read file list from Hugging Face API (no 'siblings')."
}

# Download every file in the repo snapshot (best for compatibility)
$files = @()
foreach ($s in $modelInfo.siblings) {
  if ($s.rfilename) { $files += $s.rfilename }
}

if ($files.Count -eq 0) {
  throw "No files found in model repo."
}

Write-Host "Found $($files.Count) files."

foreach ($f in $files) {
  # skip LFS pointer metadata in case it appears (usually not listed separately)
  $dest = Join-Path $OutDir $f
  $url = "https://huggingface.co/$Repo/resolve/$Revision/$f"
  Download-File -Url $url -DestPath $dest
}

# Basic sanity check
$bin = Join-Path $OutDir "model.bin"
if (-not (Test-Path -LiteralPath $bin)) {
  throw "Download finished but model.bin was not found at '$bin'."
}

Write-Host ""
Write-Host "Done. Model is available locally at '$OutDir'."
Write-Host "Next run should be 100% offline (no Hugging Face requests)."

