from pydantic import BaseSettings


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0  # mặc định DB 0, service có thể override

    class Config:
        env_file = ".env"


settings = Settings()
