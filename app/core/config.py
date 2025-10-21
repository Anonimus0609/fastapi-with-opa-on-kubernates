from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPA_SERVER_URL: str = "http://localhost:8181/v1/data/sample"
    APP_NAME: str = "FastAPI with OPA"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

settings = Settings()