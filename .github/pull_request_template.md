## Mô tả
<!-- Làm gì? Vì sao? Liên quan tầng nào (models / repositories / services / controllers / views)? -->

## Cách kiểm tra
<!-- Lệnh chạy hoặc các bước thử -->

## Checklist
- [ ] Chạy được `uv run streamlit run src/app.py` và `uv run pytest`
- [ ] Không commit `.venv`, `__pycache__`, file JSON chạy thật (`data/*.json`)
- [ ] Tầng trên chỉ gọi tầng dưới (View -> Controller -> Service -> Repository -> Models)
- [ ] Không đụng file của người khác (nếu có, đã báo và gắn người đó review)
- [ ] Đã merge `main` mới nhất vào nhánh, không còn conflict
