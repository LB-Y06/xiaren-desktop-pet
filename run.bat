@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python 启动器。请先安装 Python 3.10 或更高版本。
  pause
  exit /b 1
)

py -3 -c "import PyQt5" >nul 2>nul
if errorlevel 1 (
  echo 正在安装界面依赖，请稍候...
  py -3 -m pip install -r requirements.txt
  if errorlevel 1 (
    echo 依赖安装失败，请检查网络后重试。
    pause
    exit /b 1
  )
)

start "" pyw -3 main.py

