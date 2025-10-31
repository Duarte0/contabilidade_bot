from datetime import datetime

def formatar_mensagem_cobranca(nome, descricao, valor):
    return f"""Olá {nome},

Lembrete de honorários:
Serviço: {descricao}
Valor: R$ {valor:.2f}
Vencimento: {datetime.now().strftime('%d/%m')}

Atenciosamente,
Grupo INOV"""