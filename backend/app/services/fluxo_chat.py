import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.api import RespostaChat
from app.core.clients import generate_chat_completion, _calcular_custo, buscar_artigos_por_embedding, gerar_embedding_openai
from app.core.cache import obter_parametro, obter_prompt
from app.services.classificador import classificar_pergunta
from app.services.sessoes import obter_ou_criar_sessao, obter_detalhes_sessao
from app.services.mensagens import salvar_mensagem
from app.utils.time_utils import formatar_timestamp_para_brt

logger = logging.getLogger(__name__)

async def buscar_artigos_weaviate(pergunta: str, categoria: Optional[str]) -> list:
    logger.info(f"Iniciando busca RAG para a pergunta: '{pergunta}'")
    embedding = await gerar_embedding_openai(pergunta)
    if embedding is None:
        logger.warning("Não foi possível gerar o embedding da pergunta.")
        return []
    limite_rag = obter_parametro("rag_search_limit", default=3)
    artigos_encontrados = buscar_artigos_por_embedding(near_vector=embedding, categoria=None, limit=limite_rag)
    return artigos_encontrados

async def processar_pergunta(pergunta: str, id_usuario: int) -> RespostaChat:
    inicio = time.time()
    logger.info(f"🧠 Pergunta recebida para Usuário ID {id_usuario}: '{pergunta}'")
    
    id_sessao = obter_ou_criar_sessao(usuario_id=id_usuario)
    detalhes_sessao = obter_detalhes_sessao(id_sessao)
    id_mensagem_pergunta = salvar_mensagem(pergunta=pergunta, resposta="", usuario_id=id_usuario, sessao_id=id_sessao, tipo_resposta="usuario")
    
    categoria = await classificar_pergunta(pergunta)
    precisa_rag = categoria not in ["social", "geral"]
    logger.info(f"📚 Categoria: '{categoria}' | Precisa de RAG: {precisa_rag}")
    
    artigos_encontrados = []
    system_prompt = ""
    nome_prompt_usado = ""

    if precisa_rag:
        artigos_encontrados = await buscar_artigos_weaviate(pergunta, categoria)
        if artigos_encontrados:
            contexto = "\n\n---\n\n".join([f"Título: {a.get('title', '')}\nConteúdo: {a.get('content', '')}" for a in artigos_encontrados])
            nome_prompt_usado = obter_parametro("prompt_chat_padrao", default="chat_padrao")
            prompt_obj = obter_prompt(nome_prompt_usado)
            system_prompt = prompt_obj['conteudo'].format(historico_texto="", context=contexto, question=pergunta) if prompt_obj else ""
        else:
            precisa_rag = False

    if not precisa_rag:
        nome_prompt_usado = obter_parametro("prompt_chat_geral", default="chat_geral")
        prompt_obj = obter_prompt(nome_prompt_usado)
        system_prompt = prompt_obj['conteudo'].format(pergunta=pergunta) if prompt_obj else ""
        
    dados_llm = await generate_chat_completion(
        system_prompt=system_prompt,
        user_message=pergunta,
        model=obter_parametro("modelo", default="gpt-4o"),
        temperature=float(obter_parametro("temperatura", default=0.7))
    )
    resposta_final = dados_llm.get("content", "Desculpe, não consegui gerar uma resposta no momento.")

    tempo_total = round(time.time() - inicio, 2)
    usage = dados_llm.get("usage")
    
    data_inicio_sessao_str, hora_inicio_sessao_str = "N/A", ""
    if detalhes_sessao and 'criado_em' in detalhes_sessao:
        data_hora_formatada = formatar_timestamp_para_brt(detalhes_sessao['criado_em'])
        if data_hora_formatada not in ["N/A", "Data Inválida"]:
            partes = data_hora_formatada.split(" ")
            data_inicio_sessao_str = partes[0]
            hora_inicio_sessao_str = partes[1]

    salvar_mensagem(
        id_da_mensagem_a_atualizar=id_mensagem_pergunta,
        pergunta=pergunta,
        resposta=resposta_final,
        usuario_id=id_usuario,
        sessao_id=id_sessao,
        tipo_resposta="ia",
        prompt_usado=nome_prompt_usado,
        classificacao=categoria,
        rag_utilizado=precisa_rag,
        custo_total=dados_llm.get("cost", 0.0),
        tokens_prompt=usage.prompt_tokens if usage else 0,
        tokens_completion=usage.completion_tokens if usage else 0,
        artigos_fonte=artigos_encontrados,
        tempo_processamento=tempo_total
    )

    return RespostaChat(
        id_mensagem=id_mensagem_pergunta,
        id_sessao=id_sessao,
        data_inicio_sessao=data_inicio_sessao_str,
        hora_inicio_sessao=hora_inicio_sessao_str,
        resposta=resposta_final,
        categoria=categoria,
        artigos=artigos_encontrados,
        tempo_processamento=tempo_total,
        prompt_usado=nome_prompt_usado
    )