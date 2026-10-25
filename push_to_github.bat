@echo off
title Push Mlzmodel to GitHub
cd /d "%~dp0"

echo ======================================================================
echo   Pushing Mlzmodel to https://github.com/bluradota/mlzmodel-power
echo ======================================================================
echo.
echo Make sure you have created the empty repository on https://github.com/new
echo named 'mlzmodel-power' before running this script.
echo.
echo Pushing branch 'main' to GitHub...
echo (If a browser window appears, click 'Authorize Git Credential Manager')
echo.

git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ======================================================================
    echo   SUCCESS! All files are now published to GitHub!
    echo   Repo: https://github.com/bluradota/mlzmodel-power
    echo   Next step: Go to https://share.streamlit.io to deploy in 1 click!
    echo ======================================================================
) else (
    echo ======================================================================
    echo   Push failed. Please ensure:
    echo   1. The repository 'mlzmodel-power' exists at https://github.com/new
    echo   2. You are logged into your GitHub account: bluradota
    echo ======================================================================
)

echo.
pause
