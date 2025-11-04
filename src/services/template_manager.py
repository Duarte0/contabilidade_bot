from .template_engine import TemplateEngine
from typing import Dict, Any, List

class TemplateManager:
    def __init__(self, db):
        self.db = db
        self.engine = TemplateEngine(db)

    def criar_template(self, nome: str, template_text: str) -> int:
        is_valid, missing_vars = self.engine.validate_template(template_text)
        if not is_valid:
            raise ValueError(f"Variáveis não encontradas: {missing_vars}")
        return self.db.inserir_template(nome, template_text)

    def listar_templates(self) -> List:
        return self.db.get_all_templates()

    def aplicar_template_cliente(self, template_name: str, cliente_id: int, conta_id: int) -> str:
        context = self._build_context(cliente_id, conta_id)
        mensagem = self.engine.render_template(template_name, context)
        
        if not mensagem:
            raise ValueError(f"Template '{template_name}' não encontrado ou inválido")
        
        return mensagem

    def _build_context(self, cliente_id: int, conta_id: int) -> Dict[str, Any]:
        cliente_data = self._get_cliente_data(cliente_id)
        conta_data = self._get_conta_data(conta_id)
        
        return {
            'nome': cliente_data.get('nome', ''),
            'descricao': conta_data.get('descricao', ''),
            'valor': conta_data.get('valor', 0),
            'vencimento': conta_data.get('dia_vencimento', '')
        }

    def _get_cliente_data(self, cliente_id: int) -> Dict[str, str]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM clientes WHERE id = %s', (cliente_id,))
            result = cursor.fetchone()
            return {'nome': result[0]} if result else {}

    def _get_conta_data(self, conta_id: int) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT descricao, valor, dia_vencimento FROM contas_fixas WHERE id = %s', (conta_id,))
            result = cursor.fetchone()
            return {
                'descricao': result[0],
                'valor': float(result[1]),
                'dia_vencimento': result[2]
            } if result else {}