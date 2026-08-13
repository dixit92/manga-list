@echo off
REM Build script for MangaList Windows executable
REM Creates a single-file executable using PyInstaller

setlocal enabledelayedexpansion

echo ===========================================
echo Building MangaList Executable
echo ===========================================
echo.

REM Check if we're in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: No virtual environment detected.
    echo It's recommended to use a venv: python -m venv .venv
    echo.
)

REM Install/update requirements
echo Installing dependencies...
pip install -r requirements-dev.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller MangaList.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

REM Verify output
if exist "dist\MangaList.exe" (
    echo.
    echo ===========================================
    echo Build successful!
    echo Output: dist\MangaList.exe
    echo ===========================================
    echo.
    echo File size:
    dir "dist\MangaList.exe" | find "MangaList.exe"
) else (
    echo ERROR: Expected output file not found
    exit /b 1
)

endlocal
