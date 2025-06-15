# app/services/fluxo_chat.py
"""
Serviço principal que orquestra o fluxo de processamento de uma pergunta do usuário.
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.api import RespostaChat
from app.core.clients import (
    generate_chat_completion, 
    gerar_embedding_openai, 
    buscar_artigos_por_embedding
)
from app.core.dynamic_config import obter_parametro
from app.services.classificador import classificar_pergunta
from app.services.sessoes import obter_ou_criar_sessao, obter_detalhes_sessao
from app.services.mensagens import salvar_mensagem
from app.services.prompts import buscar_prompt_por_nome

logger = logging.getLogger(__name__)


async def buscar_artigos_weaviate(pergunta: str, categoria: Optional[str]) -> list:
    """
    Orquestra a busca de artigos no Weaviate (RAG).
    
    ATENÇÃO: Atualmente, a busca é feita sem filtro de categoria para garantir
    maior chance de encontrar resultados enquanto a base não está bem categorizada.
    A categoria recebida é ignorada para a busca, mas ainda pode ser usada para logs.
    """
    logger.info(f"Iniciando busca RAG para a pergunta: '{pergunta}' (Categoria classificada: '{categoria}' - não utilizada no filtro)")
    embedding = gerar_embedding_openai(pergunta)
    if embedding is None: 
        logger.warning("Não foi possível gerar o embedding da pergunta.")
        return []
    
    limite_rag = obter_parametro("rag_search_limit", default=3)
    
    # --- ALTERAÇÃO: A busca é sempre feita sem filtro de categoria ---
    artigos_encontrados = buscar_artigos_por_embedding(
        near_vector=embedding, categoria=None, limit=limite_rag
    )
        
    return artigos_encontrados


async def classificar_precisa_rag(pergunta: str) -> bool:
    """Classifica se a pergunta do usuário necessita de busca na base de conhecimento (RAG)."""
    prompt_nome = obter_parametro("prompt_rag_classificador", default="classificador_rag")
    prompt_obj = buscar_prompt_por_nome(prompt_nome)
    if not prompt_obj:
        logger.error(f"Prompt '{prompt_nome}' não encontrado.")
        return "?" in pergunta
    prompt_formatado = prompt_obj['conteudo'].format(pergunta=pergunta)
    resposta_llm_obj = generate_chat_completion(
        system_prompt=prompt_formatado, user_message="", 
        model=obter_parametro("modelo_classificacao", default="gpt-3.5-turbo"), 
        temperature=0.0
    )
    return "SIM" in resposta_llm_obj.get("content", "").strip().upper()


async def processar_pergunta(
    pergunta: str, 
    id_usuario: int
) -> RespostaChat:
    """
    Pipeline principal que processa a pergunta do usuário.
    """
    inicio = time.time()
    logger.info(f"🧠 Pergunta recebida para Usuário ID {id_usuario}: '{pergunta}'")

    id_sessao = obter_ou_criar_sessao(usuario_id=id_usuario)
    logger.info(f"Chat utilizando Sessão ID: {id_sessao} para Usuário ID: {id_usuario}")

    detalhes_sessao = obter_detalhes_sessao(id_sessao)
    data_inicio_sessao_str = "N/A"
    hora_inicio_sessao_str = "N/A"
    if detalhes_sessao and 'criado_em' in detalhes_sessao:
        try:
            data_criacao_dt = datetime.fromisoformat(detalhes_sessao['criado_em'])
            data_inicio_sessao_str = data_criacao_dt.strftime("%d/%m/%Y")
            hora_inicio_sessao_str = data_criacao_dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            logger.warning(f"Não foi possível formatar a data de criação da sessão {id_sessao}.")

    id_mensagem_pergunta = salvar_mensagem(
        pergunta=pergunta, resposta="", usuario_id=id_usuario, sessao_id=id_sessao,
        tipo_resposta="usuario", rag_utilizado=False, custo_total=0.0,
        tokens_prompt=0, tokens_completion=0, tempo_processamento=0.0
    )

    categoria = await classificar_pergunta(pergunta)
    precisa_rag = await classificar_precisa_rag(pergunta)
    logger.info(f"📚 Categoria: '{categoria}' | Precisa de RAG: {precisa_rag}")

    artigos_encontrados = []
    dados_llm = {}
    nome_prompt_usado = "desconhecido"
    resposta_final = "Desculpe, não consegui gerar uma resposta no momento."

    if precisa_rag:
        artigos_encontrados = await buscar_artigos_weaviate(pergunta, categoria)
        if artigos_encontrados:
            contexto = "\n\n---\n\n".join([f"Título: {a.get('title', '')}\nConteúdo: {a.get('content', '')}" for a in artigos_encontrados])
            nome_prompt = obter_parametro("prompt_chat_padrao", default="chat_padrao")
            nome_prompt_usado = nome_prompt
            prompt_obj = buscar_prompt_por_nome(nome_prompt)
            system_prompt = prompt_obj['conteudo'].format(historico_texto="", context=contexto, question=pergunta) if prompt_obj else "Responda de forma útil com base nas informações fornecidas."
            dados_llm = generate_chat_completion(
                system_prompt=system_prompt,
                user_message=pergunta,
                model=obter_parametro("modelo", default="gpt-4o"),
                temperature=float(obter_parametro("temperatura", default=0.7))
            )
            resposta_final = dados_llm.get("content", resposta_final)
        else:
            logger.warning("⚠️ RAG solicitado, mas nenhum artigo foi encontrado (mesmo após busca geral). Utilizando prompt sem contexto.")
            precisa_rag = False

    if not precisa_rag:
        nome_prompt = obter_parametro("prompt_chat_geral", default="chat_geral")
        nome_prompt_usado = nome_prompt
        prompt_obj = buscar_prompt_por_nome(nome_prompt)
        system_prompt = prompt_obj['conteudo'].format(pergunta=pergunta) if prompt_obj else "Você é um assistente prestativo."
        dados_llm = generate_chat_completion(
            system_prompt=system_prompt,
            user_message=pergunta,
            model=obter_parametro("modelo", default="gpt-4o"),
            temperature=float(obter_parametro("temperatura", default=0.7))
        )
        resposta_final = dados_llm.get("content", resposta_final)

    tempo_total = round(time.time() - inicio, 2)
    usage = dados_llm.get("usage")

    salvar_mensagem(
        id_da_mensagem_a_atualizar=id_mensagem_pergunta, pergunta=pergunta,
        resposta=resposta_final, usuario_id=id_usuario, sessao_id=id_sessao,
        prompt_usado=nome_prompt_usado, classificacao=categoria, tipo_resposta="ia",
        custo_total=dados_llm.get("cost", 0.0), tokens_prompt=usage.prompt_tokens if usage else 0,
        tokens_completion=usage.completion_tokens if usage else 0, artigos_fonte=artigos_encontrados,
        tempo_processamento=tempo_total
    )

    return RespostaChat(
        id_sessao=id_sessao,
        data_inicio_sessao=data_inicio_sessao_str,
        hora_inicio_sessao=hora_inicio_sessao_str,
        resposta=resposta_final,
        categoria=categoria,
        artigos=artigos_encontrados,
        tempo_processamento=tempo_total,
        prompt_usado=nome_prompt_usado
    )
