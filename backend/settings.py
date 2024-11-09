from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # OpenRouter
    OPENROUTER_API_KEY: str
    LLM_MODEL_NAME: str = "openai/gpt-4o-mini"

    class Config:
        env_file = ".env"


settings = Settings()
