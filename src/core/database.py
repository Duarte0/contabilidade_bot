import sqlite3
from datetime import datetime
from typing import List, Optional
from models.models import Cliente, ClienteStatus, ContaConfig, ContaFixa, MessageTemplate

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Inicializa todas as tabelas do sistema"""
        tables = [
            # Clientes
            '''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                digisac_contact_id TEXT UNIQUE NOT NULL,
                telefone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            # Contas fixas (fonte única do dia_vencimento)
            '''
            CREATE TABLE IF NOT EXISTS contas_fixas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                dia_vencimento INTEGER NOT NULL CHECK (dia_vencimento BETWEEN 1 AND 31),
                ativo BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            # Configurações de agendamento
            '''
            CREATE TABLE IF NOT EXISTS contas_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conta_id INTEGER UNIQUE NOT NULL,
                frequencia TEXT DEFAULT 'mensal' CHECK (frequencia IN ('diaria', 'semanal', 'quinzenal', 'mensal', 'bimestral')),
                prox_data_cobranca DATE,
                feriados_ajustar BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conta_id) REFERENCES contas_fixas (id) ON DELETE CASCADE
            )
            ''',
            # Histórico de cobranças
            '''
            CREATE TABLE IF NOT EXISTS historico_cobrancas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                conta_id INTEGER NOT NULL,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mensagem TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('enviado', 'erro', 'pendente')),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE,
                FOREIGN KEY (conta_id) REFERENCES contas_fixas (id) ON DELETE CASCADE
            )
            ''',
            # Status do cliente
            '''
            CREATE TABLE IF NOT EXISTS cliente_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER UNIQUE NOT NULL,
                status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inadimplente', 'suspenso', 'cancelado')),
                last_payment_date DATE,
                dias_tolerancia INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            # Histórico de pagamentos
            '''
            CREATE TABLE IF NOT EXISTS historico_pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                valor REAL NOT NULL CHECK (valor > 0),
                data_pagamento DATE NOT NULL,
                mes_referencia TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            # Interações com clientes
            '''
            CREATE TABLE IF NOT EXISTS interacoes_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                tipo_interacao TEXT NOT NULL CHECK (tipo_interacao IN ('pagamento_detectado', 'duvida', 'reclamacao', 'outro')),
                mensagem TEXT NOT NULL,
                resolvido BOOLEAN DEFAULT 0,
                data_interacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            # Templates de mensagem
            '''
            CREATE TABLE IF NOT EXISTS message_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                template_text TEXT NOT NULL,
                variaveis TEXT,
                ativo BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        ]
        
        with self.get_connection() as conn:
            for table_sql in tables:
                conn.execute(table_sql)
            conn.commit()

    # CLIENTES
    def inserir_cliente(self, nome: str, digisac_contact_id: str, telefone: str = None, email: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO clientes (nome, digisac_contact_id, telefone, email)
                VALUES (?, ?, ?, ?)
            ''', (nome, digisac_contact_id, telefone, email))
            return cursor.lastrowid

    def get_cliente_by_contact_id(self, contact_id: str) -> Optional[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes WHERE digisac_contact_id = ?', (contact_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_all_clientes(self) -> List[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes')
            return [Cliente(*row) for row in cursor.fetchall()]

    # CONTAS FIXAS
    def inserir_conta_fixa(self, cliente_id: int, descricao: str, valor: float, dia_vencimento: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_fixas (cliente_id, descricao, valor, dia_vencimento)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, descricao, valor, dia_vencimento))
            return cursor.lastrowid

    def get_contas_ativas_cliente(self, cliente_id: int) -> List[ContaFixa]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_id, descricao, valor, dia_vencimento, ativo 
                FROM contas_fixas WHERE cliente_id = ? AND ativo = 1
            ''', (cliente_id,))
            return [ContaFixa(*row) for row in cursor.fetchall()]

    # CONFIGURAÇÕES DE CONTA
    def get_conta_config(self, conta_id: int) -> Optional[ContaConfig]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cc.id, cc.conta_id, cc.frequencia, cc.prox_data_cobranca, cc.feriados_ajustar
                FROM contas_config cc
                WHERE cc.conta_id = ?
            ''', (conta_id,))
            result = cursor.fetchone()
            return ContaConfig(*result) if result else None

    def update_proxima_cobranca(self, conta_id: int, proxima_data: datetime):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO contas_config 
                (conta_id, prox_data_cobranca) 
                VALUES (?, ?)
            ''', (conta_id, proxima_data.strftime('%Y-%m-%d')))

    def update_conta_config(self, conta_id: int, frequencia: str = None, prox_data_cobranca: datetime = None, feriados_ajustar: bool = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Buscar configuração atual
            current = self.get_conta_config(conta_id)
            if not current:
                cursor.execute('''
                    INSERT INTO contas_config (conta_id, frequencia, prox_data_cobranca, feriados_ajustar)
                    VALUES (?, ?, ?, ?)
                ''', (conta_id, frequencia or 'mensal', prox_data_cobranca, feriados_ajustar or True))
            else:
                cursor.execute('''
                    UPDATE contas_config 
                    SET frequencia = COALESCE(?, frequencia),
                        prox_data_cobranca = COALESCE(?, prox_data_cobranca),
                        feriados_ajustar = COALESCE(?, feriados_ajustar)
                    WHERE conta_id = ?
                ''', (frequencia, prox_data_cobranca, feriados_ajustar, conta_id))

    # COBRANÇAS
    def get_clientes_para_cobrar_hoje(self) -> List[tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            hoje = datetime.now().date()
            
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE (cc.prox_data_cobranca = ? OR 
                      (cc.prox_data_cobranca IS NULL AND cf.dia_vencimento = ?))
                AND cf.ativo = 1
            ''', (hoje, hoje.day))
            
            return cursor.fetchall()

    def registrar_cobranca(self, cliente_id: int, conta_id: int, mensagem: str, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_cobrancas (cliente_id, conta_id, mensagem, status)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, conta_id, mensagem, status))

    # PAGAMENTOS E STATUS
    def registrar_pagamento(self, cliente_id: int, valor: float, data_pagamento: str, mes_referencia: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if not mes_referencia:
                mes_referencia = datetime.now().strftime('%Y-%m')
                
            cursor.execute('''
                INSERT INTO historico_pagamentos (cliente_id, valor, data_pagamento, mes_referencia)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, valor, data_pagamento, mes_referencia))
            
            # Atualizar status do cliente
            cursor.execute('''
                INSERT OR REPLACE INTO cliente_status 
                (cliente_id, status, last_payment_date, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (cliente_id, 'ativo', data_pagamento))

    def get_historico_pagamentos_cliente(self, cliente_id: int) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_pagamento 
                FROM historico_pagamentos 
                WHERE cliente_id = ? 
                ORDER BY data_pagamento DESC 
                LIMIT 1
            ''', (cliente_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_cliente_status(self, cliente_id: int) -> Optional[ClienteStatus]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_id, status, last_payment_date, dias_tolerancia
                FROM cliente_status WHERE cliente_id = ?
            ''', (cliente_id,))
            result = cursor.fetchone()
            return ClienteStatus(*result) if result else None

    def update_cliente_status(self, cliente_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cliente_status 
                (cliente_id, status, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (cliente_id, status))

    # INTERAÇÕES
    def registrar_interacao(self, cliente_id: int, tipo_interacao: str, mensagem: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interacoes_cliente (cliente_id, tipo_interacao, mensagem)
                VALUES (?, ?, ?)
            ''', (cliente_id, tipo_interacao, mensagem))

    # TEMPLATES
    def inserir_template(self, nome: str, template_text: str, variaveis: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO message_templates (nome, template_text, variaveis)
                VALUES (?, ?, ?)
            ''', (nome, template_text, variaveis))
            return cursor.lastrowid

    def get_template_by_name(self, nome: str) -> Optional[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, template_text, variaveis, ativo FROM message_templates WHERE nome = ? AND ativo = 1', (nome,))
            result = cursor.fetchone()
            return MessageTemplate(*result) if result else None

    def get_all_templates(self) -> List[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, template_text, variaveis, ativo FROM message_templates WHERE ativo = 1')
            return [MessageTemplate(*row) for row in cursor.fetchall()]

    # RELATÓRIOS
    def get_clientes_inadimplentes(self, dias_tolerancia: int = 30) -> List[tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.nome, c.digisac_contact_id, cs.last_payment_date,
                       julianday('now') - julianday(cs.last_payment_date) as dias_atraso
                FROM clientes c
                JOIN cliente_status cs ON c.id = cs.cliente_id
                WHERE cs.status = 'inadimplente' 
                OR (cs.last_payment_date IS NULL OR 
                    julianday('now') - julianday(cs.last_payment_date) > ?)
            ''', (dias_tolerancia,))
            return cursor.fetchall()