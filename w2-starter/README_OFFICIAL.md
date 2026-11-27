# Cập nhật theo bộ case CHÍNH THỨC của mentor (27/11/2026)

Mentor đã phát bộ case dùng chung cho cả 8 thành viên từ ngày
21/11/2026: `week2_meeting_notes_expected_20_cases.json` (+ bản `.md`
giải thích). Bản cập nhật này áp dụng bộ case vào ngày 27/11/2026.
Bộ này thay bộ luyện tự soạn (`w2-practice-cases.json`) làm chuẩn đo.

## Hợp đồng chính thức khác bài cũ ở 4 điểm — code đã sửa theo

1. Tên trường request: `meeting_text` (bài cũ: `meeting_notes`).
2. Tên trường response: danh sách là `actions`, mỗi việc có trường
   `action` (bài cũ: `action_items` / `task`).
3. Luật ngày: ngày có nêu ngày/tháng mà thiếu năm thì lấy năm theo
   ngày họp ghi trong biên bản; "on the same day" lấy theo ngày của
   sự kiện được nhắc tới. Chỉ khi không có ngày cụ thể nào thì mới
   để `due_date` là null.
4. Một việc chung của 2 người = 2 dòng riêng, mỗi dòng một owner.

## File đã thay / thêm

- `app/schemas.py` — viết lại theo hợp đồng chính thức.
- `app/main.py` — đọc `payload.meeting_text`.
- `prompts/w2_v2.md` — prompt mới cho hợp đồng chính thức (thêm luật
  ngày, luật việc chung 2 owner, luật "đồng ý = quyết định, đề xuất
  thì không").
- `app/services/llm.py` — nạp `w2_v2.md` thay cho `w2_v1.md` (chỉ đổi
  tên file prompt; retry/validate giữ nguyên).
- `tests/test_w2_errors.py` — cập nhật theo field mới, vẫn 8 test.
- `scripts/run_official.py` — chạy endpoint qua 20 case chính thức,
  ghi `reports/w2_official_results.json`.
- `scripts/evaluate_official.py` — chấm theo 52 dữ kiện của bộ chính
  thức (15 decisions + 37 actions), in thêm số case đạt trọn vẹn
  (x/20) và số dữ kiện bịa thêm.

## Cách chạy (trong thư mục w2-starter, venv đang bật)

```powershell
pytest -q tests\test_w2_errors.py
# Kỳ vọng: 8 passed

python scripts\run_official.py
# Kỳ vọng: 20 dòng HTTP 200

python scripts\evaluate_official.py
# In điểm từng case + Total .../52 + Fully passing .../20 + Invented
```

Gói này chỉ chứa những gì liên quan đến bộ case của mentor. Các file
của bộ luyện tự soạn trước đây (prompt `w2_v1.md`, `run_w2.py`,
`evaluate_w2.py`, `w2-practice-cases.json`) đã được cất riêng ngoài
thư mục dự án, không nằm trong gói này.
