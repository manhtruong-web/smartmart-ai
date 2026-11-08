"""Đọc cấu hình từ biến môi trường, không ghi khóa bí mật trong mã nguồn."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartMart AI"
    debug: bool = False
    database_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    dataset_dir: Path = Path("../dataset/GroceryStoreDataset/dataset")
    faiss_index_dir: Path = Path("../faiss_index")
    image_search_top_k: int = 5
    max_image_size_mb: int = 8
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_image_type_set(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_image_types.split(",")}


settings = Settings()
