import re
from datetime import datetime

class TemplateEngine:
    def __init__(self, db):
      self.db = db
      self.default_variables = {
          'data_hoje': datetime.now().strftime('%d/%m/%Y'),
          'dia_semana': self._get_dia_semana(),
          'mes_ano': datetime.now().strftime('%B/%Y'),
          'empresa': 'Grupo INOV'  # NOVA VARIÁVEL
      }

    def _get_dia_semana(self):
        dias = {
            0: 'segunda-feira',
            1: 'terça-feira', 
            2: 'quarta-feira',
            3: 'quinta-feira',
            4: 'sexta-feira',
            5: 'sábado',
            6: 'domingo'
        }
        return dias[datetime.now().weekday()]

    def render_template(self, template_name, context=None):
        template_data = self.db.get_template_by_name(template_name)
        if not template_data:
            return None
        
        template_id, nome, template_text, variaveis, ativo = template_data
        
        # Combinar variáveis padrão com contexto fornecido
        full_context = self.default_variables.copy()
        if context:
            full_context.update(context)
        
        # Renderizar template
        rendered_text = template_text
        for key, value in full_context.items():
            placeholder = f'${{{key}}}'
            rendered_text = rendered_text.replace(placeholder, str(value))
        
        return rendered_text

    def get_available_variables(self):
        return list(self.default_variables.keys())

    def validate_template(self, template_text):
        """Valida se todas as variáveis no template existem"""
        variables_in_template = re.findall(r'\$\{(\w+)\}', template_text)
        available_vars = self.get_available_variables()
        
        missing_vars = [var for var in variables_in_template if var not in available_vars]
        return len(missing_vars) == 0, missing_vars