from datetime import datetime, timedelta
import requests
import json

class FeriadosManager:
    def __init__(self):
        self.feriados_nacionais = self._carregar_feriados_fixos()
    
    def _carregar_feriados_fixos(self):
        return {
            '01-01': 'Confraternização Universal',
            '21-04': 'Tiradentes',
            '01-05': 'Dia do Trabalho',
            '07-09': 'Independência do Brasil',
            '12-10': 'Nossa Senhora Aparecida',
            '02-11': 'Finados',
            '15-11': 'Proclamação da República',
            '25-12': 'Natal'
        }
    
    def _carregar_feriados_moveis(self, ano):
        a = ano % 19
        b = ano // 100
        c = ano % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        mes = (h + l - 7 * m + 114) // 31
        dia = ((h + l - 7 * m + 114) % 31) + 1
        
        pascoa = datetime(ano, mes, dia)
        
        return {
            'carnaval': pascoa - timedelta(days=47),
            'sexta_santa': pascoa - timedelta(days=2),
            'pascoa': pascoa,
            'corpus_christi': pascoa + timedelta(days=60)
        }
    
    def is_feriado(self, data):
        data_str = data.strftime('%d-%m')
        ano = data.year
        
        if data_str in self.feriados_nacionais:
            return True
        
        feriados_moveis = self._carregar_feriados_moveis(ano)
        for feriado in feriados_moveis.values():
            if feriado.date() == data.date():
                return True
        
        return False
    
    def is_final_semana(self, data):
        return data.weekday() >= 5  
    
    def ajustar_data_util(self, data):
        data_ajustada = data
        
        while self.is_feriado(data_ajustada) or self.is_final_semana(data_ajustada):
            data_ajustada += timedelta(days=1)
        
        return data_ajustada