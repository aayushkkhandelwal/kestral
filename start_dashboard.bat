@echo off
echo ==========================================
echo Starting Kestral ATM Vision AI Dashboard
echo ==========================================
cd /d "%~dp0atm-vision-ai-dashboard"
echo Access locally: https://localhost:3000
echo Access on Wi-Fi (Webcam enabled): https://192.168.2.105:3000
npm run dev:https
pause
