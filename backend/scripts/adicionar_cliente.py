#!/usr/bin/env python3
"""
Script para adicionar clientes no sistema
Uso: python scripts/adicionar_cliente.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database import DatabaseManager


def adicionar_cliente_interativo():
    """Adiciona cliente de forma interativa"""
    print(" ADICIONAR NOVO CLIENTE")
    print()
    
    nome = input("Nome do cliente: ").strip()
    if not nome:
        print(" Nome é obrigatório!")
        return False
    
    telefone = input("Telefone (apenas números, ex: 11999999999): ").strip()
    if not telefone:
        print(" Telefone é obrigatório!")
        return False
    
    email = input("Email (opcional): ").strip() or None
    
    ativo = input("Cliente ativo? (s/N): ").strip().lower() == 's'
    
    inadimplente = input("Cliente inadimplente? (s/N): ").strip().lower() == 's'
    
    observacoes = input("Observações (opcional): ").strip() or None
    
    print()
    print("CONFIRME OS DADOS:")
    print(f"Nome: {nome}")
    print(f"Telefone: {telefone}")
    print(f"Email: {email or '(não informado)'}")
    print(f"Ativo: {'Sim' if ativo else 'Não'}")
    print(f"Inadimplente: {'Sim' if inadimplente else 'Não'}")
    print(f"Observações: {observacoes or '(nenhuma)'}")
    
    confirma = input("\nConfirmar cadastro? (S/n): ").strip().lower()
    if confirma == 'n':
        print(" Cadastro cancelado!")
        return False
    
    try:
        db = DatabaseManager()
        cliente_id = db.inserir_cliente(
            nome=nome,
            telefone=telefone,
            email=email,
            ativo=ativo,
            inadimplente=inadimplente,
            observacoes=observacoes
        )
        
        print()
        print("✅ Cliente cadastrado com sucesso!")
        print(f"   ID: {cliente_id}")
        print()
        return True
        
    except Exception as e:
        print()
        print(f"❌ Erro ao cadastrar cliente: {e}")
        print()
        return False


def adicionar_cliente_lote():
    """Adiciona múltiplos clientes de uma só vez"""
    print("📝 ADICIONAR CLIENTES EM LOTE")
    print()
    print("Digite os dados de cada cliente no formato:")
    print("nome;telefone;email;ativo;inadimplente;observacoes")
    print()
    print("Exemplo:")
    print("João Silva;11999999999;joao@email.com;s;n;Cliente VIP")
    print("Maria Santos;11988888888;;;n;")
    print()
    print("Digite 'fim' quando terminar")
    print()
    
    clientes = []
    while True:
        linha = input("Cliente: ").strip()
        if linha.lower() == 'fim':
            break
        
        if not linha:
            continue
        
        partes = linha.split(';')
        if len(partes) < 2:
            print(" Formato inválido! Mínimo: nome;telefone")
            continue
        
        nome = partes[0].strip()
        telefone = partes[1].strip()
        email = partes[2].strip() if len(partes) > 2 and partes[2].strip() else None
        ativo = partes[3].strip().lower() == 's' if len(partes) > 3 else True
        inadimplente = partes[4].strip().lower() == 's' if len(partes) > 4 else False
        observacoes = partes[5].strip() if len(partes) > 5 and partes[5].strip() else None
        
        clientes.append({
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'ativo': ativo,
            'inadimplente': inadimplente,
            'observacoes': observacoes
        })
    
    if not clientes:
        print(" Nenhum cliente para adicionar!")
        return
    
    # Confirmar
    print()
    print(f"TOTAL: {len(clientes)} clientes")
    for i, c in enumerate(clientes, 1):
        print(f"{i}. {c['nome']} - {c['telefone']}")
    
    confirma = input("\nConfirmar cadastro em lote? (S/n): ").strip().lower()
    if confirma == 'n':
        print(" Cadastro cancelado!")
        return
    
    # Adicionar no banco
    db = DatabaseManager()
    sucesso = 0
    erros = 0
    
    print()
    print("Processando...")
    for c in clientes:
        try:
            db.inserir_cliente(**c)
            sucesso += 1
            print(f"SUCESSO {c['nome']}")
        except Exception as e:
            erros += 1
            print(f"ERRO {c['nome']}: {e}")
    
    print()
    print(f" SUCESSO: {sucesso}")
    print(f" ERRO: {erros}")


def importar_csv():
    """Importa clientes de um arquivo CSV"""
    import csv
    
    print("IMPORTAR CLIENTES DE CSV")
    print()
    
    arquivo = input("Caminho do arquivo CSV: ").strip()
    if not arquivo or not os.path.exists(arquivo):
        print(" Arquivo não encontrado!")
        return
    
    print()
    print("Formato esperado do CSV:")
    print("nome,telefone,email,ativo,inadimplente,observacoes")
    print()
    
    confirma = input("Continuar? (S/n): ").strip().lower()
    if confirma == 'n':
        return
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            clientes = []
            
            for row in reader:
                clientes.append({
                    'nome': row.get('nome', '').strip(),
                    'telefone': row.get('telefone', '').strip(),
                    'email': row.get('email', '').strip() or None,
                    'ativo': row.get('ativo', 's').strip().lower() == 's',
                    'inadimplente': row.get('inadimplente', 'n').strip().lower() == 's',
                    'observacoes': row.get('observacoes', '').strip() or None
                })
        
        if not clientes:
            print(" Nenhum cliente encontrado no CSV!")
            return
        
        print()
        print(f" {len(clientes)} clientes encontrados no arquivo")
        print()
        
        confirma = input("Importar todos? (S/n): ").strip().lower()
        if confirma == 'n':
            print("[ERRO] Importação cancelada!")
            return
        
        db = DatabaseManager()
        sucesso = 0
        erros = 0
        
        print()
        print("Processando...")
        for c in clientes:
            if not c['nome'] or not c['telefone']:
                erros += 1
                print(f"[ERRO] Registro inválido: {c}")
                continue
            
            try:
                db.inserir_cliente(**c)
                sucesso += 1
                print(f"[SUCCESS] {c['nome']}")
            except Exception as e:
                erros += 1
                print(f"[ERRO] {c['nome']}: {e}")
        
        print()
        print(f"[SUCCESS] Importados: {sucesso}")
        print(f"[ERRO]: {erros}")
        
    except Exception as e:
        print(f" Erro ao ler CSV: {e}")


def listar_clientes():
    """Lista todos os clientes cadastrados"""
    try:
        db = DatabaseManager()
        clientes = db.get_clientes()
        
        if not clientes:
            print(" Nenhum cliente cadastrado ainda.")
            return
        
        print()
        print("=" * 80)
        print(" CLIENTES CADASTRADOS")
        print("=" * 80)
        print()
        print(f"{'ID':<5} {'Nome':<30} {'Telefone':<15} {'Ativo':<8} {'Inadimplente':<13}")
        print("-" * 80)
        
        for c in clientes:
            print(f"{c.id:<5} {c.nome:<30} {c.telefone:<15} "
                  f"{'✅' if c.ativo else '❌':<8} "
                  f"{'⚠️' if c.inadimplente else '✅':<13}")
        
        print("-" * 80)
        print(f"Total: {len(clientes)} clientes")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erro ao listar clientes: {e}")


def menu_principal():
    """Exibe menu principal"""
    while True:
        print()
        print("=" * 60)
        print("👥 GERENCIAMENTO DE CLIENTES")
        print("=" * 60)
        print()
        print("1. Adicionar cliente (interativo)")
        print("2. Adicionar clientes em lote (terminal)")
        print("3. Importar de CSV")
        print("4. Listar clientes")
        print("5. Sair")
        print()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            adicionar_cliente_interativo()
        elif opcao == '2':
            adicionar_cliente_lote()
        elif opcao == '3':
            importar_csv()
        elif opcao == '4':
            listar_clientes()
        elif opcao == '5':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")


if __name__ == '__main__':
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário. Até logo!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
