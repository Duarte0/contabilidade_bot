# Automação Digisac Mensagens

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Digisac](https://img.shields.io/badge/Digisac-API-green)

## 📝 Descrição do Projeto
Sistema de automação para envio em massa de mensagens via Digisac, especializado em cobranças recorrentes e comunicação automatizada com clientes.

## 🚀 Status do Projeto
> **Em desenvolvimento** 

## 🎯 Funcionalidades e Demonstração da Aplicação

### Funcionalidades Principais
- **Cobranças Automáticas** - Agendamento diário de mensagens
- **Respostas Inteligentes** - Processamento automático de interações
- **Gestão de Clientes** - Controle de status e histórico
- **Templates Personalizáveis** - Mensagens dinâmicas e profissionais

## Configuração para uso
```
# 1. CONFIGURAÇÕES DIGISAC 
# ---------------------------------------
# Obtenha seu token em: https://seu_subdominio.digisac.chat
DIGISAC_API_URL=https://seu_subdominio.digisac.chat/api/v1
DIGISAC_API_TOKEN=seu_token_digisac_aqui

# Webhook URL (obter executando: ngrok http 5000)
DIGISAC_WEBHOOK_URL=https://seu-subdominio.ngrok-free.dev

# 2. BANCO DE DADOS POSTGRESQL
# -------------------------------------------
# Configure o PostgreSQL via Docker:
# docker run --name cobranca-postgres -e POSTGRES_PASSWORD=sua_senha -p 5432:5432 -d postgres:15
# docker exec -it cobranca-postgres psql -U postgres -c "CREATE DATABASE cobranca_db;"

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cobranca_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_postgres
```

## Instalação Rápida
```
git clone https://github.com/Duarte0/automacao-digisac-mensagens.git
cd automacao-digisac-mensagens
pip install -r requirements.txt
python src/services/webhook_handler.py
ngrok http 5000
python src/main.py
```
