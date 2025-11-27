CREATE TABLE IF NOT EXISTS _backup_historico_cobrancas AS 
SELECT * FROM historico_cobrancas;
DROP TABLE IF EXISTS historico_solicitacoes CASCADE;
DROP TABLE IF EXISTS documentos_config CASCADE;
DROP TABLE IF EXISTS solicitacoes_documentos CASCADE;
DROP TABLE IF EXISTS interacoes_cliente CASCADE;
DROP TABLE IF EXISTS historico_pagamentos CASCADE;
DROP TABLE IF EXISTS cliente_status CASCADE;
DROP TABLE IF EXISTS contas_config CASCADE;
DROP TABLE IF EXISTS contas_fixas CASCADE;
ALTER TABLE historico_cobrancas RENAME TO historico_envios;
ALTER TABLE historico_envios DROP COLUMN IF EXISTS conta_id;
ALTER TABLE historico_envios ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'financeira' 
CHECK (tipo IN ('financeira', 'documento', 'geral'));
ALTER TABLE historico_envios ADD COLUMN IF NOT EXISTS template_usado TEXT;

DROP INDEX IF EXISTS idx_contas_fixas_cliente_id;
DROP INDEX IF EXISTS idx_contas_config_conta_id;
DROP INDEX IF EXISTS idx_contas_config_prox_data;
DROP INDEX IF EXISTS idx_historico_pagamentos_cliente_id;
DROP INDEX IF EXISTS idx_historico_pagamentos_data;
DROP INDEX IF EXISTS idx_cliente_status_cliente_id;
DROP INDEX IF EXISTS idx_cliente_status_last_payment;
DROP INDEX IF EXISTS idx_solicitacoes_documentos_cliente_id;
DROP INDEX IF EXISTS idx_documentos_config_prox_data;
DROP INDEX IF EXISTS idx_historico_solicitacoes_cliente_id;
DROP INDEX IF EXISTS idx_historico_solicitacoes_data;

DROP INDEX IF EXISTS idx_historico_cobrancas_cliente_id;
DROP INDEX IF EXISTS idx_historico_cobrancas_data_envio;

CREATE INDEX IF NOT EXISTS idx_historico_envios_cliente_id ON historico_envios(cliente_id);
CREATE INDEX IF NOT EXISTS idx_historico_envios_data_envio ON historico_envios(data_envio);
CREATE INDEX IF NOT EXISTS idx_historico_envios_tipo ON historico_envios(tipo);
CREATE INDEX IF NOT EXISTS idx_historico_envios_status ON historico_envios(status);

CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone);


ALTER TABLE clientes ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'ativo' 
CHECK (status IN ('ativo', 'inativo', 'suspenso'));

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN (
        'contas_fixas', 'contas_config', 'historico_pagamentos',
        'cliente_status', 'interacoes_cliente', 'solicitacoes_documentos',
        'documentos_config', 'historico_solicitacoes'
    );
    
    IF table_count > 0 THEN
        RAISE EXCEPTION 'Algumas tabelas não foram removidas corretamente';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'historico_envios'
    ) THEN
        RAISE EXCEPTION 'Tabela historico_envios não foi criada';
    END IF;
    
    RAISE NOTICE ' Migration concluída: Schema simplificado com sucesso!';
END $$;
