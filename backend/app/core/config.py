from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    ENVIRONMENT: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    OPENAI_API_KEY: str
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str = None

    MOVI_TOKEN: str
    MOVI_LIST_URL: str
    MOVI_DETAIL_URL: str
    BASE_ARTICLE_URL: str

    APP_PASSWORD: str
    
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


settings = Settings()
