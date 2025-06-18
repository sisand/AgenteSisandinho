# ==============================================================================
# ARQUIVO 1 (NOVO ou CORRIGIDO): app/services/parametros.py
# ANÁLISE: Este arquivo agora contém a função 'atualizar_parametro'
# que estava em falta.
# ==============================================================================
import logging
from typing import Any

from app.core.clients import get_supabase_client
from app.core.cache import carregar_parametros_para_cache

logger = logging.getLogger(__name__)

def atualizar_parametro(nome: str, valor: Any) -> bool:
    """
    Atualiza o valor de um parâmetro no banco de dados e recarrega o cache.
    """
    try:
        supabase = get_supabase_client()
        logger.info(f"Atualizando parâmetro '{nome}' para o valor '{valor}'")
        
        # Atualiza o valor na tabela 'parametros'
        supabase.table("parametros").update({"valor": str(valor)}).eq("nome", nome).execute()
        
        # Recarrega todos os parâmetros para o cache em memória para refletir a mudança
        carregar_parametros_para_cache(supabase)
        
        logger.info(f"Parâmetro '{nome}' atualizado e cache recarregado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar o parâmetro '{nome}': {e}")
        return False
