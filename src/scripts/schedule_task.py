import os
import sys

def criar_agendamento_windows():
    batch_content = f'''@echo off
cd {os.path.dirname(os.path.abspath(__file__))}
python main.py
'''
    
    with open('agendar_cobranca.bat', 'w') as f:
        f.write(batch_content)
    
    print("Execute no Task Scheduler:")
    print("Ação: C:\\contabilidade_bot\\agendar_cobranca.bat")
    print("Agendamento: Diariamente 09:00")

if __name__ == "__main__":
    criar_agendamento_windows()