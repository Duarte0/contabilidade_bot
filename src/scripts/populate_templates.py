import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager
from core.config import DATABASE_PATH

def popular_templates_iniciais():
    db = DatabaseManager(DATABASE_PATH)
    
    templates = [
        {
            'nome': 'cobranca_padrao',
            'texto': '''Olá ${nome},

Lembrete de honorários:
Serviço: ${descricao}
Valor: R$ ${valor}
Vencimento: ${data_hoje}

Atenciosamente,
Grupo INOV'''
        },
        {
            'nome': 'cobranca_antecipada', 
            'texto': '''Olá ${nome},

Aviso antecipado de honorários:
Serviço: ${descricao}
Valor: R$ ${valor} 
Vencimento: ${data_hoje}

Pagamento antecipado tem 5% de desconto!
Grupo INOV'''
        },
        {
            'nome': 'cobranca_inadimplente',
            'texto': '''Olá ${nome},

URGENTE - Honorários em atraso:
Serviço: ${descrica0}
Valor: R$ ${valor}
Vencimento: ${data_hoje}

Regularize sua situação para evitar bloqueio.
Grupo INOV'''
        },
        {
            'nome': 'cobranca_reenvio',
            'texto': '''Olá ${nome},

Reenvio - Honorários pendentes:
Serviço: ${descricao} 
Valor: R$ ${valor}
Vencimento: ${data_hoje}

Caso já tenha pago, desconsidere esta mensagem.
Grupo INOV'''
        }
    ]
    
    for template in templates:
        db.inserir_template(template['nome'], template['texto'])
    
    print("Templates INOV criados com sucesso!")

if __name__ == "__main__":
    popular_templates_iniciais()