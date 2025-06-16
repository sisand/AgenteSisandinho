# app/core/config.py
"""
Módulo de configuração da aplicação.
Carrega as variáveis de ambiente e as expõe através de um modelo Pydantic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # --- Configurações da API e Conexões ---
    ALLOWED_API_KEYS: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    OPENAI_API_KEY: str
    WEAVIATE_API_KEY: str
    HUGGING_FACE_HUB_TOKEN: Optional[str] = None # Tornamos opcional, caso o modelo seja público

    # --- VARIÁVEIS ADICIONADAS PARA CORRIGIR O ERRO DE STARTUP ---
    MOVI_TOKEN: Optional[str] = None # Token para a API do Movidesk (opcional se não for usado em todos os ambientes)
    ENVIRONMENT: str = "development" # Define um valor padrão

    class Config:
        # O nome do seu ficheiro de ambiente (ex: .env)
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Retorna uma instância cacheada das configurações da aplicação.
    O lru_cache garante que o ficheiro .env seja lido apenas uma vez.
    """
    return Settings()


