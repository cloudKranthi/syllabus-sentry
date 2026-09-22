from urllib.parse import quote_plus
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    POSTGRES_USER:str="postgres"
    POSTGRES_PASSWORD:str="Shiva@37"
    POSTGRES_HOST:str="localhost"
    POSTGRES_PORT:int=5432
    POSTGRES_DB: str = "syllabus-sentry"
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    @property
    def async_url(self)->str:
        s:str=quote_plus(self.POSTGRES_PASSWORD)
        return(
           f"postgresql+asyncpg://{self.POSTGRES_USER}:{s}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    model_config=SettingsConfigDict(env_file=".env",env_file_encoding="UTF-8",extra="ignore")
settings=Settings()