#!/usr/bin/env python3
"""
Importa contatos do Digisac para o banco de dados local
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.database import DatabaseManager
import core.config as config
import requests


def importar_contatos():
    """Importa todos os contatos do Digisac com paginação"""
    print("=" * 60)
    print("📥 IMPORTANDO CONTATOS DO DIGISAC")
    print("=" * 60)
    print()
    
    # Inicializar serviços
    db = DatabaseManager()
    
    # Configurar requisição
    headers = {
        "Authorization": f"Bearer {config.DIGISAC_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Buscando contatos no Digisac (paginado)...")
    
    try:
        all_contatos = []
        page = 1
        per_page = 200
        
        # Buscar todos os contatos com paginação
        while True:
            print(f"   Página {page}...", end=" ", flush=True)
            
            response = requests.get(
                f"{config.API_BASE_URL}/contacts",
                headers=headers,
                params={"perPage": per_page, "page": page},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Erro: {response.status_code}")
                break
            
            data = response.json()
            contatos = data.get('data', [])
            
            if not contatos:
                print("✅ (fim)")
                break
            
            all_contatos.extend(contatos)
            print(f"✅ (+{len(contatos)})")
            
            # Verificar se tem mais páginas
            if len(contatos) < per_page:
                break
            
            page += 1
        
        if not all_contatos:
            print("⚠️  Nenhum contato encontrado no Digisac!")
            return
        
        print()
        print(f"✅ Total de {len(all_contatos)} contatos encontrados")
        print()
        print("💾 Importando para o banco de dados...")
        print()
        
        # Importar para o banco
        sucesso = 0
        erros = 0
        duplicados = 0
        
        for i, contato in enumerate(all_contatos, 1):
            try:
                nome = contato.get('name', 'Sem Nome')
                contact_id = str(contato.get('id', ''))
                
                # Telefone está em data.number
                telefone = ''
                if contato.get('data') and isinstance(contato['data'], dict):
                    telefone = contato['data'].get('number', '')
                
                if not telefone or not contact_id:
                    erros += 1
                    continue
                
                # Limpar telefone (remover caracteres especiais)
                telefone = ''.join(filter(str.isdigit, telefone))
                
                # Se nome é igual ao telefone, significa que não tem nome real
                # Usar "Cliente [telefone]" ou "Sem Nome"
                if nome.replace('+', '').replace(' ', '').replace('-', '') == telefone:
                    nome = 'Sem Nome'
                
                # Verificar se já existe
                cliente_existente = db.get_cliente_por_telefone(telefone)
                if cliente_existente:
                    duplicados += 1
                    continue
                
                # Inserir no banco
                db.inserir_cliente(
                    nome=nome,
                    digisac_contact_id=contact_id,
                    telefone=telefone,
                    email=None
                )
                
                sucesso += 1
                
                # Mostrar progresso a cada 100 contatos
                if sucesso % 100 == 0:
                    print(f"   Processados: {i}/{len(all_contatos)} | Importados: {sucesso}")
                
            except Exception as e:
                print(f"❌ Erro ao importar {contato.get('name', '?')}: {e}")
                erros += 1
        
        print()
        print("=" * 60)
        print(f"✅ Importados: {sucesso}")
        print(f"⏭️  Duplicados: {duplicados}")
        print(f"❌ Erros: {erros}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao buscar contatos do Digisac: {e}")
        return


if __name__ == '__main__':
    try:
        importar_contatos()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
