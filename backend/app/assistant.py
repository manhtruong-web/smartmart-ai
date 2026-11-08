"""Chatbot siêu thị có phân tích ý định và trả lời dựa trên SQL Server."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from .config import settings
from .products import format_product_context, search_products

STOP_WORDS = {
    "cho", "toi", "tôi", "hoi", "hỏi", "biet", "biết", "xin", "vui", "long",
    "lòng", "co", "có", "khong", "không", "san", "sản", "pham", "phẩm",
    "nao", "nào", "giup", "giúp", "tu", "tư", "van", "vấn", "gia", "giá",
    "bao", "bao", "nhieu", "nhiêu", "mot", "một", "loai", "loại", "con",
    "còn", "hang", "hàng", "voi", "với", "ngan", "ngân", "sach", "sách",
}


@dataclass(frozen=True)
class ChatIntent:
    kind: str
    keyword: str | None = None
    max_price: Decimal | None = None
    min_price: Decimal | None = None
    in_stock_only: bool = False


def _normalized(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def _extract_budget(question: str) -> Decimal | None:
    normalized = _normalized(question).replace(".", "").replace(",", "")
    match = re.search(r"(\d+(?:\s*\d{3})?)\s*(trieu|tr|k|nghin|ngan|dong|d)?", normalized)
    if not match:
        return None
    amount = Decimal(match.group(1).replace(" ", ""))
    unit = match.group(2) or ""
    if unit in {"trieu", "tr"}:
        amount *= 1_000_000
    elif unit in {"k", "nghin", "ngan"}:
        amount *= 1_000
    return amount


def _extract_keyword(question: str) -> str | None:
    words = re.findall(r"[a-zA-ZÀ-ỹ0-9-]+", question)
    useful = [word for word in words if _normalized(word) not in STOP_WORDS and len(word) > 2]
    return " ".join(useful[:4]) or None


def detect_intent(question: str) -> ChatIntent:
    normalized = _normalized(question)
    budget = _extract_budget(question)
    keyword = _extract_keyword(question)
    if any(word in normalized for word in ("xin chao", "hello", "chao ban", "cam on")):
        return ChatIntent("greeting")
    if "con hang" in normalized or "ton kho" in normalized or "co ban" in normalized:
        return ChatIntent("availability", keyword=keyword, in_stock_only=False)
    if "gia" in normalized or "bao nhieu" in normalized:
        return ChatIntent("price", keyword=keyword)
    if budget is not None and any(word in normalized for word in ("ngan sach", "duoi", "trong tam", "phu hop")):
        return ChatIntent("budget", max_price=budget, in_stock_only=True)
    if any(word in normalized for word in ("goi y", "tu van", "phu hop", "thay the", "tuong tu")):
        return ChatIntent("recommendation", keyword=keyword, in_stock_only=True)
    return ChatIntent("search", keyword=keyword)


def _format_money(value: Any) -> str:
    return f"{Decimal(str(value)):,.0f}".replace(",", ".") + " đồng"


def _deterministic_answer(intent: ChatIntent, products: list[dict[str, Any]]) -> str:
    if intent.kind == "greeting":
        return "Xin chào! Tôi có thể tra giá, tồn kho, tìm sản phẩm theo ngân sách và tư vấn sản phẩm đang có bán."
    if not products:
        if intent.kind == "budget" and intent.max_price is not None:
            return f"Hiện chưa tìm thấy sản phẩm đang còn hàng trong ngân sách {_format_money(intent.max_price)}."
        return "Tôi chưa tìm thấy sản phẩm phù hợp trong dữ liệu siêu thị. Bạn có thể thử tên hoặc danh mục cụ thể hơn."
    if intent.kind == "price":
        return "\n".join(
            f"- {item['TenSP']}: {_format_money(item['GiaBan'])}; "
            f"{'còn hàng' if item['SoLuongTon'] > 0 else 'hết hàng'}."
            for item in products[:10]
        )
    if intent.kind == "availability":
        return "\n".join(
            f"- {item['TenSP']}: {'còn ' + str(item['SoLuongTon']) + ' sản phẩm' if item['SoLuongTon'] > 0 else 'hết hàng'}."
            for item in products[:10]
        )
    if intent.kind == "budget":
        return "Các sản phẩm đang còn hàng phù hợp ngân sách:\n" + "\n".join(
            f"- {item['TenSP']}: {_format_money(item['GiaBan'])}."
            for item in products[:10]
        )
    return "Tôi tìm thấy các sản phẩm phù hợp:\n" + "\n".join(
        f"- {item['TenSP']} ({item['DanhMuc']}): {_format_money(item['GiaBan'])}; "
        f"{'còn hàng' if item['SoLuongTon'] > 0 else 'hết hàng'}."
        for item in products[:10]
    )


def answer_question(
    db: Session,
    question: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Trả về câu trả lời và nguồn sản phẩm để frontend hiển thị minh bạch."""
    intent = detect_intent(question)
    if intent.kind == "greeting":
        return {"answer": _deterministic_answer(intent, []), "products": [], "intent": intent.kind}

    products = search_products(
        db,
        keyword=intent.keyword,
        max_price=intent.max_price,
        min_price=intent.min_price,
        in_stock_only=intent.in_stock_only,
        limit=30,
    )
    fallback = _deterministic_answer(intent, products)
    if not settings.openai_api_key:
        return {"answer": fallback, "products": products, "intent": intent.kind}

    context = format_product_context(products)
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý SmartMart, luôn trả lời bằng tiếng Việt. "
                "Chỉ được sử dụng dữ liệu trong CONTEXT. Không được bịa tên, giá, "
                "tồn kho, thương hiệu hoặc khuyến mãi. Nếu CONTEXT không có thông "
                "tin, phải nói rõ chưa có dữ liệu. Trả lời ngắn gọn, thân thiện."
            ),
        }
    ]
    for item in (history or [])[-6:]:
        if item.get("role") in {"user", "assistant"} and item.get("content"):
            messages.append({"role": item["role"], "content": item["content"][:2000]})
    messages.append({
        "role": "user",
        "content": f"CONTEXT DỮ LIỆU SIÊU THỊ:\n{context}\n\nCÂU HỎI:\n{question}",
    })
    try:
        response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
            model=settings.openai_model,
            temperature=0.1,
            messages=messages,
        )
        answer = response.choices[0].message.content or fallback
    except Exception:
        # Khi dịch vụ AI tạm lỗi, vẫn trả lời bằng dữ liệu SQL đã truy vấn.
        answer = fallback + "\n\n(Lưu ý: dịch vụ AI đang tạm thời không khả dụng.)"
    return {"answer": answer, "products": products, "intent": intent.kind}
