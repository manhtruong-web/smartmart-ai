# SmartMart AI

Website siêu thị tích hợp chatbot AI tiếng Việt và tìm kiếm sản phẩm bằng hình ảnh.

SmartMart AI Shopping Assistant hỗ trợ hội thoại, gợi ý theo tồn kho và kiểm
soát không bịa dữ liệu.

## Tiến độ triển khai

- [x] Giai đoạn 1: Phân tích yêu cầu và thiết kế cơ sở dữ liệu
- [ ] Giai đoạn 2: Tải, đọc và tiền xử lý GroceryStoreDataset
- [ ] Giai đoạn 3: Trích xuất đặc trưng ảnh và tìm kiếm bằng FAISS
- [ ] Giai đoạn 4: Xây dựng backend FastAPI
- [ ] Giai đoạn 5: Kết nối SQL Server và truy vấn sản phẩm
- [x] Giai đoạn 6: Xây dựng chatbot AI
- [ ] Giai đoạn 7: Xây dựng giao diện website
- [ ] Giai đoạn 8: Tích hợp và kiểm thử
- [ ] Giai đoạn 9: Đánh giá và triển khai

## Giai đoạn 2-3: Dataset và FAISS

Từ thư mục gốc dự án:

```bash
chmod +x scripts/download_dataset.sh
./scripts/download_dataset.sh
python scripts/dataset_reader.py
```

Lệnh đọc sẽ báo số ảnh của `train`, `val`, `test` và số lớp trong `classes.csv`.
Mỗi dòng split chính thức có đường dẫn ảnh, nhãn fine-grained và nhãn coarse-grained.

Cài dependency backend rồi tạo index chỉ từ tập train:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python scripts/build_index.py
```

Mô hình ResNet18 pretrained được dùng để trích xuất vector 512 chiều, chuẩn hóa
L2 và lưu bằng `faiss.IndexFlatIP` (inner product tương đương cosine similarity
sau chuẩn hóa). Tập validation/test không được đưa vào index.

Đánh giá truy hồi trên tập test:

```bash
python scripts/evaluate.py
```

## Chạy FastAPI

Sao chép `backend/.env.example` thành `backend/.env`, điền `DATABASE_URL` và
`OPENAI_API_KEY` nếu muốn bật chatbot sinh câu trả lời. Sau đó:

```bash
cd backend
uvicorn app.main:app --reload
```

Mở `frontend/index.html` bằng trình duyệt. Nếu trình duyệt chặn gọi API từ
file cục bộ, chạy `python -m http.server 5500 --directory frontend` rồi mở
`http://localhost:5500`.

### Chatbot hoàn chỉnh

Chatbot nhận diện các nhóm câu hỏi chào hỏi, giá, tồn kho, tìm theo ngân sách,
tìm kiếm và gợi ý. Các bộ lọc được chuyển thành truy vấn tham số hóa tới
SQL Server trước khi gọi OpenAI. OpenAI chỉ diễn đạt lại dữ liệu đã truy vấn;
nếu thiếu `OPENAI_API_KEY` hoặc API tạm lỗi, hệ thống dùng câu trả lời dự phòng
từ SQL Server và không tự tạo thông tin sản phẩm.

Ví dụ:

- `Sản phẩm này giá bao nhiêu?`
- `Có sữa còn hàng không?`
- `Gợi ý sản phẩm dưới 100.000 đồng`
- `Tư vấn sản phẩm phù hợp ngân sách 200k`

API `POST /api/chat` nhận:

```json
{
  "question": "Gợi ý sản phẩm dưới 100.000 đồng",
  "history": []
}
```

## Chạy Giai đoạn 1

1. Mở SQL Server Management Studio hoặc Azure Data Studio.
2. Mở file `database/create_database.sql`.
3. Chạy toàn bộ script. Script tạo database `SmartMartAI` và các bảng cần thiết.
4. Kiểm tra các bảng `DanhMuc`, `SanPham` và `SanPhamAnh`.

Chưa có dữ liệu giá bán hoặc tồn kho mẫu trong giai đoạn này. Những dữ liệu đó
phải được nhập từ nguồn kinh doanh thật của siêu thị, không lấy từ
`GroceryStoreDataset`.
>>>>>>> f121577 (Build SmartMart AI supermarket chatbot)
