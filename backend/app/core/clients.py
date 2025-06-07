"""
Módulo de clientes para serviços externos (OpenAI, Supabase e Weaviate)
"""

import logging
from functools import lru_cache
from typing import Optional, List
from openai import OpenAI
from supabase import create_client, Client
from app.core.config import settings
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter

# Logger
logger = logging.getLogger(__name__)

# Definindo dimensões dos modelos de embedding
EMBEDDING_DIMENSIONS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072
}
DEFAULT_EMBEDDING_DIM = EMBEDDING_DIMENSIONS.get(settings.EMBEDDING_MODEL, 1536)


# 🔗 OpenAI
@lru_cache(maxsize=1)
def get_openai_client():
    try:
        if not settings.OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY não está configurada")
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("✅ Cliente OpenAI conectado com sucesso.")
        return client
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar cliente OpenAI: {e}")
        raise


# 🔗 Supabase
@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("❌ SUPABASE_URL ou SUPABASE_KEY não estão configuradas")
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info(f"✅ Cliente Supabase conectado: {settings.SUPABASE_URL}")
        return client
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar cliente Supabase: {e}")
        raise


# 🔗 Cliente Weaviate
@lru_cache(maxsize=1)
def get_weaviate_client():
    try:
        if not settings.WEAVIATE_URL:
            raise ValueError("❌ WEAVIATE_URL não está configurada")

        auth_credentials = None
        if settings.WEAVIATE_API_KEY:
            auth_credentials = Auth.api_key(settings.WEAVIATE_API_KEY)

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=settings.WEAVIATE_URL,
            auth_credentials=auth_credentials,
        )

        # Testar se o cliente está pronto
        if not client.is_ready():
            raise RuntimeError("❌ Cliente Weaviate não está pronto para uso")

        logger.info("✅ Cliente Weaviate conectado com sucesso")
        return client

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar cliente Weaviate: {e}")
        raise


# 🔥 Função para gerar chat completion
async def generate_chat_completion(
    system_prompt: str,
    user_message: str,
    chat_history: Optional[List[dict]] = None,
    model: str = settings.DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    client = get_openai_client()

    try:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = response.choices[0].message.content.strip()
        return content

    except Exception as e:
        logger.error(f"❌ Erro ao gerar chat completion: {e}")
        raise


# 🔥 Função para gerar embedding
async def gerar_embedding_openai(texto: str) -> Optional[List[float]]:
    client = get_openai_client()

    try:
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texto
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embedding: {e}")
        return None


# 👇 FUNÇÃO ATUALIZADA 👇
# Adicionamos o parâmetro 'categoria: Optional[str] = None'
# Função para buscar artigos por embedding com filtro de categoria
async def buscar_artigos_por_embedding(
    embedding: List[float],
    categoria: Optional[str] = None, # Parâmetro opcional para o filtro
    limit: int = 5
):
    """
    Busca artigos no Weaviate por embedding, com um filtro opcional de categoria.
    """
    client = get_weaviate_client()

    # Monta o filtro apenas se a categoria for fornecida
    filtro = None
    if categoria:
        logger.warning(f"Filtro por categoria '{categoria}' ignorado pois o campo não existe no esquema do Weaviate.")
        #logger.info(f"Aplicando filtro de categoria: {categoria}")
        #filtro = Filter.by_property("categoria").equal(categoria)

    try:
        results = client.collections.get("Article").query.near_vector(
            near_vector=embedding,
            limit=limit,
            filters=filtro, # Aplica o filtro aqui (será None se não houver categoria)
            return_metadata=["distance"],
            return_properties=["title", "url", "resumo", "content"] # Adicionei 'content' que usamos no prompt
        )

        artigos = []
        if hasattr(results, "objects") and results.objects:
            for obj in results.objects:
                artigos.append({
                    "title": obj.properties.get("title", "(sem título)"),
                    "url": obj.properties.get("url", "#"),
                    "resumo": obj.properties.get("resumo", ""),
                    # Garante que o 'content' seja retornado para montar o prompt do RAG
                    "content": obj.properties.get("content", obj.properties.get("resumo", "")), 
                    "distance": obj.metadata.distance if obj.metadata else None
                })

        return artigos
    except Exception as e:
        logger.error(f"❌ Erro ao buscar artigos por embedding: {e}")
        return []


# 🔄 Gerenciar conexões
async def connect_clients():
    get_openai_client()
    get_supabase_client()
    get_weaviate_client()
    logger.info("🔗 Todas as conexões foram inicializadas com sucesso")


async def close_clients():
    logger.info("🔒 Todas as conexões foram fechadas (Weaviate, Supabase e OpenAI)")
