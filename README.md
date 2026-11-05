# Hệ đa agent dự đoán bệnh tiểu đường & so sánh 3 bộ dữ liệu

Dự án cho môn Hệ đa agent: nhiều agent chuyên biệt phối hợp qua **bus tin nhắn** + **blackboard** (bộ nhớ chung)
để dự đoán đái tháo đường trên 3 bộ dữ liệu và so sánh sự khác biệt giữa chúng. **Agent 2 (EvaluatorAgent) tự đánh giá**
kết quả và yêu cầu làm lại khi chưa đạt.

| Dataset | File | Ghi chú |
|---|---|---|
| 1. Pima Indians Diabetes | `data/diabetes.csv` | 768 dòng, đo lâm sàng |
| 2. Diabetes Prediction 100k | `data/diabetes_dataset.csv` | 100.000 dòng, có HbA1c + đường huyết |
| 3. CDC BRFSS 2015 | `data/archive.zip` (3 file: `binary`, `5050split`, `012`) | khảo sát tự khai; `binary` là bản chính, `5050split` chạy như biến thể, `012` chỉ để mô tả |

## Chạy

```bash
pip install -r requirements.txt
python main.py                 # chạy đầy đủ (~2-3 phút trên máy 2 nhân)
python main.py --fast          # thử nhanh trên mẫu nhỏ
python make_report.py          # dựng lại báo cáo/biểu đồ từ outputs/results.json
python predict.py --input examples/patient_example.json   # dự đoán cho 1 người bằng "hội đồng" agent
```

Kết quả nằm trong `outputs/`: **`REPORT.md`** (báo cáo tiếng Việt), `figures/`, `metrics_summary.csv`, `results.json`,
`agent_trace.jsonl` (toàn bộ message giữa các agent). Mô hình cuối của mỗi dataset lưu ở `models/`.

## Giao diện web

Web app Flask: nhập thông tin một người -> 3 agent (mỗi agent = 1 mô hình đã huấn luyện ở `models/`) cho xác suất, so với ngưỡng riêng và **bỏ phiếu**. Tab "Kết quả nghiên cứu" hiển thị bảng chỉ số và biểu đồ từ `outputs/`.

```bash
pip install -r requirements-web.txt
python app.py                  # mở http://localhost:8000
```

Web **không cần dữ liệu gốc** (`data/`) và không huấn luyện lại, chỉ đọc `models/*.joblib` (~0,4 MB) nên rất nhẹ.

| Đường dẫn | Mô tả |
|---|---|
| `GET /` | Giao diện |
| `GET /healthz` | Kiểm tra sống + mô hình đã nạp |
| `GET /api/schema` | Danh sách trường nhập của từng agent |
| `POST /api/predict` | Dự đoán, nhận JSON cùng định dạng `examples/patient_example.json` |
| `GET /api/report` | Bảng chỉ số + danh sách biểu đồ |

```bash
curl -X POST localhost:8000/api/predict -H "Content-Type: application/json" \
  -d '{"common":{"age":52,"bmi":33.5,"sex":"female"},"kaggle100k":{"hbA1c_level":6.6}}'
```

Quy tắc: bắt buộc có `age`; agent nào có < 50% đặc trưng sẽ bị bỏ qua (cột chủng tộc của dataset 100k không tính). Muốn thêm/bớt ô nhập chỉ cần sửa `SCHEMA` trong `service.py`.

## Deploy

**Quan trọng:** file `models/*.joblib` phụ thuộc phiên bản scikit-learn. `requirements-web.txt` giữ scikit-learn ở dòng `1.9.x` (`~=1.9.0`). Nếu bạn chạy lại `main.py` bằng dòng khác (ví dụ 1.8 hoặc 2.x), hãy sửa dòng này cho khớp (`pip show scikit-learn`).

Mọi cách dưới đây đều cần đẩy dự án lên GitHub trước (trừ Hugging Face có thể upload trực tiếp):

```bash
git init && git add . && git commit -m "diabetes mas web"
git branch -M main
git remote add origin https://github.com/<ten-ban>/diabetes-mas.git
git push -u origin main
```

> `data/` nặng ~12 MB (có `archive.zip`). Web không cần nên nếu muốn repo nhẹ, thêm `data/` vào `.gitignore` trước khi `git add`. Cách này vẫn chạy được web, chỉ không chạy lại được `main.py` từ repo.

