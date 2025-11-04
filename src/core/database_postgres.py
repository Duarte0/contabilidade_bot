import psycopg2
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple, Any
from datetime import datetime
from models.models import Cliente, ClienteStatus, ContaConfig, ContaFixa, MessageTemplate

class PostgreSQLManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Erro na conexão PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        tables = [
            '''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                digisac_contact_id TEXT UNIQUE NOT NULL,
                telefone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS contas_fixas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                valor DECIMAL(10,2) NOT NULL,
                dia_vencimento INTEGER NOT NULL CHECK (dia_vencimento BETWEEN 1 AND 31),
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS contas_config (
                id SERIAL PRIMARY KEY,
                conta_id INTEGER UNIQUE NOT NULL,
                frequencia TEXT DEFAULT 'mensal' CHECK (frequencia IN ('diaria', 'semanal', 'quinzenal', 'mensal', 'bimestral')),
                prox_data_cobranca DATE,
                feriados_ajustar BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conta_id) REFERENCES contas_fixas (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS historico_cobrancas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                conta_id INTEGER NOT NULL,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mensagem TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('enviado', 'erro', 'pendente')),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE,
                FOREIGN KEY (conta_id) REFERENCES contas_fixas (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS cliente_status (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER UNIQUE NOT NULL,
                status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inadimplente', 'suspenso', 'cancelado')),
                last_payment_date DATE,
                dias_tolerancia INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS historico_pagamentos (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                valor DECIMAL(10,2) NOT NULL CHECK (valor > 0),
                data_pagamento DATE NOT NULL,
                mes_referencia TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS interacoes_cliente (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                tipo_interacao TEXT NOT NULL CHECK (tipo_interacao IN (
                    'pagamento_detectado', 'duvida', 'reclamacao', 'outro',
                    'confirmacao', 'urgencia_contato', 'parcelamento', 'duvida_generica',
                    'duvida_valor', 'duvida_data'
                )),
                mensagem TEXT NOT NULL,
                resolvido BOOLEAN DEFAULT false,
                data_interacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS message_templates (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE NOT NULL,
                template_text TEXT NOT NULL,
                variaveis TEXT,
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table_sql in tables:
                try:
                    cursor.execute(table_sql)
                except Exception as e:
                    self.logger.warning(f"Tabela possivelmente já existe: {e}")

    def inserir_cliente(self, nome: str, digisac_contact_id: str, telefone: str = None, email: str = None) -> int:
      with self.get_connection() as conn:
          cursor = conn.cursor()
          cursor.execute('''
              INSERT INTO clientes (nome, digisac_contact_id, telefone, email)
              VALUES (%s, %s, %s, %s)
              ON CONFLICT (digisac_contact_id) DO NOTHING
              RETURNING id
          ''', (nome, digisac_contact_id, telefone, email))
          result = cursor.fetchone()
          
          if not result:
              cursor.execute('SELECT id FROM clientes WHERE digisac_contact_id = %s', (digisac_contact_id,))
              result = cursor.fetchone()
          
          return result[0] if result else None

    def get_cliente_by_contact_id(self, contact_id: str) -> Optional[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes WHERE digisac_contact_id = %s', (contact_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_all_clientes(self) -> List[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes')
            return [Cliente(*row) for row in cursor.fetchall()]

    def inserir_conta_fixa(self, cliente_id: int, descricao: str, valor: float, dia_vencimento: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_fixas (cliente_id, descricao, valor, dia_vencimento)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (cliente_id, descricao, valor, dia_vencimento))
            return cursor.fetchone()[0]

    def get_contas_fixas_cliente(self, cliente_id: int) -> List[ContaFixa]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_id, descricao, valor, dia_vencimento, ativo 
                FROM contas_fixas WHERE cliente_id = %s AND ativo = true
            ''', (cliente_id,))
            return [ContaFixa(*row) for row in cursor.fetchall()]

    def get_conta_config(self, conta_id: int) -> Optional[ContaConfig]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cc.id, cc.conta_id, cc.frequencia, cc.prox_data_cobranca, cc.feriados_ajustar
                FROM contas_config cc
                WHERE cc.conta_id = %s
            ''', (conta_id,))
            result = cursor.fetchone()
            return ContaConfig(*result) if result else None

    def update_proxima_cobranca(self, conta_id: int, proxima_data: datetime):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_config (conta_id, prox_data_cobranca) 
                VALUES (%s, %s)
                ON CONFLICT (conta_id) 
                DO UPDATE SET prox_data_cobranca = EXCLUDED.prox_data_cobranca
            ''', (conta_id, proxima_data.strftime('%Y-%m-%d')))

    def update_conta_config(self, conta_id: int, frequencia: str = None, prox_data_cobranca: datetime = None, feriados_ajustar: bool = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            current = self.get_conta_config(conta_id)
            if not current:
                cursor.execute('''
                    INSERT INTO contas_config (conta_id, frequencia, prox_data_cobranca, feriados_ajustar)
                    VALUES (%s, %s, %s, %s)
                ''', (conta_id, frequencia or 'mensal', 
                      prox_data_cobranca.strftime('%Y-%m-%d') if prox_data_cobranca else None, 
                      feriados_ajustar or True))
            else:
                update_fields = []
                update_data = []
                
                if frequencia is not None:
                    update_fields.append("frequencia = %s")
                    update_data.append(frequencia)
                
                if prox_data_cobranca is not None:
                    update_fields.append("prox_data_cobranca = %s")
                    update_data.append(prox_data_cobranca.strftime('%Y-%m-%d'))
                
                if feriados_ajustar is not None:
                    update_fields.append("feriados_ajustar = %s")
                    update_data.append(feriados_ajustar)
                
                if update_fields:
                    update_data.append(conta_id)
                    cursor.execute(f'''
                        UPDATE contas_config 
                        SET {', '.join(update_fields)}
                        WHERE conta_id = %s
                    ''', update_data)

    def get_clientes_para_cobrar_hoje(self) -> List[Tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            hoje = datetime.now().date()
            
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE (cc.prox_data_cobranca = %s OR 
                      (cc.prox_data_cobranca IS NULL AND cf.dia_vencimento = %s))
                AND cf.ativo = true
            ''', (hoje, hoje.day))
            
            return cursor.fetchall()

    def registrar_cobranca(self, cliente_id: int, conta_id: int, mensagem: str, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_cobrancas (cliente_id, conta_id, mensagem, status)
                VALUES (%s, %s, %s, %s)
            ''', (cliente_id, conta_id, mensagem, status))

    def registrar_pagamento(self, cliente_id: int, valor: float, data_pagamento: str, mes_referencia: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if not mes_referencia:
                mes_referencia = datetime.now().strftime('%Y-%m')
                
            cursor.execute('''
                INSERT INTO historico_pagamentos (cliente_id, valor, data_pagamento, mes_referencia)
                VALUES (%s, %s, %s, %s)
            ''', (cliente_id, valor, data_pagamento, mes_referencia))
            
            cursor.execute('''
                INSERT INTO cliente_status (cliente_id, status, last_payment_date, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cliente_id) 
                DO UPDATE SET status = EXCLUDED.status, 
                            last_payment_date = EXCLUDED.last_payment_date,
                            updated_at = EXCLUDED.updated_at
            ''', (cliente_id, 'ativo', data_pagamento))

    def get_ultimo_pagamento_cliente(self, cliente_id: int) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_pagamento 
                FROM historico_pagamentos 
                WHERE cliente_id = %s 
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
                FROM cliente_status WHERE cliente_id = %s
            ''', (cliente_id,))
            result = cursor.fetchone()
            return ClienteStatus(*result) if result else None

    def update_cliente_status(self, cliente_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cliente_status (cliente_id, status, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cliente_id) 
                DO UPDATE SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
            ''', (cliente_id, status))

    def registrar_interacao(self, cliente_id: int, tipo_interacao: str, mensagem: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interacoes_cliente (cliente_id, tipo_interacao, mensagem)
                VALUES (%s, %s, %s)
            ''', (cliente_id, tipo_interacao, mensagem))

    def inserir_template(self, nome: str, template_text: str, variaveis: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_templates (nome, template_text, variaveis)
                VALUES (%s, %s, %s)
                ON CONFLICT (nome) 
                DO UPDATE SET template_text = EXCLUDED.template_text, 
                            variaveis = EXCLUDED.variaveis,
                            ativo = true
                RETURNING id
            ''', (nome, template_text, variaveis))
            return cursor.fetchone()[0]

    def get_template_by_name(self, nome: str) -> Optional[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, template_text, variaveis, ativo FROM message_templates WHERE nome = %s AND ativo = true', (nome,))
            result = cursor.fetchone()
            return MessageTemplate(*result) if result else None

    def get_all_templates(self) -> List[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, template_text, variaveis, ativo FROM message_templates WHERE ativo = true')
            return [MessageTemplate(*row) for row in cursor.fetchall()]

    def get_clientes_inadimplentes(self, dias_tolerancia: int = 30) -> List[Tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.nome, c.digisac_contact_id, cs.last_payment_date,
                       EXTRACT(DAY FROM (CURRENT_DATE - cs.last_payment_date)) as dias_atraso
                FROM clientes c
                JOIN cliente_status cs ON c.id = cs.cliente_id
                WHERE cs.status = 'inadimplente' 
                OR (cs.last_payment_date IS NULL OR 
                    CURRENT_DATE - cs.last_payment_date > %s)
            ''', (dias_tolerancia,))
            return cursor.fetchall()
        
    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes WHERE id = %s', (cliente_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None