ALTER TABLE historico_pagamentos 
DROP COLUMN IF EXISTS confirmado;

ALTER TABLE message_templates 
ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'financeira' 
CHECK (tipo IN ('financeira', 'documento', 'geral'));

UPDATE message_templates 
SET tipo = 'financeira' 
WHERE nome IN ('Cobrança Mensal', 'Lembrete Amigável')
AND tipo IS NULL;

UPDATE message_templates 
SET tipo = 'documento' 
WHERE nome = 'Solicitação de Documentos'
AND tipo IS NULL;

ALTER TABLE cliente_status 
DROP COLUMN IF EXISTS payment_preferences;

CREATE INDEX IF NOT EXISTS idx_templates_tipo ON message_templates(tipo) WHERE ativo = true;

CREATE INDEX IF NOT EXISTS idx_clientes_nome_telefone ON clientes(nome, telefone);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'message_templates' 
        AND column_name = 'tipo'
    ) THEN
        RAISE EXCEPTION 'Coluna tipo não foi criada corretamente';
    END IF;
END $$;
