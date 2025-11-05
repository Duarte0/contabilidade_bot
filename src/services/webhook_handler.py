import os
import sys
from datetime import datetime
import hashlib
import hmac
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify

SRC_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, SRC_DIR)

from core.database import DatabaseManager
from core.config import WEBHOOK_SECRET
from services.digisac_service import DigisacAPI
from services.template_engine import TemplateEngine

app = Flask(__name__)
db = DatabaseManager() 
digisac = DigisacAPI()
template_engine = TemplateEngine(db)

_cliente_cache: Dict[str, Any] = {}

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET or not signature:
        return True
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def _get_cliente_cached(contact_id: str) -> Optional[Any]:
    if contact_id in _cliente_cache:
        return _cliente_cache[contact_id]
    
    cliente = db.get_cliente_by_contact_id(contact_id)
    if cliente:
        _cliente_cache[contact_id] = cliente
    return cliente

def _analisar_intencao_mensagem(text: str) -> str:
    text = text.lower().strip()
    
    opcoes_map = {
        'ok': 'confirmacao',
        'paguei': 'pagamento_confirmado',
        'valor': 'duvida_valor', 
        'vencto': 'duvida_data',
        'vencimento': 'duvida_data',
        'falar': 'urgencia_contato',
        'parcelar': 'parcelamento',
        'duvida': 'duvida_generica'
    }
    
    for opcao, intencao in opcoes_map.items():
        if opcao in text:
            return intencao
    
    return 'indefinido'

def _get_valor_conta_cliente(cliente_id: int) -> Optional[float]:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT valor FROM contas_fixas WHERE cliente_id = %s AND ativo = true LIMIT 1', (cliente_id,))
        result = cursor.fetchone()
        return float(result[0]) if result else None

def _calcular_proximo_vencimento(dia_vencimento: int) -> str:
    hoje = datetime.now()
    
    try:
        vencimento = hoje.replace(day=dia_vencimento)
        if vencimento.date() > hoje.date():
            return vencimento.strftime('%d/%m/%Y')
    except ValueError:
        pass
    
    if hoje.month == 12:
        proximo = hoje.replace(year=hoje.year + 1, month=1, day=1)
    else:
        proximo = hoje.replace(month=hoje.month + 1, day=1)
    
    from calendar import monthrange
    _, ultimo_dia = monthrange(proximo.year, proximo.month)
    dia_final = min(dia_vencimento, ultimo_dia)
    
    return proximo.replace(day=dia_final).strftime('%d/%m/%Y')

def _registrar_pagamento_detectado(cliente_id: int, mensagem: str):
    if valor := _get_valor_conta_cliente(cliente_id):
        db.registrar_pagamento(
            cliente_id=cliente_id,
            valor=valor,
            data_pagamento=datetime.now().strftime('%Y-%m-%d'),
            mes_referencia=datetime.now().strftime('%Y-%m')
        )
        
        db.registrar_interacao(cliente_id, 'pagamento_detectado', mensagem)

def _registrar_interacao_cliente(cliente_id: int, tipo: str, mensagem: str):
    db.registrar_interacao(cliente_id, tipo, mensagem)

def _enviar_confirmacao_pagamento(cliente_id: int):
    cliente = db.get_cliente_by_id(cliente_id)
    contas = db.get_contas_fixas_cliente(cliente_id)
    
    if not cliente or not contas:
        return
        
    conta = contas[0]
    proximo_vencimento = _calcular_proximo_vencimento(conta.dia_vencimento)
    
    mensagem = template_engine.render_template('confirmacao_pagamento', {
        'nome': cliente.nome,
        'valor': conta.valor,
        'proximo_vencimento': proximo_vencimento
    })
    
    if mensagem:
        digisac.enviar_mensagem(cliente.digisac_contact_id, mensagem)

def _enviar_resposta_valor(cliente_id: int):
    cliente = db.get_cliente_by_id(cliente_id)
    contas = db.get_contas_fixas_cliente(cliente_id)
    
    if not cliente or not contas:
        return
        
    conta = contas[0]
    mensagem = template_engine.render_template('resposta_valor', {
        'nome': cliente.nome,
        'descricao': conta.descricao,
        'valor': conta.valor,
        'data_hoje': datetime.now().strftime('%d/%m/%Y')
    })
    
    if mensagem:
        digisac.enviar_mensagem(cliente.digisac_contact_id, mensagem)

def _enviar_resposta_vencimento(cliente_id: int):
    cliente = db.get_cliente_by_id(cliente_id)
    contas = db.get_contas_fixas_cliente(cliente_id)
    
    if not cliente or not contas:
        return
        
    conta = contas[0]
    proximo_vencimento = _calcular_proximo_vencimento(conta.dia_vencimento)
    
    mensagem = template_engine.render_template('resposta_vencimento', {
        'nome': cliente.nome,
        'proximo_vencimento': proximo_vencimento,
        'dia_vencimento': conta.dia_vencimento
    })
    
    if mensagem:
        digisac.enviar_mensagem(cliente.digisac_contact_id, mensagem)

def _enviar_escalation_humano(cliente_id: int, tipo: str):
    cliente = db.get_cliente_by_id(cliente_id)
    if cliente:
        print(f"ESCALATION: {cliente.nome} precisa de follow-up - {tipo}")

@app.route('/webhook/digisac', methods=['POST'])
def handle_digisac_webhook():
    signature = request.headers.get('X-Digisac-Signature')
    
    if not verify_webhook_signature(request.get_data(), signature):
        return jsonify({'error': 'Assinatura inválida'}), 401
    
    data = request.json
    event_type = data.get('event')
    
    if event_type in ['message.received', 'message.created']:  
        _process_message_received(data.get('data', {}))
    
    return jsonify({'status': 'processed'})

def _process_message_received(message: Dict[str, Any]):
    contact_id = message.get('contactId')
    text = message.get('text', '').strip()
    is_from_me = message.get('isFromMe', False)
    is_from_bot = message.get('isFromBot', False)
    
    if not contact_id or not text:
        return
    
    if is_from_me or is_from_bot:
        print("DEBUG - Mensagem do próprio bot, ignorando")
        return
    
    cliente = _get_cliente_cached(contact_id)
    if not cliente:
        return
    
    intencao = _analisar_intencao_mensagem(text)
    print(f"DEBUG - Intenção: {intencao} - Mensagem: {text}")
    
    if intencao == 'pagamento_confirmado':
        _registrar_pagamento_detectado(cliente.id, text)
        _enviar_confirmacao_pagamento(cliente.id)
        db.registrar_interacao(cliente.id, 'confirmacao', text)
    elif intencao == 'confirmacao':
        _registrar_interacao_cliente(cliente.id, 'confirmacao', text)
    elif intencao == 'duvida_valor':
        _enviar_resposta_valor(cliente.id)
    elif intencao == 'duvida_data':
        _enviar_resposta_vencimento(cliente.id)
    elif intencao in ['urgencia_contato', 'parcelamento', 'duvida_generica']:
        _registrar_interacao_cliente(cliente.id, intencao, text)
        _enviar_escalation_humano(cliente.id, intencao)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)