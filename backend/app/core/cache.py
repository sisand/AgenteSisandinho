# app/core/cache.py
"""
Módulo para gerenciar um cache em memória simples para dados que mudam pouco,
como prompts e parâmetros, evitando chamadas repetidas ao banco de dados.
"""
import logging
from supabase import Client
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Dicionários globais que servirão como nosso cache.
PROMPTS_CACHE: Dict[str, Any] = {}
PARAMETROS_CACHE: Dict[str, Any] = {}

def _converter_valor(valor_str: str) -> Any:
    """Tenta converter o valor string do banco para um tipo Python apropriado."""
    if valor_str is None: return None
    valor_limpo = valor_str.strip().lower()
    if valor_limpo == 'true': return True
    if valor_limpo == 'false': return False
    try:
        if '.' in valor_limpo: return float(valor_limpo)
        return int(valor_limpo)
    except (ValueError, TypeError):
        return str(valor_str)

def carregar_parametros_para_cache(supabase: Client):
    """Carrega os parâmetros da tabela 'parametros' e os armazena no cache."""
    global PARAMETROS_CACHE
    logger.info("⚙️ Carregando parâmetros para o cache em memória...")
    try:
        response = supabase.table("parametros").select("nome, valor").execute()
        if response.data:
            PARAMETROS_CACHE = {item['nome']: _converter_valor(item['valor']) for item in response.data}
            logger.info(f"✅ {len(PARAMETROS_CACHE)} parâmetros carregados para o cache.")
    except Exception as e:
        logger.error(f"❌ Erro crítico ao carregar parâmetros para o cache: {e}")

def carregar_prompts_para_cache(supabase: Client):
    """Carrega os prompts da tabela 'prompts' e os armazena no cache."""
    global PROMPTS_CACHE
    logger.info("⚙️ Carregando prompts para o cache em memória...")
    try:
        response = supabase.table("prompts").select("nome, conteudo").eq("ativo", True).execute()
        if response.data:
            PROMPTS_CACHE = {item['nome']: item for item in response.data}
            logger.info(f"✅ {len(PROMPTS_CACHE)} prompts carregados para o cache.")
    except Exception as e:
        logger.error(f"❌ Erro crítico ao carregar prompts para o cache: {e}")

def obter_parametro(nome: str, default: Any = None) -> Any:
    """Busca um parâmetro do cache em memória."""
    return PARAMETROS_CACHE.get(nome, default)

def obter_prompt(nome: str) -> Any:
    """Busca um prompt do cache em memória."""
    return PROMPTS_CACHE.get(nome)

def obter_todos_parametros() -> Dict[str, Any]:
    """Retorna uma cópia de todos os parâmetros que estão em cache."""
    return PARAMETROS_CACHE.copy()
