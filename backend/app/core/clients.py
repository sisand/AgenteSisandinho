import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any

from openai import OpenAI
from supabase import create_client, Client
import weaviate
from weaviate.classes.query import Filter # Importação necessária para o filtro

# Importa a função para obter as configurações
from app.core.config import get_settings
from app.core.dynamic_config import obter_parametro

logger = logging.getLogger(__name__)

# --- Clientes de Bootstrap (só dependem do .env) ---

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Cria e retorna o cliente Supabase usando as configurações da aplicação."""
    # CORREÇÃO: Chama get_settings() para carregar a variável settings
    settings = get_settings()
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Credenciais do Supabase não encontradas nas configurações.")
        
    logger.info("✅ Cliente Supabase pronto.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Cria e retorna o cliente OpenAI usando as configurações da aplicação."""
    # CORREÇÃO: Chama get_settings() para carregar a variável settings
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        raise ValueError("Chave da OpenAI não encontrada nas configurações.")

    logger.info("✅ Cliente OpenAI (Síncrono) pronto.")
    return OpenAI(api_key=settings.OPENAI_API_KEY)

# --- Clientes Dinâmicos (dependem dos parâmetros do banco) ---
# (O restante do arquivo permanece igual, mas incluído aqui para facilitar)

weaviate_client: Optional[weaviate.WeaviateClient] = None

def initialize_dynamic_clients():
    global weaviate_client
    settings = get_settings() # Também precisa das settings aqui
    logger.info("⚙️ Inicializando clientes dinâmicos (Weaviate)...")
    weaviate_url = obter_parametro("weaviate_url")
    if weaviate_url and settings.WEAVIATE_API_KEY:
        try:
            auth = weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
            # A chave da OpenAI também vem das settings
            client = weaviate.connect_to_weaviate_cloud(cluster_url=weaviate_url, auth_credentials=auth, headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY})
            client.connect()
            weaviate_client = client
            logger.info("✅ Cliente Weaviate (dinâmico) inicializado e conectado.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Weaviate: {e}")
    else:
        logger.error("❌ 'weaviate_url' não encontrado ou WEAVIATE_API_KEY faltando.")

def get_weaviate_client() -> weaviate.WeaviateClient:
    if not weaviate_client: raise RuntimeError("Cliente Weaviate não foi inicializado.")
    return weaviate_client


# --- Funções de Lógica de Negócio ---
# (As funções abaixo já usam os getters corrigidos, então não precisam de alteração)

def _calcular_custo(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    #... (código inalterado)
    precos = {"gpt-4": {"prompt": 10.0, "completion": 30.0}, "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50}}
    modelo_precos = precos.get(model, precos.get(obter_parametro("modelo"), precos["gpt-3.5-turbo"]))
    return ((prompt_tokens / 1_000_000) * modelo_precos["prompt"]) + ((completion_tokens / 1_000_000) * modelo_precos["completion"])

def generate_chat_completion(
    system_prompt: str, user_message: str, model: str, temperature: float,
    chat_history: Optional[List[dict]] = None
) -> Dict[str, Any]:
    #... (código inalterado)
    client = get_openai_client()
    try:
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history: messages.extend(chat_history)
        if user_message: messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        
        content = response.choices[0].message.content.strip()
        usage = response.usage
        custo = _calcular_custo(model, usage.prompt_tokens, usage.completion_tokens)
        
        return {"content": content, "usage": usage, "cost": custo}
    except Exception as e:
        logger.error(f"❌ Erro ao gerar chat completion: {e}")
        return {"content": "Desculpe, ocorreu um erro ao gerar uma resposta.", "usage": {}, "cost": 0.0}

def gerar_embedding_openai(texto: str) -> Optional[List[float]]:
    #... (código inalterado)
    client = get_openai_client()
    embedding_model = obter_parametro("embedding_model", default="text-embedding-ada-002")
    try:
        response = client.embeddings.create(model=embedding_model, input=texto.replace("\n", " "))
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embedding: {e}")
        return None
    
def buscar_artigos_por_embedding(
    near_vector: List[float],
    limit: int,
    categoria: Optional[str] = None
) -> List[Dict]:
    #... (código inalterado)
    client = get_weaviate_client()
    
    filtro = None
    if categoria and categoria != 'geral':
        logger.info(f"Aplicando filtro de categoria no Weaviate: {categoria}")
        filtro = Filter.by_property("categoria").equal(categoria)
    
    try:
        collection = client.collections.get("Article")
        
        results = collection.query.near_vector(
            near_vector=near_vector,
            limit=limit,
            filters=filtro,
            return_metadata=["distance"],
            return_properties=["title", "url", "content", "resumo", "movidesk_id"]
        )
        
        return [obj.properties for obj in results.objects]
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar artigos por embedding: {e}")
        return []

@lru_cache(maxsize=10)
def carregar_prompt_por_nome(nome: str) -> Optional[Dict[str, Any]]:
    #... (código inalterado)
    logger.info(f"🔍 Buscando prompt '{nome}' no banco de dados...")
    try:
        supabase = get_supabase_client()
        response = supabase.table("prompts").select("nome, conteudo").eq("nome", nome).limit(1).execute()
        if response.data:
            logger.info(f"✅ Prompt '{nome}' encontrado.")
            return response.data[0]
        else:
            logger.warning(f"⚠️ Prompt '{nome}' não encontrado.")
            return None
    except Exception as e:
        logger.error(f"❌ Erro ao buscar prompt '{nome}': {e}")
        return None