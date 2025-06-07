"""
Domínio para processamento de chat inteligente, com ou sem RAG.
"""

import logging
import time
from typing import Optional, List, Dict, Any

from app.core.clients import (
    get_openai_client,
    get_supabase_client,
    get_weaviate_client,
    gerar_embedding_openai,
    buscar_artigos_por_embedding,
    generate_chat_completion
)

from app.services.chat_flow import (
    classify_message,
    get_user_history,
    add_message_to_history,
    save_interaction
)

from app.services.prompts import buscar_prompt


logger = logging.getLogger(__name__)


async def responder_ao_usuario(
    pergunta: str,
    usar_rag: bool = True,
    usuario_id: Optional[int] = None,
    nome_usuario: Optional[str] = None,
    contexto_anterior: Optional[List[Dict[str, str]]] = None,
    sistema_prompt: Optional[str] = None,
    temperatura: float = 0.7
) -> Dict[str, Any]:
    """
    Processa uma pergunta e retorna a resposta, com ou sem RAG (busca vetorial).
    """

    inicio = time.time()

   

    # Classificar pergunta
    tipo = await classify_message(pergunta)
    
    # Definir se usa RAG pela classificação
    if tipo in ["tecnica", "fiscal", "comercial"]:
        usar_rag = True
    else:
        usar_rag = False
    
    logger.info(f"🧠 Pergunta recebida: {pergunta}")
    if usar_rag:
        logger.info("🔍 RAG Ativado")
    else:
        logger.info("💬 RAG Desativado (apenas IA)")

    # Adicionar ao histórico
    if usuario_id:
        add_message_to_history(usuario_id, pergunta, is_user=True)

    if tipo in ["social", "conversacional"]:
        logger.info(f"💬 Pergunta classificada como {tipo}, respondendo sem RAG.")
        resposta = await generate_chat_completion(
            system_prompt="Seja simpático, acolhedor e converse de forma leve.",
            user_message=pergunta,
            chat_history=contexto_anterior,
            temperature=temperatura
        )
        if usuario_id:
            add_message_to_history(usuario_id, resposta, is_user=False)
            await save_interaction(usuario_id, pergunta, resposta, tipo)

        return {
            "resposta": resposta,
            "tipo": tipo,
            "artigos": [],
            "prompt_usado": "Chat direto (sem RAG)",
            "tempo_processamento": round(time.time() - inicio, 2)
        }

    # Processamento com ou sem RAG
    artigos = []
    contexto = ""

    if usar_rag:
        try:
            embedding = await gerar_embedding_openai(pergunta)
            artigos_encontrados = await buscar_artigos_por_embedding(embedding)

            if artigos_encontrados:
                for artigo in artigos_encontrados:
                    artigos.append({
                        "title": artigo.get("title"),
                        "url": artigo.get("url"),
                        "trecho": artigo.get("resumo")
                    })
                contexto = "\n\n".join(
                    f"Título: {a['title']}\nResumo: {a['trecho']}\nFonte: {a['url']}" for a in artigos
                )
            else:
                logger.warning("⚠️ Nenhum artigo encontrado no Weaviate.")

        except Exception as e:
            logger.error(f"❌ Erro no RAG: {e}")
            contexto = ""
            artigos = []

    # Montar histórico
    historico = get_user_history(usuario_id) if usuario_id else ""

    # Buscar prompt
    try:
        prompt_base = buscar_prompt_personalizado("padrao") if not sistema_prompt else sistema_prompt
    except Exception as e:
        logger.warning(f"⚠️ Erro ao buscar prompt: {e}")
        prompt_base = """
Você é um assistente técnico da Sisand, focado em responder perguntas sobre nossos sistemas.
"""

    # Substituir placeholders
    prompt = prompt_base.replace("{pergunta}", pergunta)\
                         .replace("{contexto}", contexto)\
                         .replace("{historico}", historico)

    logger.debug(f"🧾 Prompt usado: {prompt}")

    try:
        resposta = await generate_chat_completion(
            system_prompt=prompt,
            user_message=pergunta,
            chat_history=contexto_anterior,
            temperature=temperatura
        )
    except Exception as e:
        logger.error(f"❌ Erro ao gerar resposta: {e}")
        resposta = "Desculpe, estou com dificuldades técnicas para responder agora."

    if usuario_id:
        add_message_to_history(usuario_id, resposta, is_user=False)
        await save_interaction(usuario_id, pergunta, resposta, tipo)

    tempo = round(time.time() - inicio, 2)

    return {
        "resposta": resposta,
        "tipo": tipo,
        "artigos": artigos,
        "prompt_usado": prompt,
        "tempo_processamento": tempo
    }