### Cách 1 - Render (miễn phí, dễ nhất)
1. Vào https://render.com -> **New -> Blueprint** (hoặc **Web Service**) -> chọn repo GitHub.
2. Với Blueprint: Render đọc `render.yaml` và tự cấu hình. Với Web Service nhập tay: *Build* `pip install -r requirements-web.txt`, *Start* `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`, *Health check path* `/healthz`.
3. Đợi build xong, nhận link dạng `https://diabetes-mas.onrender.com`.

Gói free sẽ "ngủ" sau ~15 phút không có truy cập, lần mở đầu tiên mất khoảng 30-60 giây. Nên mở trước khi thuyết trình/demo.

### Cách 2 - Hugging Face Spaces (miễn phí, không ngủ lâu, hợp demo học thuật)
1. https://huggingface.co/new-space -> SDK chọn **Docker** (template Blank).
2. Upload toàn bộ dự án (hoặc `git push` sang repo Space). Thêm vào đầu `README.md` của Space khối cấu hình:
   ```
   ---
   title: Diabetes MAS
   sdk: docker
   app_port: 7860
   ---
   ```
3. `Dockerfile` đã sẵn sàng (cổng 7860). Space tự build, link dạng `https://huggingface.co/spaces/<user>/<ten-space>`.

### Cách 3 - Railway / Fly.io / Heroku
- **Railway:** New Project -> Deploy from GitHub; dùng `Procfile` hoặc `Dockerfile` có sẵn.
- **Fly.io:** `fly launch` (nhận `Dockerfile`), rồi `fly deploy`.
- Biến môi trường `PORT` do nền tảng cấp, không cần đặt.

### Cách 4 - Chạy bằng Docker trên máy / VPS
```bash
docker build -t diabetes-mas .
docker run -p 8000:7860 diabetes-mas      # http://localhost:8000
```
Trên VPS có thể đặt Nginx/Caddy phía trước để có HTTPS và tên miền.

### Khắc phục sự cố
- `InconsistentVersionWarning` hoặc lỗi khi nạp `.joblib`: sai phiên bản scikit-learn, xem mục "Quan trọng" ở trên.
- Build lỗi hết bộ nhớ trên gói free: giảm `--workers 2` xuống `1`.
- `/healthz` báo `false` cho một mô hình: thiếu file trong `models/` (chạy `python main.py` để tạo lại).

## Cấu trúc

```
main.py                 điểm vào: dựng agent, gửi message khởi động, chạy bus
config.py               đường dẫn, ngưỡng tự đánh giá, mô tả dataset
agents/
  base.py               Message, Blackboard, MessageBus, Agent
  orchestrator.py       điều phối, vòng lặp huấn luyện -> tự đánh giá -> làm lại
  data_agent.py         nạp, làm sạch, bỏ trùng lặp, chia train/test
  model_agent.py        3 mô hình ứng viên + CV 5-fold + chiến lược (ngưỡng, class_weight, regularize, bỏ đặc trưng)
  evaluator_agent.py    AGENT 2 - tự đánh giá (9 tiêu chí, ra hành động khắc phục)
  comparator_agent.py   so sánh dataset: hiệu năng, đặc trưng chung, chuyển giao chéo, ablation
  reporter_agent.py / report_builder.py   biểu đồ + REPORT.md
predict.py              dự đoán một bệnh nhân bằng hội đồng 3 agent (dòng lệnh)
app.py                  web app Flask (giao diện + API)
service.py              nạp mô hình, schema form, hàm predict dùng cho web
templates/index.html    giao diện web
requirements-web.txt    thư viện tối thiểu để chạy/deploy web (ghim phiên bản)
Dockerfile, Procfile, render.yaml   cấu hình deploy
```

## Điều chỉnh

- Ngưỡng tự đánh giá (AUC tối thiểu, recall mục tiêu, overfitting…) trong `Config.thr` ở `config.py`.
- Thêm dataset mới: khai báo trong `DATASETS` (file, cột nhãn, cột phân loại, cột bỏ).
- Lưu ý: đây là mô hình nghiên cứu, **không phải công cụ chẩn đoán y khoa**.
