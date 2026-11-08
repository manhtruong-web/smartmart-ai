"""API FastAPI cho tìm kiếm sản phẩm, chatbot và tìm kiếm ảnh."""

from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .assistant import answer_question
from .config import settings
from .database import get_db
from .image_search import ImageIndex
from .products import find_products_by_dataset_labels, search_products

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=12)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products")
def products(
    keyword: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
):
    return search_products(db, keyword, category, brand, min_price, max_price)


@app.post("/api/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        return answer_question(db, payload.question, payload.history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Không thể xử lý câu hỏi: {exc}") from exc


@app.post("/api/image-search")
async def image_search(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.content_type not in settings.allowed_image_type_set:
        raise HTTPException(status_code=415, detail="Chỉ hỗ trợ JPEG, PNG hoặc WebP.")
    content = await file.read()
    if len(content) > settings.max_image_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ảnh vượt quá kích thước cho phép.")
    try:
        image = Image.open(BytesIO(content)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Tệp tải lên không phải ảnh hợp lệ.") from exc

    try:
        results = ImageIndex(settings.faiss_index_dir).search(image, settings.image_search_top_k)
        labels = list(dict.fromkeys(item["label"] for item in results if item.get("label")))
        matched_products = find_products_by_dataset_labels(db, labels)
        return {"matches": results, "products": matched_products}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
