# app/core/clients.py
import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI
from supabase import create_client, Client
import weaviate
from weaviate.classes.query import Filter

from app.core.config import get_settings
from app.core.cache import obter_parametro

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

weaviate_client: Optional[weaviate.WeaviateClient] = None

def initialize_dynamic_clients():
    global weaviate_client
    settings = get_settings()
    logger.info("⚙️ Inicializando clientes dinâmicos (Weaviate)...")
    weaviate_url = obter_parametro("weaviate_url")
    if weaviate_url and settings.WEAVIATE_API_KEY:
        try:
            auth = weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=auth,
                headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
            )
            client.connect()
            weaviate_client = client
            logger.info("✅ Cliente Weaviate (dinâmico) inicializado e conectado.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Weaviate: {e}")

def get_weaviate_client() -> weaviate.WeaviateClient:
    if not weaviate_client:
        raise RuntimeError("Cliente Weaviate não foi inicializado.")
    return weaviate_client

def _calcular_custo(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    precos = {"gpt-4o": {"prompt": 5.0, "completion": 15.0}, "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50}}
    modelo_precos = precos.get(model, precos.get(obter_parametro("modelo"), precos["gpt-3.5-turbo"]))
    return ((prompt_tokens / 1_000_000) * modelo_precos["prompt"]) + ((completion_tokens / 1_000_000) * modelo_precos["completion"])

async def gerar_embedding_openai(texto: str) -> Optional[List[float]]:
    client = get_openai_client()
    embedding_model = obter_parametro("embedding_model", default="text-embedding-ada-002")
    try:
        response = await client.embeddings.create(model=embedding_model, input=texto.replace("\n", " "))
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embedding: {e}")
        return None

async def generate_chat_completion(system_prompt: str, user_message: str, model: str, temperature: float) -> Dict[str, Any]:
    """Versão assíncrona que gera a resposta completa do chat e retorna um dicionário."""
    client = get_openai_client()
    try:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
        response = await client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        
        content = response.choices[0].message.content.strip()
        usage = response.usage
        custo = _calcular_custo(model, usage.prompt_tokens, usage.completion_tokens)
        
        return {"content": content, "usage": usage, "cost": custo}
    except Exception as e:
        logger.error(f"❌ Erro ao gerar chat completion: {e}")
        return {"content": "Desculpe, ocorreu um erro ao gerar a resposta.", "usage": None, "cost": 0.0}
        
def buscar_artigos_por_embedding(near_vector: List[float], limit: int, categoria: Optional[str] = None) -> List[Dict]:
    client = get_weaviate_client()
    filters = None
    if categoria and categoria != 'geral':
        filters = Filter.by_property("categoria").equal(categoria)
    try:
        collection = client.collections.get("Article")
        results = collection.query.near_vector(
            near_vector=near_vector, limit=limit, filters=filters,
            return_metadata=["distance"],
            return_properties=["title", "url", "content", "resumo", "movidesk_id"]
        )
        return [obj.properties for obj in results.objects]
    except Exception as e:
        logger.error(f"❌ Erro ao buscar artigos por embedding: {e}")
        return []
