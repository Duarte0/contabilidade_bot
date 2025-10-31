import sqlite3
from datetime import datetime

from models.models import Cliente, ClienteStatus, ContaConfig

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    digisac_contact_id TEXT UNIQUE,
                    telefone TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contas_fixas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    dia_vencimento INTEGER NOT NULL,
                    ativo BOOLEAN DEFAULT 1,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historico_cobrancas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    conta_id INTEGER,
                    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    mensagem TEXT,
                    status TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                    FOREIGN KEY (conta_id) REFERENCES contas_fixas (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cliente_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER UNIQUE,
                    status TEXT DEFAULT 'ativo',
                    last_payment_date DATE,
                    payment_preferences TEXT,
                    dias_tolerancia INTEGER DEFAULT 0,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS historico_pagamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    valor REAL NOT NULL,
                    data_pagamento DATE NOT NULL,
                    mes_referencia TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interacoes_cliente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    tipo_interacao TEXT,
                    mensagem TEXT,
                    resolvido BOOLEAN DEFAULT 0,
                    data_interacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    template_text TEXT NOT NULL,
                    variaveis TEXT,
                    ativo BOOLEAN DEFAULT 1
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contas_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conta_id INTEGER UNIQUE,
                    frequencia TEXT DEFAULT 'mensal',
                    dia_vencimento INTEGER,
                    prox_data_cobranca DATE,
                    feriados_ajustar BOOLEAN DEFAULT 1,
                    FOREIGN KEY (conta_id) REFERENCES contas_fixas (id)
                )
            ''')

    def get_clientes_para_cobrar_hoje(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            hoje = datetime.now().day
            
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                WHERE cf.dia_vencimento = ? AND cf.ativo = 1
            ''', (hoje,))
            
            return cursor.fetchall()

    def inserir_cliente(self, nome, digisac_contact_id, telefone=None, email=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO clientes (nome, digisac_contact_id, telefone, email)
                VALUES (?, ?, ?, ?)
            ''', (nome, digisac_contact_id, telefone, email))
            return cursor.lastrowid

    def inserir_conta_fixa(self, cliente_id, descricao, valor, dia_vencimento):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_fixas (cliente_id, descricao, valor, dia_vencimento)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, descricao, valor, dia_vencimento))
            return cursor.lastrowid

    def registrar_cobranca(self, cliente_id, conta_id, mensagem, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_cobrancas (cliente_id, conta_id, mensagem, status)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, conta_id, mensagem, status))
            
    def inserir_template(self, nome, template_text, variaveis=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_templates (nome, template_text, variaveis)
                VALUES (?, ?, ?)
            ''', (nome, template_text, variaveis))
            return cursor.lastrowid

    def get_template_by_name(self, nome):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM message_templates WHERE nome = ? AND ativo = 1', (nome,))
            result = cursor.fetchone()
            return result if result else None

    def get_all_templates(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM message_templates WHERE ativo = 1')
            return cursor.fetchall()

    def update_template(self, template_id, nome, template_text, variaveis):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE message_templates 
                SET nome = ?, template_text = ?, variaveis = ?
                WHERE id = ?
            ''', (nome, template_text, variaveis, template_id))
            
    def get_cliente_status(self, cliente_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cliente_status WHERE cliente_id = ?', (cliente_id,))
            result = cursor.fetchone()
            return ClienteStatus(*result) if result else None

    def registrar_pagamento(self, cliente_id, valor, data_pagamento, mes_referencia=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Inserir pagamento
            cursor.execute('''
                INSERT INTO historico_pagamentos 
                (cliente_id, valor, data_pagamento, mes_referencia)
                VALUES (?, ?, ?, ?)
            ''', (cliente_id, valor, data_pagamento, mes_referencia))
            
            # Atualizar status na mesma transação
            cursor.execute('''
                INSERT OR REPLACE INTO cliente_status 
                (cliente_id, status, last_payment_date) 
                VALUES (?, ?, ?)
            ''', (cliente_id, 'ativo', data_pagamento))

    def get_clientes_inadimplentes(self, dias_tolerancia=5):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.nome, c.digisac_contact_id, cs.last_payment_date
                FROM clientes c
                JOIN cliente_status cs ON c.id = cs.cliente_id
                WHERE cs.status = 'inadimplente' 
                OR (cs.last_payment_date IS NULL OR 
                    julianday('now') - julianday(cs.last_payment_date) > ?)
            ''', (dias_tolerancia,))
            return cursor.fetchall()
        
    def get_cliente_by_contact_id(self, contact_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id 
                FROM clientes WHERE digisac_contact_id = ?
            ''', (contact_id,))
            result = cursor.fetchone()
            
            if result:
                return Cliente(
                    id=result[0],
                    nome=result[1],
                    digisac_contact_id=result[2]
                )
            return None

    def registrar_interacao(self, cliente_id, tipo_interacao, mensagem):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interacoes_cliente 
                (cliente_id, tipo_interacao, mensagem) 
                VALUES (?, ?, ?)
            ''', (cliente_id, tipo_interacao, mensagem))
            
    def get_conta_config(self, conta_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM contas_config WHERE conta_id = ?', (conta_id,))
            result = cursor.fetchone()
            return ContaConfig(*result) if result else None

    def update_proxima_cobranca(self, conta_id, proxima_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO contas_config 
                (conta_id, prox_data_cobranca) 
                VALUES (?, ?)
            ''', (conta_id, proxima_data.strftime('%Y-%m-%d')))