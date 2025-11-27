@echo off
echo ============================================
echo Verificando Sistema de Mensagens WhatsApp
echo ============================================
echo.

REM 1. Verificar Docker
echo [Docker]
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker instalado
) else (
    echo [ERRO] Docker nao encontrado
)

docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker Compose instalado
) else (
    echo [ERRO] Docker Compose nao encontrado
)

echo.

REM 2. Verificar containers
echo [Containers]
docker compose ps | findstr /C:"contabilidade_backend" | findstr /C:"Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend rodando
) else (
    echo [ERRO] Backend nao esta rodando
)

docker compose ps | findstr /C:"contabilidade_frontend" | findstr /C:"Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend rodando
) else (
    echo [ERRO] Frontend nao esta rodando
)

docker compose ps | findstr /C:"contabilidade_postgres" | findstr /C:"Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL rodando
) else (
    echo [ERRO] PostgreSQL nao esta rodando
)

echo.

REM 3. Verificar saúde dos serviços
echo [Servicos]
curl -s http://localhost:8000/health 2>nul | findstr /C:"healthy" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend saudavel ^(http://localhost:8000^)
) else (
    echo [ERRO] Backend nao responde
)

curl -s -o nul -w "%%{http_code}" http://localhost:3000 2>nul | findstr /C:"200" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend acessivel ^(http://localhost:3000^)
) else (
    echo [ERRO] Frontend nao responde
)

echo.

REM 4. Verificar arquivo .env
echo [Configuracoes]
if exist ".env" (
    echo [OK] Arquivo .env existe
    findstr /C:"DIGISAC_API_TOKEN=" .env | findstr /V /C:"DIGISAC_API_TOKEN=$" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Token Digisac configurado
    ) else (
        echo [AVISO] Token Digisac nao configurado
    )
) else (
    echo [ERRO] Arquivo .env nao encontrado
)

echo.

REM 5. Verificar ngrok
echo [Ngrok - Opcional]
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ngrok instalado
    curl -s http://localhost:4040/api/tunnels 2>nul | findstr /C:"public_url" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Tuneis ngrok ativos
        echo.
        echo    Acesse: http://localhost:4040
    ) else (
        echo [AVISO] Nenhum tunel ativo
        echo    Execute: ngrok http 8000 e ngrok http 3000
    )
) else (
    echo [AVISO] Ngrok nao instalado
    echo    Download: https://ngrok.com/download
)

echo.
echo ============================================
echo Resumo:
echo.
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/api/docs
echo    Health:   http://localhost:8000/health
echo.
echo ============================================
echo.

pause
