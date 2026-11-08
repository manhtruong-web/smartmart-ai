"""Các truy vấn sản phẩm dùng tham số hóa, tránh ghép chuỗi SQL."""

from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


def search_products(
    db: Session,
    keyword: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock_only: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conditions = ["sp.TrangThai = 1"]
    params: dict[str, Any] = {}
    safe_limit = min(max(limit, 1), 100)
    if keyword:
        terms = [term for term in keyword.split() if term]
        for index, term in enumerate(terms):
            param_name = f"keyword_{index}"
            conditions.append(
                f"(sp.TenSP LIKE :{param_name} OR sp.MoTa LIKE :{param_name} "
                f"OR sp.ThuongHieu LIKE :{param_name})"
            )
            params[param_name] = f"%{term}%"
    if category:
        conditions.append("dm.TenDM LIKE :category")
        params["category"] = f"%{category}%"
    if brand:
        conditions.append("sp.ThuongHieu LIKE :brand")
        params["brand"] = f"%{brand}%"
    if min_price is not None:
        conditions.append("sp.GiaBan >= :min_price")
        params["min_price"] = min_price
    if max_price is not None:
        conditions.append("sp.GiaBan <= :max_price")
        params["max_price"] = max_price
    if in_stock_only:
        conditions.append("sp.SoLuongTon > 0")

    query = text(f"""
        SELECT TOP {safe_limit} sp.MaSP, sp.TenSP, dm.TenDM AS DanhMuc,
               sp.MoTa, sp.ThuongHieu, sp.Anh, sp.DonViTinh,
               sp.GiaBan, sp.SoLuongTon, sp.HanSuDung
        FROM dbo.SanPham sp
        INNER JOIN dbo.DanhMuc dm ON dm.MaDM = sp.MaDM
        WHERE {' AND '.join(conditions)}
        ORDER BY sp.TenSP
    """)
    return [_row_to_dict(row) for row in db.execute(query, params).fetchall()]


def find_products_by_dataset_labels(db: Session, labels: list[str]) -> list[dict[str, Any]]:
    """Chỉ trả về sản phẩm có ánh xạ thật trong SQL Server."""
    if not labels:
        return []
    placeholders = ", ".join(f":label_{i}" for i in range(len(labels)))
    params = {f"label_{i}": label for i, label in enumerate(labels)}
    query = text(f"""
        SELECT DISTINCT TOP 50 sp.MaSP, sp.TenSP, dm.TenDM AS DanhMuc,
               sp.MoTa, sp.ThuongHieu, sp.Anh, sp.DonViTinh,
               sp.GiaBan, sp.SoLuongTon, sp.HanSuDung
        FROM dbo.SanPham sp
        INNER JOIN dbo.DanhMuc dm ON dm.MaDM = sp.MaDM
        INNER JOIN dbo.SanPhamAnh spa ON spa.MaSP = sp.MaSP
        WHERE sp.TrangThai = 1 AND spa.NhanDataset IN ({placeholders})
        ORDER BY sp.TenSP
    """)
    return [_row_to_dict(row) for row in db.execute(query, params).fetchall()]


def format_product_context(products: list[dict[str, Any]]) -> str:
    """Tạo dữ liệu có nguồn cho prompt; không tạo sản phẩm ngoài DB."""
    if not products:
        return "Không tìm thấy sản phẩm phù hợp trong cơ sở dữ liệu siêu thị."
    lines = []
    for product in products:
        stock = "còn hàng" if product["SoLuongTon"] > 0 else "hết hàng"
        lines.append(
            f"- {product['TenSP']} | danh mục: {product['DanhMuc']} | "
            f"thương hiệu: {product['ThuongHieu'] or 'chưa cập nhật'} | "
            f"giá: {product['GiaBan']} | {stock} | tồn: {product['SoLuongTon']}"
        )
    return "\n".join(lines)
