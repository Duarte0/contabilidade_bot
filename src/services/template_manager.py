from .template_engine import TemplateEngine

class TemplateManager:
    def __init__(self, db):
        self.db = db
        self.engine = TemplateEngine(db)

    def criar_template(self, nome, template_text):
        # Validar template antes de salvar
        is_valid, missing_vars = self.engine.validate_template(template_text)
        if not is_valid:
            raise ValueError(f"Variáveis não encontradas: {missing_vars}")
        
        return self.db.inserir_template(nome, template_text)

    def listar_templates(self):
        return self.db.get_all_templates()

    def aplicar_template_cliente(self, template_name, cliente_id, conta_id):
        # Buscar dados do cliente e conta
        cliente_data = self._get_cliente_data(cliente_id)
        conta_data = self._get_conta_data(conta_id)
        
        context = {
            'nome': cliente_data['nome'],
            'descricao': conta_data['descricao'],
            'valor': conta_data['valor'],
            'vencimento': conta_data['dia_vencimento']
        }
        
        return self.engine.render_template(template_name, context)

    def _get_cliente_data(self, cliente_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM clientes WHERE id = ?', (cliente_id,))
            result = cursor.fetchone()
            return {'nome': result[0]} if result else {}

    def _get_conta_data(self, conta_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT descricao, valor, dia_vencimento FROM contas_fixas WHERE id = ?', (conta_id,))
            result = cursor.fetchone()
            return {
                'descricao': result[0],
                'valor': result[1],
                'dia_vencimento': result[2]
            } if result else {}