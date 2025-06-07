from datetime import datetime, timezone, timedelta

def get_brazil_time():
    """
    Retorna o datetime atual no fuso horário do Brasil (UTC-3).
    Usa o módulo datetime padrão sem depender do pytz.
    """
    # Criar datetime em UTC
    utc_now = datetime.now(timezone.utc)
    
    # Converter para fuso horário do Brasil (UTC-3)
    brazil_offset = timedelta(hours=-3)
    brazil_time = utc_now.replace(tzinfo=timezone.utc).astimezone(timezone(brazil_offset))
    
    return brazil_time

def parse_isoformat_safe(s: str) -> datetime:
    """
    Converte string ISO para datetime, tratando microssegundos incompletos e sufixo Z.
    """
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        if 'T' in s and '.' in s:
            base, rest = s.split('T')
            time_part, micro_part = rest.split('.')
            micro_part = (micro_part + '000000')[:6]  # Preenche até 6 dígitos
            fixed = f"{base}T{time_part}.{micro_part}"
            return datetime.fromisoformat(fixed)
        if s.endswith('Z'):
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        raise
