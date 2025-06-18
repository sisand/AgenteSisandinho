# app/utils/time_utils.py
"""
Módulo com funções utilitárias para manipulação de data e hora,
agora usando pytz para lidar com o horário de verão brasileiro.
"""
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

# Define o fuso horário de Brasília como uma constante para ser reutilizada
BRT_TIMEZONE = pytz.timezone('America/Sao_Paulo')

def formatar_timestamp_para_brt(timestamp_utc_str: str) -> str:
    """
    Converte uma string de timestamp em formato ISO (UTC) para uma string
    formatada no horário de Brasília (DD/MM/YYYY HH:MM:SS), lidando
    corretamente com o horário de verão.
    """
    if not timestamp_utc_str:
        return "N/A"
    
    try:
        # Converte a string para um objeto datetime.
        # A informação de fuso horário UTC já está na string do Supabase.
        dt_utc = datetime.fromisoformat(timestamp_utc_str)
        
        # Converte para o fuso horário de Brasília
        dt_brt = dt_utc.astimezone(BRT_TIMEZONE)
        
        # Formata para o padrão brasileiro
        return dt_brt.strftime('%d/%m/%Y %H:%M:%S')
    except (ValueError, TypeError) as e:
        logger.warning(f"Não foi possível formatar o timestamp '{timestamp_utc_str}': {e}")
        return "Data Inválida"

