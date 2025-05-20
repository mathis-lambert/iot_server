from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- General Configuration ---
    peripheral_port: str
    peripheral_baudrate: int

    # --- MongoDB Configuration ---
    mongo_host: str
    mongo_port: int
    mongo_username: str
    mongo_password: str

    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}"


settings = Settings()
