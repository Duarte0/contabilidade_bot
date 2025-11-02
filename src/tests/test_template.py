import pytest
from services.template_manager import TemplateManager

class TestTemplates:
    
    def test_renderizacao_basica(self, temp_db):
        template_manager = TemplateManager(temp_db)
        
        # Inserir template de teste
        temp_db.inserir_template(
            "teste_basico", 
            "Olá ${nome}, valor: R$ ${valor}"
        )
        
        contexto = {"nome": "João Silva", "valor": 150.75}
        resultado = template_manager.engine.render_template("teste_basico", contexto)
        
        assert "João Silva" in resultado
        assert "150.75" in resultado
        assert "${" not in resultado

    def test_variaveis_padrao(self, temp_db):
        template_manager = TemplateManager(temp_db)
        
        temp_db.inserir_template(
            "teste_data", 
            "Hoje é ${data_hoje} - ${empresa}"
        )
        
        resultado = template_manager.engine.render_template("teste_data", {})
        
        assert "202" in resultado  # Contém ano atual
        assert "Grupo INOV" in resultado
        assert "${" not in resultado

    def test_template_nao_encontrado(self, temp_db):
        template_manager = TemplateManager(temp_db)
        resultado = template_manager.engine.render_template("inexistente", {})
        assert resultado is None