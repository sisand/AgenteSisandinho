# app/core/dynamic_config.py

import logging
from supabase import Client

logger = logging.getLogger(__name__)

# Este dicionário em memória funcionará como um cache rápido dos parâmetros.
# Ele será populado na inicialização da aplicação.
parametros_db = {}

def _converter_valor(valor_str: str):
    """Tenta converter o valor string do banco para um tipo Python apropriado."""
    if valor_str is None:
        return None
    
    valor_limpo = valor_str.strip().lower()

    if valor_limpo == 'true': return True
    if valor_limpo == 'false': return False

    try:
        if '.' in valor_limpo: return float(valor_limpo)
        return int(valor_limpo)
    except (ValueError, TypeError):
        return str(valor_str) # Retorna o valor original como string

def carregar_parametros_do_banco(supabase: Client):
    """
    Carrega os parâmetros da tabela 'parametros' do Supabase.
    Esta função é SÍNCRONA.
    """
    logger.info("⚙️ Carregando parâmetros dinâmicos do banco de dados...")
    global parametros_db
    try:
        # A chamada ao Supabase é síncrona, então removemos o 'await'.
        response = supabase.table("parametros").select("nome, valor").execute()
        
        if response.data:
            parametros_carregados = {item['nome']: _converter_valor(item['valor']) for item in response.data}
            parametros_db = parametros_carregados
            logger.info(f"✅ {len(parametros_db)} parâmetros carregados com sucesso.")
            logger.debug(f"Parâmetros em memória: {parametros_db}")
        else:
            logger.warning("⚠️ Nenhum parâmetro encontrado na tabela 'parametros'.")
    except Exception as e:
        logger.error(f"❌ Erro crítico ao carregar parâmetros do banco: {e}.")

def obter_parametro(nome: str, default: any = None):
    """Função auxiliar para buscar um parâmetro do cache em memória com um valor padrão."""
    return parametros_db.get(nome, default)