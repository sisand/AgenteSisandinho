# app/services/prompts.py
"""
Camada de serviço para gerir a lógica de negócio relacionada com os prompts.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone # Importação necessária

# Importa as funções de cliente que acedem à base de dados
from app.core.clients import get_supabase_client, carregar_prompt_por_nome

logger = logging.getLogger(__name__)


def buscar_prompt_por_nome(nome: str) -> Optional[Dict[str, Any]]:
    """Busca um prompt pelo nome, utilizando a função cacheada do cliente."""
    logger.info(f"A obter prompt '{nome}' através da camada de serviço.")
    prompt_obj = carregar_prompt_por_nome(nome)
    if not prompt_obj:
        logger.warning(f"O prompt '{nome}' não foi encontrado na base de dados.")
    return prompt_obj


def atualizar_prompt_por_id(id_prompt: int, nome: str, conteudo: str) -> bool:
    """Atualiza um prompt existente na base de dados com base no seu ID."""
    try:
        supabase = get_supabase_client()
        # --- ALTERAÇÃO AQUI: Adicionado o campo 'atualizado_em' ---
        dados_para_atualizar = {
            "nome": nome, 
            "conteudo": conteudo,
            "atualizado_em": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"A atualizar o prompt ID: {id_prompt}")
        supabase.table("prompts").update(dados_para_atualizar).eq("id", id_prompt).execute()
        logger.info(f"Prompt '{nome}' (ID: {id_prompt}) atualizado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar o prompt ID {id_prompt}: {e}")
        return False


def criar_novo_prompt(nome: str, conteudo: str) -> bool:
    """Cria um novo prompt na base de dados."""
    try:
        supabase = get_supabase_client()
        dados = {"nome": nome, "conteudo": conteudo, "ativo": True}
        
        logger.info(f"A criar novo prompt com o nome: {nome}")
        supabase.table("prompts").insert(dados).execute()
        logger.info(f"Prompt '{nome}' criado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar o prompt '{nome}': {e}")
        return False


def listar_prompts_ativos() -> List[Dict[str, Any]]:
    """Lista todos os prompts ativos, ordenados por nome."""
    try:
        supabase = get_supabase_client()
        resultado = (
            supabase.table("prompts")
            .select("id, nome, conteudo, descricao, ativo")
            .eq("ativo", True)
            .order("nome")
            .execute()
        )
        logger.info(f"Listados {len(resultado.data)} prompts ativos.")
        return resultado.data if resultado.data else []
    except Exception as e:
        logger.error(f"Erro ao listar prompts: {e}")
        return []

