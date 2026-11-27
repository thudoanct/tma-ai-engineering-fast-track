# Tuần 2 — Bộ khởi động `POST /analyze-meeting`

> Slide 24 (assignment) + slide 25 (implementation guide), Gate 1 chấm
> thứ Sáu 27/11/2026. Tuần 2 chạy 23–27/11.
> Bộ 20 case đi kèm là **bộ luyện tự soạn, KHÔNG PHẢI GOLD** — xem
> `w2-practice-cases-README.md`. Nếu mentor cấp bộ chính thức thì bộ đó
> mới là chuẩn chấm Gate 1.

## Trong thư mục này có gì

| File | Để làm gì |
|---|---|
| `app/main.py` | Endpoint `POST /analyze-meeting` + bảng ánh xạ lỗi (422 / 504 / 503 / 502) |
| `app/schemas.py` | Khuôn Pydantic: `MeetingRequest`, `MeetingAnalysis`, `ActionItem` (owner/due_date được phép `null`) |
| `app/services/llm.py` | Chỗ duy nhất gọi OpenAI: tối đa 3 lần thử (1 lần đầu + 2 lần thử lại), chờ 1s rồi 2s, tôn trọng `Retry-After`, SDK đặt `max_retries=0` để không retry lồng nhau |
| `prompts/w2_v1.md` | System prompt V1 — toàn văn file là prompt, đúng kiểu Tuần 1 (v1/v2/v3 tách file) |
| `scripts/run_w2.py` | Chạy endpoint qua cả 20 case luyện, ghi `reports/w2_results.json` |
| `scripts/evaluate_w2.py` | Chấm `w2_results.json` theo đúng cách chấm 52 dữ kiện, mốc đạt ≥ 45/52 |
| `tests/test_w2_errors.py` | 5 kịch bản lỗi bắt buộc của Gate 1 (không cần key, không cần mạng) |

## Mốc Gate 1 cần đạt

- API chạy được chỉ từ README + trang `/docs`
- Output đúng schema 100%
- Trích xuất đúng ≥ 85% trên 20 case → ở bộ luyện này là **≥ 45/52 dữ kiện**
- Qua đủ 5/5 kịch bản lỗi
- Không lộ API key trong Git/log — lộ là rớt gate ngay

## Cách chạy trên máy Thư (PowerShell, thư mục kit)

Chép **nguyên thư mục `w2-starter`** (giữ nguyên cả thư mục, đừng chép
từng file con ra ngoài — trong kit đã có sẵn các thư mục `app/`,
`scripts/`, `tests/`, `requirements.txt` trùng tên, chép lẻ sẽ ghi đè
lên file của kit) + file `w2-practice-cases.json` vào thư mục gốc của
kit, rồi:

```powershell
.\.venv\Scripts\Activate.ps1
cd w2-starter
Copy-Item ..\.env .env
```

Dùng lại venv cũ của kit — **không cần tạo venv mới, không cần
`pip install` lại**: `requirements.txt` của kit đã có đủ mọi thư viện
trong `w2-starter/requirements.txt` (fastapi, uvicorn, openai,
pydantic, httpx, python-dotenv, pytest), nên venv bạn dùng từ Tuần 1
chạy được ngay. (File `.env` chép vào `w2-starter/` vẫn an toàn:
cả `.gitignore` của kit lẫn của `w2-starter/` đều chặn `.env`.)

**Bước 1 — chạy 5 test lỗi (không tốn API, làm trước):**

```powershell
pytest -q tests\test_w2_errors.py
```

Kỳ vọng: `8 passed` (5 kịch bản lỗi + đường happy path + 422 biên bản
rỗng + health).

**Bước 2 — chạy thử API bằng tay (tùy chọn):**

```powershell
uvicorn app.main:app --reload --port 8000
```

Mở `http://127.0.0.1:8000/docs` → bấm `POST /analyze-meeting` → Try it
out với `{"meeting_notes": "..."}`. Cửa sổ này đang chạy server thì
mở thêm một cửa sổ PowerShell khác cho các lệnh dưới.

**Bước 3 — chạy cả 20 case luyện rồi chấm:**

```powershell
python scripts\run_w2.py
python scripts\evaluate_w2.py
```

Kỳ vọng: in từng case `x/y OK/MISS`, cuối cùng `Total: .../52` và
`PASS` khi ≥ 45/52. Case nào MISS thì soi đúng chỗ đó (sai owner? sai
ngày? bịa thêm?) rồi sửa prompt — giống cách V1 → V2 ở Tuần 1: đo trên
cùng một bộ case, chỉ giữ thay đổi khi điểm đo thật tăng.

## Ba bẫy "không bịa" đã cài trong bộ luyện

- Ngày tương đối ("next Friday", "tomorrow", "this week") → `due_date`
  phải là `null`, không tự đổi sang ngày ISO.
- Việc chưa giao cho ai → `owner: null`, không tự gán cho PM hay người
  chủ trì.
- W2P-12: họp chỉ bàn, không quyết gì → cả hai danh sách đều rỗng.

## Còn mở

- **W2P-20** ("due tomorrow" trong khi biết ngày họp 24/11): theo luật
  nghiêm của slide 25 thì vẫn `null`; nếu bộ chính thức tính là
  2026-11-25 thì theo bộ chính thức. Ca này tiện hỏi mentor luôn.
- **Tin nhắn gửi mentor** (hỏi bộ case chính thức Tuần 2) vẫn chưa có
  xác nhận đã gửi — bản soạn sẵn ở `tin-nhan-gui-mentor-w01-w02.md`.
  Gửi hôm nay (thứ Bảy 21/11) vẫn kịp hơn để tới thứ Hai 23/11 mới hỏi.
- **Chưa kiểm chứng bằng model thật:** code + test + script chấm đã
  được chạy thử trong môi trường của Muse (8 test pass, chấm thử
  52/52 với đáp án đúng và 50/52 khi cố tình bịa ngày/quyết định),
  nhưng lần chạy thật bằng key của Thư trên máy Windows vẫn cần Thư
  tự chạy ở Bước 3 — kết quả đó mới là điểm thật của V1 Tuần 2.
