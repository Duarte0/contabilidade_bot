#!/bin/bash
# =================================================================
# Script de Inicialização do Banco de Dados
# =================================================================
# 
# Este script inicializa o banco de dados PostgreSQL com todas
# as tabelas necessárias para o sistema.
#
# USO:
#   ./scripts/init_db.sh
#
# =================================================================

set -e

echo "🗄️  Iniciando configuração do banco de dados..."

# Carregar variáveis de ambiente
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Variáveis de ambiente carregadas"
else
    echo "❌ Arquivo .env não encontrado!"
    echo "   Copie .env.example para .env e configure suas credenciais"
    exit 1
fi

# Aguardar banco estar pronto (se estiver usando Docker)
echo "⏳ Aguardando PostgreSQL ficar pronto..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL ainda não está pronto - aguardando..."
  sleep 2
done

echo "✅ PostgreSQL está pronto!"

# Criar banco se não existir
echo "📦 Verificando banco de dados..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE $POSTGRES_DB'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB')\gexec
EOSQL

echo "✅ Banco de dados verificado/criado"

# Executar script SQL de inicialização
echo "🔧 Criando tabelas..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL

-- =================================================================
-- TABELA: clientes
-- =================================================================
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE,
    inadimplente BOOLEAN DEFAULT FALSE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_ultima_cobranca TIMESTAMP,
    observacoes TEXT
);

CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone);
CREATE INDEX IF NOT EXISTS idx_clientes_ativo ON clientes(ativo);
CREATE INDEX IF NOT EXISTS idx_clientes_inadimplente ON clientes(inadimplente);

-- =================================================================
-- TABELA: templates
-- =================================================================
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    mensagem TEXT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_templates_tipo ON templates(tipo);
CREATE INDEX IF NOT EXISTS idx_templates_ativo ON templates(ativo);

