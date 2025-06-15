from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Define e carrega as configurações da aplicação a partir de um arquivo .env.
    """
    model_config = SettingsConfigDict(env_file="backend/.env", extra='ignore')

    # Segredos e Conexões
    SUPABASE_URL: str
    SUPABASE_KEY: str
    OPENAI_API_KEY: str
    WEAVIATE_API_KEY: str
    MOVI_TOKEN: str
    HUGGING_FACE_HUB_TOKEN: str
    ALLOWED_API_KEYS: str

@lru_cache
def get_settings() -> Settings:
    """
    Retorna a instância única das configurações.
    O cache garante que o objeto Settings seja criado apenas uma vez.
    """
    return Settings()