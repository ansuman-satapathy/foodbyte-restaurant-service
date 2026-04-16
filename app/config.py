from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "restaurants_db"

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    app_name: str = "foodbyte-restaurant-service"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
