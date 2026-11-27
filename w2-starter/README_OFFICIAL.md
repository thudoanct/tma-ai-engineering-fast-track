# W02 — API phân tích biên bản họp (bộ case chính thức của mentor)

Endpoint `POST /analyze-meeting` theo slide 24–25 (Slide Package V12):
nhận biên bản họp, trả về summary / decisions / actions có owner và
due_date, với xử lý lỗi đầy đủ (timeout, 429, input không hợp lệ, lỗi
phía model).

Bài được đo trên **bộ case chính thức của mentor** —
`week2_meeting_notes_expected_20_cases.json` (+ bản `.md` giải thích),
20 case TC01–TC20 dùng chung cho cả 8 thành viên, mentor phát ngày
21/11/2026. Tổng 52 dữ kiện (15 decisions + 37 actions); mốc đạt
≥ 45/52 (85%, Gate 1).

## Hợp đồng của bộ case — code làm đúng theo

1. Tên trường request: `meeting_text`.
2. Tên trường response: danh sách là `actions`, mỗi việc có trường
   `action` (kèm `owner` và `due_date`).
3. Luật ngày: ngày có nêu ngày/tháng mà thiếu năm thì lấy năm theo
   ngày họp ghi trong biên bản; "on the same day" lấy theo ngày của
   sự kiện được nhắc tới. Chỉ khi không có ngày cụ thể nào thì mới
   để `due_date` là null.
4. Một việc chung của 2 người = 2 dòng riêng, mỗi dòng một owner.
5. Decision và action chấm theo nghĩa; owner và due_date kiểm chặt
   tuyệt đối, kể cả null.

## Các file chính

- `app/schemas.py` — khuôn Pydantic theo hợp đồng: `MeetingRequest
  {meeting_text}`, `MeetingAnalysis {summary, decisions, actions}`,
  `ActionItem {owner, action, due_date}`.
- `app/main.py` — endpoint + ánh xạ lỗi: input sai → 422, timeout →
  504, 429 dai dẳng → 503, lỗi phía model / JSON hỏng → 502.
- `app/services/llm.py` — nơi duy nhất gọi OpenAI: prompt đọc từ
  `prompts/w2_v2.md`; temperature 0; timeout 20s; tối đa 3 lần thử
  (1 lần đầu + 2 lần thử lại), chờ 1s rồi 2s, tôn trọng Retry-After.
- `prompts/w2_v2.md` — prompt theo hợp đồng (luật ngày, luật việc
  chung 2 owner, luật "đồng ý = quyết định, đề xuất thì không").
- `tests/test_w2_errors.py` — 8 test kịch bản lỗi bằng model giả
  (không tốn API): happy path, input thiếu/rỗng → 422, timeout →
  504, 429 dai dẳng → 503, lỗi 500 → 502, JSON hỏng → 502, health.
- `scripts/run_official.py` — chạy endpoint qua 20 case chính thức
  bằng TestClient, ghi `reports/w2_official_results.json`.
- `scripts/evaluate_official.py` — chấm theo 52 dữ kiện của bộ chính
  thức (so theo nghĩa; owner/ngày chặt), in điểm từng case + tổng
  điểm + số case đạt trọn vẹn + số dữ kiện bịa thêm.
- `week2_meeting_notes_expected_20_cases.json` / `.md` — bộ case
  chính thức của mentor, đặt trong thư mục này để script đọc.

## Cách chạy (trong thư mục w2-starter, venv đang bật, .env đã chép vào)

```powershell
pytest -q tests\test_w2_errors.py
# Kỳ vọng: 8 passed

python scripts\run_official.py
# Kỳ vọng: 20 dòng HTTP 200

python scripts\evaluate_official.py
# In điểm từng case + Total .../52 + Fully passing .../20 + Invented
```

Chạy API bằng tay: `uvicorn app.main:app --port 8000` rồi mở
`http://127.0.0.1:8000/docs` để gọi thử.

## Kết quả đo (trên máy của mình, 27/11/2026)

- Trích xuất: **48/52 (92,3%) — PASS** (mốc ≥ 45/52); 16/20 case đạt
  trọn vẹn; invented 3.
- Test kịch bản lỗi: **8 passed**.
- API key để trong `.env` local (đã chặn khỏi Git bằng .gitignore).
