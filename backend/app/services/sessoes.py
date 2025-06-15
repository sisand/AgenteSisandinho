# services/sessoes.py

"""
Módulo de Serviços para Gerenciamento de Sessões de Usuário.
A lógica de timeout é baseada na inatividade (campo 'atualizado_em').
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from app.core.clients import get_supabase_client

logger = logging.getLogger(__name__)

# Constante de configuração para o tempo de inatividade da sessão
SESSAO_TIMEOUT_MINUTOS = 30

def obter_ou_criar_sessao(usuario_id: int) -> int:
    """
    Obtém a sessão ativa de um usuário ou cria uma nova se a última
    interação tiver excedido o tempo limite de inatividade.

    Args:
        usuario_id: ID do usuário.

    Returns:
        ID da sessão ativa.

    Raises:
        Exception: Se não for possível obter ou criar uma sessão.
    """
    supabase = get_supabase_client()
    now = datetime.now(timezone.utc)
    
    # 1. Tenta encontrar uma sessão ativa baseada na ÚLTIMA ATIVIDADE
    limite_inatividade = now - timedelta(minutes=SESSAO_TIMEOUT_MINUTOS)
    
    try:
        response = (
            supabase.table("sessoes")
            .select("id")
            .eq("usuario_id", usuario_id)
            .gt("atualizado_em", limite_inatividade.isoformat()) # <-- LÓGICA CORRIGIDA
            .order("atualizado_em", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            sessao_id = response.data[0]["id"]
            logger.info(f"Sessão ativa {sessao_id} encontrada para o usuário {usuario_id}.")
            
            # 2. Mantém a sessão viva, atualizando seu timestamp
            (supabase.table("sessoes")
             .update({"atualizado_em": now.isoformat()})
             .eq("id", sessao_id)
             .execute())
             
            return sessao_id

    except Exception as e:
        logger.error(f"Erro ao tentar obter sessão ativa: {e}")
        # Continua para criar uma nova sessão

    # 3. Se nenhuma sessão ativa foi encontrada, cria uma nova
    logger.info(f"Nenhuma sessão ativa encontrada. Criando nova sessão para o usuário {usuario_id}.")
    try:
        dados_nova_sessao = {
            "usuario_id": usuario_id,
            "criado_em": now.isoformat(),
            "atualizado_em": now.isoformat(),
        }
        
        insert_response = (
            supabase.table("sessoes")
            .insert(dados_nova_sessao, returning="minimal") # Use returning="minimal" para performance
            .execute()
        )
        
        # Após a inserção, busca o ID da sessão recém-criada
        # É a maneira mais confiável de obter o ID em diferentes configurações do Supabase
        id_response = (
            supabase.table("sessoes")
            .select("id")
            .eq("usuario_id", usuario_id)
            .order("criado_em", desc=True)
            .limit(1)
            .execute()
        )

        if id_response.data:
            nova_sessao_id = id_response.data[0]["id"]
            logger.info(f"Nova sessão {nova_sessao_id} criada com sucesso.")
            return nova_sessao_id
        else:
            raise Exception("Falha ao recuperar o ID da sessão recém-criada.")

    except Exception as e:
        logger.error(f"❌ Erro crítico ao criar nova sessão: {e}")
        raise

def listar_sessoes_usuario(usuario_id: int) -> List[Dict[str, Any]]:
    """
    Lista todas as sessões de um usuário.

    Args:
        usuario_id: ID do usuário.

    Returns:
        Lista de sessões ou lista vazia em caso de erro.
    """
    try:
        supabase = get_supabase_client()
        
        response = (
            supabase.table("sessoes")
            .select("id, criado_em, atualizado_em")
            .eq("usuario_id", usuario_id)
            .order("criado_em", desc=True)
            .execute()
        )
        
        return response.data if response.data else []
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar sessões do usuário {usuario_id}: {e}")
        return []
    
    # No final do seu arquivo app/services/sessoes.py

def obter_detalhes_sessao(sessao_id: int) -> Optional[Dict[str, Any]]:
    """
    Busca os detalhes completos de uma sessão específica pelo seu ID.

    Args:
        sessao_id: O ID da sessão a ser buscada.

    Returns:
        Um dicionário com os dados da sessão ou None se não for encontrada.
    """
    if not sessao_id:
        return None
        
    try:
        supabase = get_supabase_client()
        logger.info(f"Buscando detalhes para a sessão ID: {sessao_id}")
        
        response = supabase.table("sessoes") \
                           .select("id, criado_em, atualizado_em, usuario_id") \
                           .eq("id", sessao_id) \
                           .single() \
                           .execute()

        if response.data:
            logger.info(f"Detalhes da sessão ID {sessao_id} encontrados.")
            return response.data
        else:
            logger.warning(f"Nenhum detalhe encontrado para a sessão ID {sessao_id}.")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar detalhes da sessão ID {sessao_id}: {e}")
        return None