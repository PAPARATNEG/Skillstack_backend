from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SkillStack"
    VERSION: str = "0.1.0"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = (
        "postgresql://skillstack_user:skillstack_pass@localhost:5432/skillstack_db"
    )

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    OPENAI_API_KEY: str = ""

    # Поля для нейросети
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    class Config:
        env_file = ".env"

settings = Settings()