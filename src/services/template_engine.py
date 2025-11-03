import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class TemplateEngine:
    def __init__(self, db):
        self.db = db
        self.default_variables = self._init_default_variables()
    
    def _init_default_variables(self) -> Dict[str, str]:
        return {
            'data_hoje': datetime.now().strftime('%d/%m/%Y'),
            'dia_semana': self._get_dia_semana(),
            'mes_ano': datetime.now().strftime('%B/%Y'),
            'empresa': 'Grupo INOV'
        }
    
    def _get_dia_semana(self) -> str:
        dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 
                'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        return dias[datetime.now().weekday()]
    
    def render_template(self, template_name: str, context: Dict = None) -> Optional[str]:
        template_data = self.db.get_template_by_name(template_name)
        if not template_data:
            return None
        
        template_text = template_data.template_text
        
        full_context = {**self.default_variables, **(context or {})}
        
        return self._render_text(template_text, full_context)
    
    def _render_text(self, text: str, context: Dict) -> str:
        rendered = text
        for key, value in context.items():
            rendered = rendered.replace(f'${{{key}}}', str(value))
        return rendered
    
    def get_available_variables(self) -> List[str]:
        return list(self.default_variables.keys())
    
    def validate_template(self, template_text: str) -> Tuple[bool, List[str]]:
        variables_in_template = re.findall(r'\$\{(\w+)\}', template_text)
        available_vars = set(self.get_available_variables())
        
        missing_vars = [var for var in variables_in_template if var not in available_vars]
        return len(missing_vars) == 0, missing_vars