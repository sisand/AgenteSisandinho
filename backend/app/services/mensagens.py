# app/services/mensagens.py

"""
Módulo de Serviços para Gerenciamento de Mensagens
Contém a lógica de negócios para salvar e buscar mensagens de chat.
"""

import logging
from typing import List, Dict, Any, Optional

from app.core.clients import get_supabase_client

logger = logging.getLogger(__name__)


def salvar_mensagem(
    # Parâmetros para identificar a mensagem
    sessao_id: int,
    usuario_id: int,
    id_da_mensagem_a_atualizar: Optional[int] = None, # Chave para decidir entre INSERT e UPDATE

    # Conteúdo principal
    pergunta: str = "",
    resposta: str = "",
    tipo_resposta: str = "ia",
    
    # Metadados e métricas
    prompt_usado: Optional[str] = None,
    classificacao: Optional[str] = None,
    rag_utilizado: bool = False, # Parâmetro que faltava
    artigos_fonte: Optional[List[Dict]] = None,
    custo_total: float = 0.0,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    tempo_processamento: float = 0.0
) -> int:
    """
    Salva ou atualiza uma mensagem no banco de dados.
    - Se 'id_da_mensagem_a_atualizar' for None, cria uma nova mensagem (pergunta do usuário).
    - Se 'id_da_mensagem_a_atualizar' for fornecido, atualiza a mensagem existente (resposta da IA).

    Returns:
        O ID da mensagem salva/atualizada.
    """
    supabase = get_supabase_client()

    # Monta um dicionário com todos os dados recebidos
    dados_mensagem = {
        "pergunta": pergunta,
        "resposta": resposta,
        "usuario_id": usuario_id,
        "sessao_id": sessao_id,
        "tipo_resposta": tipo_resposta,
        "prompt_usado": prompt_usado,
        "classificacao": classificacao,
        "rag_utilizado": rag_utilizado,
        "artigos_fonte": artigos_fonte,
        "custo_total": custo_total,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "tempo_processamento": tempo_processamento
    }

    try:
        if id_da_mensagem_a_atualizar:
            # --- LÓGICA DE UPDATE ---
            # Remove campos que não devem ser atualizados (pergunta, etc.)
            dados_para_atualizar = {k: v for k, v in dados_mensagem.items() if v is not None and k != 'pergunta'}
            
            logger.info(f"Atualizando mensagem ID: {id_da_mensagem_a_atualizar}")
            response = (
                supabase.table("mensagens")
                .update(dados_para_atualizar)
                .eq("id", id_da_mensagem_a_atualizar)
                .execute()
            )
            return id_da_mensagem_a_atualizar
        else:
            # --- LÓGICA DE INSERT ---
            # Remove campos que não pertencem à inserção inicial (resposta, etc.)
            dados_para_inserir = {
                "pergunta": pergunta,
                "usuario_id": usuario_id,
                "sessao_id": sessao_id,
                "tipo_resposta": "usuario",
                "rag_utilizado": False,
            }
            logger.info(f"Criando nova mensagem para a sessão {sessao_id}")
            response = (
                supabase.table("mensagens")
                .insert(dados_para_inserir)
                .execute()
            )
            
            if response.data:
                mensagem_id = response.data[0]['id']
                logger.info(f"Mensagem ID: {mensagem_id} criada com sucesso.")
                return mensagem_id
            else:
                raise Exception("Falha ao inserir nova mensagem, nenhum dado retornado.")

    except Exception as e:
        logger.error(f"❌ Erro em salvar_mensagem: {e}")
        # Lançar a exceção permite que a camada superior decida como lidar com o erro
        raise


def buscar_mensagens_sessao(sessao_id: int) -> List[Dict[str, Any]]:
    """
    Busca todas as mensagens de uma sessão, ordenadas pela data de criação.
    """
    logger.info(f"Buscando histórico de mensagens para a sessão {sessao_id}.")
    try:
        supabase = get_supabase_client()
        
        # Seleciona colunas específicas de forma explícita e mais segura
        select_str = "id, pergunta, resposta, tipo_resposta, criado_em"
        
        response = (
            supabase.table("mensagens")
            .select(select_str)
            .eq("sessao_id", sessao_id)
            .order("criado_em", asc=True) # Ordena do mais antigo para o mais novo
            .execute()
        )
        
        logger.info(f"Carregadas {len(response.data)} mensagens da sessão {sessao_id}.")
        return response.data if response.data else []

    except Exception as e:
        logger.error(f"❌ Erro ao buscar mensagens da sessão {sessao_id}: {e}")
        return []