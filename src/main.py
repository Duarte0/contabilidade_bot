# main.py
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager 
from services.digisac_service import DigisacAPI
from services.template_manager import TemplateManager
from services.agendamento_manager import AgendamentoManager
from services.cliente_status_manager import ClienteStatusManager

def main():
    try:
        
        db = DatabaseManager()
        agendamento_manager = AgendamentoManager(db)
        template_manager = TemplateManager(db)
        status_manager = ClienteStatusManager(db)
        digisac = DigisacAPI()
        
        if not db.health_check():
            logger.error("Falha na conexão com o banco de dados")
            return
        
        agendamento_manager.inicializar_proximas_cobrancas()
        
        clientes_para_cobrar = agendamento_manager.get_clientes_para_cobrar_hoje()
        
        
        if not clientes_para_cobrar:
            logger.info("Nenhum cliente para cobrar hoje")
            return
        
        for cliente_id, contact_id, nome, descricao, valor, conta_id in clientes_para_cobrar:
            
            try:
                template_name = status_manager.get_template_por_status(cliente_id)
                
                mensagem = template_manager.aplicar_template_cliente(
                    template_name, 
                    cliente_id, 
                    conta_id
                )
                
                if not mensagem:
                    logger.error(f"Template '{template_name}' não encontrado para {nome}")
                    db.registrar_cobranca(
                        cliente_id=cliente_id,
                        conta_id=conta_id,
                        mensagem=f"Template {template_name} não encontrado",
                        status="erro",
                        erro_detalhe="Template não encontrado"
                    )
                    continue
                
                sucesso = digisac.enviar_mensagem(contact_id, mensagem)
                status = "enviado" if sucesso else "erro"
                
                db.registrar_cobranca(
                    cliente_id=cliente_id,
                    conta_id=conta_id,
                    mensagem=mensagem,
                    status=status,
                    tentativas=1,
                    erro_detalhe=None if sucesso else "Falha no envio via API"
                )
                
                if sucesso:
                    agendamento_manager.atualizar_proxima_cobranca(conta_id)
                else:
                    logger.error(f"Falha no envio da cobrança: {nome}")
                
                logger.info(f"Template usado: {template_name}, Status: {status}")
                
            except Exception as e:
                logger.error(f"Erro ao processar cliente {nome}: {str(e)}")
                db.registrar_cobranca(
                    cliente_id=cliente_id,
                    conta_id=conta_id,
                    mensagem=f"Erro no processamento: {str(e)}",
                    status="erro",
                    erro_detalhe=str(e)
                )
        
        
    except Exception as e:
        logger.error(f"Erro fatal no sistema: {str(e)}")
        raise

if __name__ == "__main__":
    main()