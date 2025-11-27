#!/usr/bin/env python3
"""
Importa contatos do Digisac para o banco de dados local
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.database import DatabaseManager
import core.config as config
import requests


def importar_contatos():
    """Importa todos os contatos do Digisac com paginação"""
    print("IMPORTANDO CONTATOS DO DIGISAC")
    print()
    
    db = DatabaseManager()
    
    headers = {
        "Authorization": f"Bearer {config.DIGISAC_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("[INFO] Buscando contatos no Digisac (paginado)...")
    
    try:
        all_contatos = []
        page = 1
        per_page = 200
        
        while True:
            print(f"   Página {page}...", end=" ", flush=True)
            
            response = requests.get(
                f"{config.API_BASE_URL}/contacts",
                headers=headers,
                params={"perPage": per_page, "page": page},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Status: {response.status_code}")
                break
            
            data = response.json()
            contatos = data.get('data', [])
            
            if not contatos:
                print("OK (fim)")
                break
            
            all_contatos.extend(contatos)
            print(f"OK (+{len(contatos)})")
            
            if len(contatos) < per_page:
                break
            
            page += 1
        
        if not all_contatos:
            print("[WARNING] Nenhum contato encontrado no Digisac!")
            return
        
        print()
        print(f"[SUCCESS] Total de {len(all_contatos)} contatos encontrados")
        print()
        print("[INFO] Importando para o banco de dados...")
        print()
        
        sucesso = 0
        erros = 0
        duplicados = 0
        
        for i, contato in enumerate(all_contatos, 1):
            try:
                nome = contato.get('name', 'Sem Nome')
                contact_id = str(contato.get('id', ''))
                
                telefone = ''
                if contato.get('data') and isinstance(contato['data'], dict):
                    telefone = contato['data'].get('number', '')
                
                if not telefone or not contact_id:
                    erros += 1
                    continue
                
                telefone = ''.join(filter(str.isdigit, telefone))
                
                if nome.replace('+', '').replace(' ', '').replace('-', '') == telefone:
                    nome = 'Sem Nome'
                
                cliente_existente = db.get_cliente_por_telefone(telefone)
                if cliente_existente:
                    duplicados += 1
                    continue
                
                db.inserir_cliente(
                    nome=nome,
                    digisac_contact_id=contact_id,
                    telefone=telefone,
                    email=None
                )
                
                sucesso += 1
                
                if sucesso % 100 == 0:
                    print(f"   Processados: {i}/{len(all_contatos)} | Importados: {sucesso}")
                
            except Exception as e:
                print(f"[ERROR] Erro ao importar {contato.get('name', '?')}: {e}")
                erros += 1
        
        print()
        print("=" * 60)
        print(f"[SUCCESS] Importados: {sucesso}")
        print(f"[INFO] Duplicados: {duplicados}")
        print(f"[ERROR] Erros: {erros}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Erro ao buscar contatos do Digisac: {e}")
        return


if __name__ == '__main__':
    try:
        importar_contatos()
    except KeyboardInterrupt:
        print("\n\n[INFO] Interrompido pelo usuário.")
    except Exception as e:
        print(f"\n[ERROR] Erro: {e}")
        sys.exit(1)
