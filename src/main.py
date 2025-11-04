import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager 
from services.digisac_service import DigisacAPI
from services.template_manager import TemplateManager
from services.agendamento_manager import AgendamentoManager
from services.cliente_status_manager import ClienteStatusManager

def main():
    db = DatabaseManager(use_postgres=True) 
    agendamento_manager = AgendamentoManager(db)
    template_manager = TemplateManager(db)
    status_manager = ClienteStatusManager(db)
    digisac = DigisacAPI()
    
    agendamento_manager.inicializar_proximas_cobrancas()
    
    clientes_para_cobrar = agendamento_manager.get_clientes_para_cobrar_hoje()
    
    print(f"Clientes para cobrar hoje: {len(clientes_para_cobrar)}")
    
    for cliente_id, contact_id, nome, descricao, valor, conta_id in clientes_para_cobrar:
        print(f"Processando cobrança para: {nome}")
        
        template_name = status_manager.get_template_por_status(cliente_id)
        
        mensagem = template_manager.aplicar_template_cliente(
            template_name, 
            cliente_id, 
            conta_id
        )
        
        if not mensagem:
            print(f" Erro: Template '{template_name}' não encontrado para {nome}")
            continue
        
        sucesso = digisac.enviar_mensagem(contact_id, mensagem)
        status = "enviado" if sucesso else "erro"
        
        db.registrar_cobranca(cliente_id, conta_id, mensagem, status)
        
        if sucesso:
            agendamento_manager.atualizar_proxima_cobranca(conta_id)
            print(f" Cobrança enviada: {nome}")
        else:
            print(f" Falha no envio: {nome}")
        
        print(f"Template usado: {template_name}")
        print(f"Status: {status}\n")

if __name__ == "__main__":
    main()