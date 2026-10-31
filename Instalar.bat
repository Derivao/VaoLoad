@echo off
setlocal
cd /d "%~dp0"
title Instalar VaoLoad
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 goto python_missing
py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import tkinter, customtkinter, imageio_ffmpeg, yt_dlp; print('FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
if errorlevel 1 goto failed
node --version >nul 2>&1
if errorlevel 1 echo Falta Node.js LTS. Instalalo desde https://nodejs.org antes de descargar.
echo.
echo Instalacion terminada. Abre Iniciar.bat.
pause
exit /b 0
:python_missing
echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
echo Incluye Python Launcher y Tcl/Tk. Luego vuelve a abrir este archivo.
pause
exit /b 1
:failed
echo.
echo La instalacion fallo. Revisa el error de arriba y tu conexion.
pause
exit /b 1
