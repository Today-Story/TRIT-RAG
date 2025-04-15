from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX: str

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str = "us-east-1"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # DeepL
    DEEPL_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