-- =================================================================
-- TABELA: historico_cobrancas
-- =================================================================
CREATE TABLE IF NOT EXISTS historico_cobrancas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    mensagem TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resposta_api TEXT,
    erro TEXT,
    template_id INTEGER REFERENCES templates(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_historico_cliente ON historico_cobrancas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_cobrancas(data_envio);
CREATE INDEX IF NOT EXISTS idx_historico_status ON historico_cobrancas(status);
CREATE INDEX IF NOT EXISTS idx_historico_tipo ON historico_cobrancas(tipo);

-- =================================================================
-- TABELA: documentos_config
-- =================================================================
CREATE TABLE IF NOT EXISTS documentos_config (
    id SERIAL PRIMARY KEY,
    tipo_documento VARCHAR(100) NOT NULL,
    nome_exibicao VARCHAR(200) NOT NULL,
    descricao TEXT,
    template_mensagem TEXT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    dias_antecedencia INTEGER DEFAULT 5,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documentos_config_ativo ON documentos_config(ativo);

-- =================================================================
-- TABELA: solicitacoes_documentos
-- =================================================================
CREATE TABLE IF NOT EXISTS solicitacoes_documentos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
    documento_config_id INTEGER REFERENCES documentos_config(id) ON DELETE CASCADE,
    dia_envio INTEGER NOT NULL,
    mensagem_personalizada TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solicitacoes_cliente ON solicitacoes_documentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_config ON solicitacoes_documentos(documento_config_id);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_ativo ON solicitacoes_documentos(ativo);

-- =================================================================
-- TABELA: historico_solicitacoes
-- =================================================================
CREATE TABLE IF NOT EXISTS historico_solicitacoes (
    id SERIAL PRIMARY KEY,
    solicitacao_id INTEGER REFERENCES solicitacoes_documentos(id) ON DELETE CASCADE,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE CASCADE,
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_recebimento TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pendente',
    mensagem_enviada TEXT,
    observacoes TEXT
);

CREATE INDEX IF NOT EXISTS idx_historico_sol_cliente ON historico_solicitacoes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_historico_sol_status ON historico_solicitacoes(status);
CREATE INDEX IF NOT EXISTS idx_historico_sol_data ON historico_solicitacoes(data_solicitacao);

-- =================================================================
-- INSERIR TEMPLATES PADRÃO
-- =================================================================

-- Template de cobrança financeira
INSERT INTO templates (nome, tipo, mensagem, ativo)
VALUES (
    'cobranca_padrao',
    'financeira',
    'Olá \${nome}! 😊

Espero que esteja tudo bem!

Estou enviando a cobrança dos honorários contábeis referentes ao mês atual.

💰 Valor: R$ \${valor}
📅 Vencimento: \${data_vencimento}

Por favor, realize o pagamento até a data de vencimento para evitar juros e multas.

Qualquer dúvida, estou à disposição!

Att,
Equipe de Contabilidade',
    TRUE
) ON CONFLICT (nome) DO NOTHING;

-- Template de solicitação de documentos
INSERT INTO templates (nome, tipo, mensagem, ativo)
VALUES (
    'solicitacao_documentos',
    'documento',
    'Olá \${nome}! 📄

Tudo bem?

Para dar continuidade aos serviços contábeis, preciso que você envie os seguintes documentos:

📋 Documentos necessários:
- Extratos bancários do mês
- Notas fiscais de entrada e saída
- Folha de pagamento
- Guias de impostos

📅 Prazo: até \${data_limite}

Por favor, envie os documentos o quanto antes para evitar atrasos no seu balancete.

Obrigado! 🙏',
    TRUE
) ON CONFLICT (nome) DO NOTHING;

-- Template de lembrete de atraso
INSERT INTO templates (nome, tipo, mensagem, ativo)
VALUES (
    'lembrete_atraso',
    'financeira',
    'Olá \${nome},

Notamos que o pagamento dos honorários contábeis está em atraso.

⚠️ Detalhes:
- Valor: R$ \${valor}
- Vencimento: \${data_vencimento}
- Atraso: \${dias_atraso} dias

Para evitar a suspensão dos serviços, solicitamos a regularização o quanto antes.

Estamos à disposição para negociar.

Att,
Departamento Financeiro',
    TRUE
) ON CONFLICT (nome) DO NOTHING;

-- =================================================================
-- INSERIR CONFIGURAÇÕES DE DOCUMENTOS PADRÃO
-- =================================================================

INSERT INTO documentos_config (tipo_documento, nome_exibicao, descricao, template_mensagem, dias_antecedencia)
VALUES (
    'extratos_bancarios',
    'Extratos Bancários',
    'Extratos bancários do mês para balancete',
    'Olá \${nome}! Preciso dos extratos bancários do mês para fazer o balancete. Por favor, envie até \${data_limite}. Obrigado!',
    5
) ON CONFLICT (tipo_documento) DO NOTHING;

INSERT INTO documentos_config (tipo_documento, nome_exibicao, descricao, template_mensagem, dias_antecedencia)
VALUES (
    'notas_fiscais',
    'Notas Fiscais',
    'Notas fiscais de entrada e saída do mês',
    'Olá \${nome}! Preciso das notas fiscais de entrada e saída do mês. Por favor, envie até \${data_limite}. Obrigado!',
    5
) ON CONFLICT (tipo_documento) DO NOTHING;

-- =================================================================
-- CRIAR USUÁRIO ADMIN PADRÃO (FUTURO)
-- =================================================================
-- CREATE TABLE IF NOT EXISTS usuarios (
--     id SERIAL PRIMARY KEY,
--     nome VARCHAR(255) NOT NULL,
--     email VARCHAR(255) UNIQUE NOT NULL,
--     senha_hash VARCHAR(255) NOT NULL,
--     nivel VARCHAR(50) DEFAULT 'operador',
--     ativo BOOLEAN DEFAULT TRUE,
--     data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

EOSQL

echo "✅ Tabelas criadas com sucesso!"

# Verificar se há clientes
echo "📊 Verificando dados..."
CLIENTE_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM clientes;")

echo "   Clientes cadastrados: $CLIENTE_COUNT"

TEMPLATE_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM templates;")

echo "   Templates disponíveis: $TEMPLATE_COUNT"

echo ""
echo "✅ Banco de dados inicializado com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Adicione clientes via interface web ou API"
echo "   2. Configure templates personalizados se necessário"
echo "   3. Inicie o envio de mensagens"
echo ""
