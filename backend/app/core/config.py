from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ARIA"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_api_key: str = ""
    huggingface_inference_base_url: str = "https://api-inference.huggingface.co/models"

    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "aria-market-intelligence"
    pinecone_namespace: str = "default"

    finnhub_api_key: str = ""
    newsapi_key: str = Field(default="", validation_alias="NEWS_API_KEY")

    top_k_vector: int = 20
    top_k_bm25: int = 20
    final_top_k: int = 8
    mmr_lambda: float = 0.65


settings = Settings()
