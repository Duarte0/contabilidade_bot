#!/bin/bash
# Script de verificação do sistema

echo "🔍 Verificando Sistema de Mensagens WhatsApp"
echo "=============================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# 1. Verificar Docker
echo "📦 Verificando Docker..."
docker --version > /dev/null 2>&1
check "Docker instalado"

docker compose version > /dev/null 2>&1
check "Docker Compose instalado"

# 2. Verificar containers
echo ""
echo "🐳 Verificando Containers..."
docker compose ps | grep -q "contabilidade_backend.*Up"
check "Backend rodando"

docker compose ps | grep -q "contabilidade_frontend.*Up"
check "Frontend rodando"

docker compose ps | grep -q "contabilidade_postgres.*Up"
check "PostgreSQL rodando"

# 3. Verificar saúde dos serviços
echo ""
echo "🏥 Verificando Saúde dos Serviços..."

# Backend Health
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | grep -o '"status":"healthy"')
if [ ! -z "$BACKEND_HEALTH" ]; then
    echo -e "${GREEN}✓${NC} Backend saudável (http://localhost:8000)"
else
    echo -e "${RED}✗${NC} Backend não responde (http://localhost:8000)"
fi

# Frontend
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND_TEST" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend acessível (http://localhost:3000)"
else
    echo -e "${RED}✗${NC} Frontend não responde (http://localhost:3000)"
fi

# 4. Verificar banco de dados
echo ""
echo "🗄️  Verificando Banco de Dados..."
DB_TEST=$(docker exec contabilidade_postgres psql -U postgres -d cobranca_db -c "SELECT COUNT(*) FROM clientes;" 2>/dev/null | grep -E "^[0-9]+$")
if [ ! -z "$DB_TEST" ]; then
    echo -e "${GREEN}✓${NC} Banco de dados conectado ($DB_TEST clientes cadastrados)"
else
    echo -e "${YELLOW}⚠${NC} Banco conectado mas sem dados (execute importar_clientes_digisac.py)"
fi

# 5. Verificar arquivo .env
echo ""
echo "⚙️  Verificando Configurações..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Arquivo .env existe"
    
    if grep -q "DIGISAC_API_TOKEN=.*[a-zA-Z0-9]" .env; then
        echo -e "${GREEN}✓${NC} Token Digisac configurado"
    else
        echo -e "${YELLOW}⚠${NC} Token Digisac não configurado"
    fi
else
    echo -e "${RED}✗${NC} Arquivo .env não encontrado"
fi

# 6. Verificar ngrok (opcional)
echo ""
echo "🌐 Verificando Ngrok (opcional)..."
if command -v ngrok &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ngrok instalado"
    
    # Verificar se há túneis ativos
    NGROK_TUNNELS=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url"' | wc -l)
    if [ "$NGROK_TUNNELS" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} $NGROK_TUNNELS túnel(is) ngrok ativo(s)"
        echo ""
        echo "   🔗 Acesse http://localhost:4040 para ver as URLs"
    else
        echo -e "${YELLOW}⚠${NC} Nenhum túnel ngrok ativo"
        echo "   Execute: ngrok http 8000 e ngrok http 3000"
    fi
else
    echo -e "${YELLOW}⚠${NC} Ngrok não instalado (opcional para compartilhar)"
    echo "   Download: https://ngrok.com/download"
fi

# Resumo Final
echo ""
echo "=============================================="
echo "📊 Resumo:"
echo ""
echo "   🌍 Frontend: http://localhost:3000"
echo "   🔌 Backend:  http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/api/docs"
echo "   🏥 Health:   http://localhost:8000/health"
echo ""

# Verificar se tudo está OK
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Sistema pronto para uso!${NC}"
else
    echo -e "${RED}⚠️  Alguns serviços não estão rodando${NC}"
    echo ""
    echo "Execute: docker compose up -d"
fi

echo ""
echo "=============================================="
