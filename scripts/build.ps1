$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $projectRoot "dist"
$packageRoot = Join-Path $outputRoot "xiaren-desktop-pet"

Push-Location $projectRoot
try {
    python -m pip install -r requirements-dev.txt
    python -m PyInstaller --noconfirm --clean --onefile --windowed --name "虾仁桌宠" main.py

    New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $outputRoot "虾仁桌宠.exe") -Destination $packageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot "assets") -Destination $packageRoot -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot "使用说明.txt") -Destination $packageRoot -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path (Join-Path $packageRoot "data") -Force | Out-Null

    Compress-Archive -LiteralPath $packageRoot -DestinationPath (Join-Path $outputRoot "xiaren-desktop-pet-windows.zip") -Force
    Write-Host "构建完成：dist/xiaren-desktop-pet-windows.zip"
}
finally {
    Pop-Location
}

