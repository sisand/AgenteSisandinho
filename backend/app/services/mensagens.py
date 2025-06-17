# app/services/mensagens.py
"""
Serviço para gerenciar o salvamento e atualização de mensagens no banco de dados.
"""
import logging
from typing import Dict, Any, Optional, List
from app.core.clients import get_supabase_client

logger = logging.getLogger(__name__)

def salvar_mensagem(
    pergunta: str,
    resposta: str,
    usuario_id: int,
    sessao_id: int,
    tipo_resposta: str,
    id_da_mensagem_a_atualizar: Optional[int] = None,
    **kwargs: Any
) -> int:
    """
    Cria ou atualiza uma mensagem, salvando os metadados na coluna correta.
    """
    try:
        supabase = get_supabase_client()
        
        # --- CORREÇÃO AQUI: Garantimos que o valor correto de 'rag_utilizado' seja salvo ---
        # Ele vem do kwargs, que é preenchido no final do fluxo_chat.py
        rag_final = kwargs.get("rag_utilizado", False)

        metadados = {
            "prompt_usado": kwargs.get("prompt_usado"),
            "classificacao": kwargs.get("classificacao"),
            "rag_utilizado": rag_final, # <-- USA A VARIÁVEL CORRIGIDA
            "artigos_fonte": kwargs.get("artigos_fonte"),
            "custo_total": kwargs.get("custo_total"),
            "tokens_prompt": kwargs.get("tokens_prompt"),
            "tokens_completion": kwargs.get("tokens_completion"),
            "tempo_processamento": kwargs.get("tempo_processamento")
        }

        metadados = {k: v for k, v in metadados.items() if v is not None}

        dados_mensagem = {
            "pergunta": pergunta,
            "resposta": resposta,
            "usuario_id": usuario_id,
            "sessao_id": sessao_id,
            "tipo_resposta": tipo_resposta,
            "metadados": metadados
        }
        
        if id_da_mensagem_a_atualizar:
            logger.info(f"Atualizando mensagem ID: {id_da_mensagem_a_atualizar} com metadados RAG: {rag_final}")
            response = supabase.table("mensagens").update(dados_mensagem).eq("id", id_da_mensagem_a_atualizar).execute()
            return id_da_mensagem_a_atualizar
        else:
            logger.info(f"Criando nova mensagem para a sessão {sessao_id}")
            response = supabase.table("mensagens").insert(dados_mensagem).execute()
            novo_id_mensagem = response.data[0]['id']
            logger.info(f"Mensagem ID: {novo_id_mensagem} criada com sucesso.")
            return novo_id_mensagem

    except Exception as e:
        logger.error(f"Erro ao salvar mensagem: {e}")
        return 0
