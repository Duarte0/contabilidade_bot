from datetime import datetime, timedelta
from typing import Dict, Set
import requests
import json

class FeriadosManager:
    def __init__(self):
        self.feriados_nacionais = self._carregar_feriados_fixos()
        self._cache_feriados_moveis: Dict[int, Dict[str, datetime]] = {}
        self._cache_datas_feriados: Dict[int, Set[datetime.date]] = {}
    
    def _carregar_feriados_fixos(self) -> Dict[str, str]:
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
    
    def _calcular_pascoa(self, ano: int) -> datetime:
        """Calcula data da Páscoa usando algoritmo de Gauss"""
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
        
        return datetime(ano, mes, dia)
    
    def _carregar_feriados_moveis(self, ano: int) -> Dict[str, datetime]:
        """Carrega feriados móveis com cache"""
        if ano in self._cache_feriados_moveis:
            return self._cache_feriados_moveis[ano]
        
        pascoa = self._calcular_pascoa(ano)
        
        feriados = {
            'carnaval': pascoa - timedelta(days=47),
            'sexta_santa': pascoa - timedelta(days=2),
            'pascoa': pascoa,
            'corpus_christi': pascoa + timedelta(days=60)
        }
        
        self._cache_feriados_moveis[ano] = feriados
        return feriados
    
    def _get_datas_feriados_ano(self, ano: int) -> Set[datetime.date]:
        """Retorna conjunto de todas as datas de feriado do ano"""
        if ano in self._cache_datas_feriados:
            return self._cache_datas_feriados[ano]
        
        datas_feriados = set()
        
        # Feriados fixos
        for data_str in self.feriados_nacionais:
            dia, mes = map(int, data_str.split('-'))
            datas_feriados.add(datetime(ano, mes, dia).date())
        
        # Feriados móveis
        feriados_moveis = self._carregar_feriados_moveis(ano)
        for feriado in feriados_moveis.values():
            datas_feriados.add(feriado.date())
        
        self._cache_datas_feriados[ano] = datas_feriados
        return datas_feriados
    
    def is_feriado(self, data: datetime) -> bool:
        """Verifica se a data é feriado (otimizado com cache)"""
        return data.date() in self._get_datas_feriados_ano(data.year)
    
    def is_final_semana(self, data: datetime) -> bool:
        return data.weekday() >= 5
    
    def ajustar_data_util(self, data: datetime) -> datetime:
        """Ajusta data para o próximo dia útil"""
        data_ajustada = data
        
        while self.is_feriado(data_ajustada) or self.is_final_semana(data_ajustada):
            data_ajustada += timedelta(days=1)
        
        return data_ajustada
    
    def pre_carregar_feriados(self, anos: range):
        """Pré-carrega feriados para múltiplos anos"""
        for ano in anos:
            self._get_datas_feriados_ano(ano)