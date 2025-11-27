# Sistema de Envio de Mensagens WhatsApp

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## Sobre o Sistema

Sistema web para envio de mensagens em lote via WhatsApp usando a API do Digisac.

### Funcionalidades

- Interface web para gerenciamento de clientes
- Sistema de templates de mensagens personalizáveis
- Envio de mensagens em lote
- Dashboard com estatísticas
- Histórico completo de envios
- Importação de contatos do Digisac

### Arquitetura

```
Frontend (Web UI) → API REST (FastAPI) → PostgreSQL + Digisac API
```

- **Frontend**: Interface web (HTML/CSS/JS)
- **Backend**: API REST com FastAPI
- **Banco de Dados**: PostgreSQL
- **Integração**: Digisac WhatsApp API
- **Deploy**: Docker Compose

## Início Rápido

### Docker

```bash
# 1. Clone e configure
git clone <seu-repo>
cd contabilidade_bot
cp .env.example .env
# Edite .env e adicione seu DIGISAC_API_TOKEN

# 2. Inicie os containers
docker-compose up -d

# 3. Importe contatos do Digisac
docker exec contabilidade_backend sh -c "cd /app && python importar_clientes_digisac.py"

# 4. Crie templates iniciais
docker exec contabilidade_backend sh -c "cd /app && python criar_templates.py"

# 5. Acesse o sistema
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

## Como Usar

### 1. Gerenciar Migrations

**Executar migrations pendentes:**
```bash
docker exec contabilidade_backend sh -c "cd /app/backend/migrations && python migrate.py"
```

**Ver status:**
```bash
docker exec contabilidade_backend sh -c "cd /app/backend/migrations && python migrate.py status"
```

### 2. Importar Clientes do Digisac

```bash
docker exec contabilidade_backend sh -c "cd /app && python importar_clientes_digisac.py"
```

### 3. Criar Templates Iniciais

```bash
docker exec contabilidade_backend sh -c "cd /app && python criar_templates.py"
```

### 4. Enviar Mensagens

**Via Interface Web:**
1. Acesse http://localhost:3000
2. Selecione clientes
3. Escolha ou crie um template
4. Clique em "Enviar"

**Via API:**
```bash
curl -X POST http://localhost:8000/api/cobrancas/enviar-lote \
  -H "Content-Type: application/json" \
  -d '{
    "clientes_ids": [1, 2, 3],
    "tipo": "cobranca",
    "mensagem_padrao": "Olá ${nome}!",
    "enviar_agora": true
  }'
```

## Estrutura do Projeto

```
contabilidade_bot/
├── docker-compose.yml          # Orquestração dos containers
├── Dockerfile.backend          # Container da API
├── Dockerfile.frontend         # Container do frontend
├── .env                        # Configurações (não commitado)
├── .env.example               # Template de configuração
├── importar_clientes_digisac.py  # Importar contatos
│
├── backend/
│   ├── migrations/            # Sistema de migrations
│   │   ├── migrate.py         # Runner de migrations
│   │   └── *.sql             # Arquivos SQL
│   └── scripts/
│       └── adicionar_cliente.py
│
├── src/
│   ├── core/
│   │   ├── config.py          # Configurações
│   │   └── database.py        # Acesso ao banco
│   ├── models/
│   │   └── models.py          # Models de dados
│   ├── services/
│   │   ├── digisac_service.py
│   │   ├── template_engine.py
│   │   ├── template_manager.py
│   │   └── feriados_manager.py
│   └── api/
│       ├── main.py            # FastAPI app
│       └── routes/            # Endpoints
│           ├── clientes.py
│           ├── cobrancas.py
│           ├── templates.py
│           └── dashboard.py
│
└── frontend/
    ├── index.html
    ├── app.js
    └── style.css
```

## Comandos Úteis

### Docker
```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Ver logs
docker-compose logs -f backend

# Reiniciar serviço
docker-compose restart backend
```

### Banco de Dados
```bash
# Acessar banco
docker exec -it contabilidade_postgres psql -U postgres -d contabilidade_db

# Backup
docker exec contabilidade_postgres pg_dump -U postgres contabilidade_db > backup.sql

# Listar clientes
docker exec contabilidade_postgres psql -U postgres -d contabilidade_db -c "SELECT id, nome, telefone FROM clientes LIMIT 10;"
```

### API
```bash
# Health check
curl http://localhost:8000/health

# Documentação
open http://localhost:8000/api/docs

# Listar clientes
curl http://localhost:8000/api/clientes/

# Estatísticas
curl http://localhost:8000/api/dashboard/stats
```

## Segurança

- Nunca commite o arquivo `.env` com credenciais reais
- Use senhas fortes para PostgreSQL em produção
- Configure CORS adequadamente
- Adicione autenticação antes de expor publicamente

## Troubleshooting

**Container não inicia:**
```bash
docker-compose logs backend
docker-compose restart backend
```

**Erro de conexão com banco:**
```bash
docker-compose ps postgres
docker-compose logs postgres
```

**API retorna erro 500:**
```bash
docker-compose logs -f backend
```

## Licença

MIT

---

## 🌐 Compartilhar com Outras Pessoas

Para permitir que outras pessoas acessem o sistema pela internet:

### Opção 1: Ngrok (Rápido e Fácil) ⚡

1. Instale o [ngrok](https://ngrok.com/download)
2. Inicie os túneis:
   ```bash
   ngrok http 8000  # Backend
   ngrok http 3000  # Frontend (em outro terminal)
   ```
3. Configure o `frontend/config.js` com a URL do backend
4. Compartilhe a URL do frontend

**📖 Documentação completa:** [`COMO-COMPARTILHAR.md`](./COMO-COMPARTILHAR.md)  
**⚡ Guia rápido:** [`QUICK-START-NGROK.md`](./QUICK-START-NGROK.md)

### Opção 2: Deploy em Servidor (Produção) 🚀

Para uso permanente, hospede em:
- **Heroku** - Deploy gratuito de Docker
- **Railway** - Deploy simples e rápido
- **AWS/Azure/GCP** - Controle total
- **DigitalOcean** - VPS acessível

---

**Sistema de Mensagens WhatsApp - Digisac Integration**
