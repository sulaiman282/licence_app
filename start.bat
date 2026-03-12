@echo off
title Spidy License Server
color 0B
echo.
echo ========================================
echo   Spidy License Server
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server on http://localhost:5000
echo.
python app.py
pause
