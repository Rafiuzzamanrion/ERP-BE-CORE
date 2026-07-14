from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 5000
    MONGODB_URI: str = "mongodb://localhost:27017/erp"
    DB_NAME: str = "erp-fastapi"
    JWT_SECRET: str = "super_secret_key_change_me"
    JWT_EXPIRES_IN: str = "1d"
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLIENT_URL: str = "http://localhost:5173"
    NODE_ENV: str = "development"
    LOG_LEVEL: str = "info"
    REDIS_URL: str = "redis://localhost:6379"

    @property
    def client_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.CLIENT_URL.split(",") if origin.strip()
        ]

    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
