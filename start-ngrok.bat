@echo off
echo ====================================
echo Iniciando Túneis Ngrok
echo ====================================
echo.
echo Iniciando túnel para FRONTEND (porta 3000)...
start cmd /k "ngrok http 3000 --log stdout"
timeout /t 2 /nobreak > nul
echo.
echo Iniciando túnel para BACKEND (porta 8000)...
start cmd /k "ngrok http 8000 --log stdout"
echo.
echo ====================================
echo Túneis iniciados!
echo ====================================
echo.
echo IMPORTANTE:
echo 1. Anote as URLs geradas por cada túnel
echo 2. Compartilhe apenas a URL do FRONTEND com outros usuários
echo 3. A comunicação entre frontend e backend será automática
echo.
pause
