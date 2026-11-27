# Weekly Submission – W02 / Member Thư

**Feature (F01–F04 or Foundation):** Foundation — LLM API & structured responses (Tuần 2, slide 24–25 của Slide Package V12; Gate 1 chấm thứ Sáu 27/11/2026). Đo trên bộ case chính thức của mentor: `week2_meeting_notes_expected_20_cases` (TC01–TC20).

**What I studied (2–3 concepts):**

- Structured output: model chỉ trả JSON đúng khuôn, rồi kiểm tra lại bằng Pydantic phía server — JSON hỏng thì báo lỗi, không cho lọt.
- Xử lý lỗi theo từng request: timeout, 429, lỗi 5xx phía model và JSON hỏng được ánh xạ thành mã HTTP riêng (504 / 503 / 502) thay vì làm sập server.
- Retry có giới hạn: tối đa 3 lần thử (1 lần gọi đầu + tối đa 2 lần thử lại) cho lỗi tạm thời, chờ 1s rồi 2s giữa các lần thử (cộng jitter nhỏ), tôn trọng `Retry-After`, SDK đặt `max_retries=0` để retry không lồng nhau.
- Cách chấm theo hợp đồng của mentor: decision và action so theo nghĩa (khác câu chữ vẫn tính nếu cùng nghĩa); riêng owner và due_date kiểm chặt tuyệt đối, kể cả `null`.

**What I built (summary + key modules):** endpoint `POST /analyze-meeting`, toàn bộ nằm trong thư mục `w2-starter/`:

- `app/main.py` — cửa ngõ: endpoint `POST /analyze-meeting` (nhận field `meeting_text`) + `GET /health`; bảng ánh xạ lỗi: input sai → 422, timeout → 504, 429 dai dẳng → 503, lỗi phía model / JSON hỏng → 502.
- `app/schemas.py` — bộ khuôn mẫu theo hợp đồng chính thức: `MeetingRequest {meeting_text}`; `MeetingAnalysis {summary, decisions, actions}`; mỗi action là `{owner, action, due_date}`; `owner` và `due_date` được phép `null` (biên bản không ghi thì để trống, không bịa).
- `app/services/llm.py` — nơi duy nhất gọi OpenAI: prompt đọc từ `prompts/w2_v2.md`; `temperature=0`; timeout 20s; tối đa 3 lần thử (1 lần đầu + 2 lần thử lại).
- `prompts/w2_v2.md` — prompt theo hợp đồng của mentor: ngày thiếu năm thì lấy năm theo ngày họp; “on the same day” tính theo sự kiện được nhắc; việc chung của 2 người tách thành 2 dòng; đồng ý = quyết định, đề xuất thì không.
- `scripts/run_official.py` — người chạy thử hàng loạt: gửi từng case của bộ chính thức vào endpoint bằng FastAPI TestClient trong cùng tiến trình (không cần mở thêm cửa sổ uvicorn); ghi kết quả vào `reports/w2_official_results.json`.
- `scripts/evaluate_official.py` — người chấm điểm: đối chiếu với đáp án của mentor theo 52 dữ kiện (15 decisions + 37 actions); decision/action so theo nghĩa, owner và due_date chặt tuyệt đối; đạt là ≥ 45/52.
- `week2_meeting_notes_expected_20_cases.json` / `.md` — bộ case chính thức do mentor phát ngày 21/11/2026, dùng chung cho cả 8 thành viên.

**How to run:**

Chạy trong thư mục gốc của kit (Windows PowerShell), dùng lại venv cũ của Tuần 1 — không tạo venv mới, không cần `pip install` lại:

```powershell
.venv\Scripts\Activate.ps1
# Bật môi trường ảo của dự án; thành công khi đầu dòng hiện (.venv).

cd w2-starter
Copy-Item ..\.env .env
# Chép key luyện tập vào thư mục w2-starter. An toàn: .gitignore chặn .env
# khỏi Git — kiểm tra bằng git status trước khi commit.

pytest -q tests\test_w2_errors.py
# Chạy 8 test kịch bản lỗi, không tốn API, không cần mạng.

python scripts\run_official.py
# Chạy endpoint qua 20 case chính thức, ghi reports\w2_official_results.json.

python scripts\evaluate_official.py
# Chấm 52 dữ kiện. In từng case x/y OK/MISS, cuối cùng Total: .../52
# và PASS khi ≥ 45/52 (đúng mốc ≥85% của Gate 1).
```

Chạy thử API bằng tay (tùy chọn): `uvicorn app.main:app --reload --port 8000`, mở `http://127.0.0.1:8000/docs` → `POST /analyze-meeting` → Try it out với `{"meeting_text": "..."}`.

**Results:** (đo thật trên máy của mình ngày 27/11/2026 trên bộ case chính thức của mentor)

- Trích xuất trên bộ chính thức 20 case / 52 dữ kiện (model gpt-4o-mini, chấm bằng `scripts/evaluate_official.py`): **48/52 = 92,3% — PASS** (mốc ≥ 45/52).
- Case đạt trọn vẹn: **16/20**. Dữ kiện bị tính là bịa thêm (invented): 3 — cả 3 đều là vế diễn đạt lại của 3 dữ kiện bị mất dưới đây, không có ca nào bịa việc, người hay ngày ngoài biên bản.
- Output đúng schema: 100% (20/20 response HTTP 200 và qua được kiểm tra Pydantic; output sai khuôn sẽ thành 502 chứ không lọt qua).
- Test kịch bản lỗi: **8 passed, 1 warning in 0.32s** (chạy trên máy của mình ngày 27/11/2026; warning là StarletteDeprecationWarning của thư viện TestClient, vô hại) (`pytest -q tests\test_w2_errors.py`: happy path + input thiếu/rỗng → 422 + timeout → 504 + 429 dai dẳng → 503 + lỗi 500 → 502 + JSON hỏng → 502 + health).
- API key / model: bài chạy bằng API key tự tạo để luyện tập (key nằm trong `.env` local, không commit). Key, model chính thức và trần chi phí của khóa do AI Lead cấp vẫn chưa nhận được.
- Xác nhận: repo không chứa secret — `.env` và `.venv` đã được chặn bằng `.gitignore`, đã kiểm tra bằng `git status` trước khi commit.

Bảng điểm theo phiên bản đo:

| Phiên bản | Điểm | Ghi chú |
|---|---|---|
| V1 — đo trên bộ luyện tự soạn (26/11) | 46/52 | Bản nộp đầu tiên. Bộ chính thức của mentor phát từ 21/11 nhưng mình bỏ sót, nên lúc đó tự chuẩn bị bộ luyện để đo. |
| V2 — hợp đồng chính thức của mentor (bản nộp) | **48/52 — PASS** | Ngày 27/11 nhận được bộ chính thức: chỉnh lại hợp đồng ở 4 điểm (field `meeting_text`; response `actions`/`action`; luật ngày suy năm theo ngày họp và “on the same day”; việc chung 2 owner tách 2 dòng), viết prompt `w2_v2.md`, đo lại trên đúng bộ của mentor. |

**Known failures / trade-offs:**

- **4 dữ kiện bị mất ở 4 case (đo 27/11/2026 trên bộ chính thức):**
  - TC03 (3/4): action của An — model viết “Review the migration before deployment”, đáp án là “Review the database migration” (cùng owner An; cách diễn đạt lệch nên script chấm không khớp).
  - TC06 (1/2): action của Phu — model viết “address any feedback from the review”, đáp án là “Address feedback from the pull request review” (sót cụm “pull request”).
  - TC07 (1/2): decision — model viết “The API documentation needs improvement”, đáp án là “Improve the API documentation” (cùng nghĩa, khác cấu trúc câu).
  - TC15 (6/7): thiếu hẳn decision “Improve the authentication module” — lỗi trích xuất thật duy nhất trong 4 ca: biên bản nhiều việc, quyết định dạng “đồng ý cải thiện” bị sót.
  - Ghi chú về cách chấm: script chấm so theo nghĩa bằng độ trùng từ có ngưỡng; 3 ca TC03/TC06/TC07 nằm sát ngưỡng nên chưa được tính. Mình không nới ngưỡng thêm để tránh tự chấm lỏng tay; nếu mentor chấm theo nghĩa như hợp đồng đã công bố, 3 ca này có thể được tính, điểm sẽ là 51/52.
- **Lỗi đã gặp và sửa trong lúc đo V1 (26/11/2026) — lượt chạy thật đầu tiên gục 20/20:**
  - Hiện tượng: cả 20 case trả `HTTP 502`, nhãn `upstream_error` — chưa case nào có đáp án để chấm.
  - Nguyên nhân: `FileNotFoundError` trong hàm `_load_prompt` của `app/services/llm.py` — đường dẫn prompt đi lên 2 tầng (`.parent.parent`) thì dừng ở `app/`, trong khi thư mục `prompts/` nằm ở gốc `w2-starter` nên phải đi lên 3 tầng; lỗi xảy ra trước cả khi gọi API.
  - Vì sao 8 test lỗi không bắt được: chúng thay nguyên hàm `analyze_meeting` bằng bản giả qua monkeypatch nên không chạm vào dòng nạp prompt — đúng loại lỗi chỉ lượt chạy API thật mới lôi ra được.
  - Cách sửa: thêm đúng một `.parent` vào đường dẫn, chạy lại → cả 20 case đều `HTTP 200`.
  - Bài học giữ lại: cần cả hai lớp kiểm chứng — test giả lập cho logic xử lý lỗi, lượt chạy thật cho cấu hình/đường dẫn.
- Bộ luyện tự soạn của bản V1 đã được gỡ khỏi thư mục nộp; bài nộp chỉ giữ những gì liên quan đến bộ case chính thức của mentor.

**Demo link:** (để trống)

**PR link:** (để trống — repo cá nhân: https://github.com/thudoanct/tma-ai-engineering-fast-track)

**Next action:** Tuần 3 (30/11) — RAG / document search theo slide của tuần đó.

**Một điều làm tốt / một điều thất bại / một cải tiến tiếp theo:**

- **Làm tốt:** phát hiện bộ case chính thức bị bỏ sót ngay trong ngày Gate 1, chỉnh lại toàn bộ hợp đồng theo mentor và đo lại đạt 48/52 (92,3%) PASS trên đúng chuẩn chấm chung; kỷ luật “không bịa” giữ được — không ca nào bịa việc, người hay ngày ngoài biên bản.
- **Thất bại:** bỏ sót bộ case chính thức mentor phát từ 21/11/2026 nên bản nộp đầu tiên phải đo trên bộ tự soạn; TC15 cho thấy model vẫn sót quyết định khi biên bản có nhiều việc.
- **Cải tiến tiếp theo:** thêm vào prompt luật “giữ nguyên văn biên bản khi ghi decision/action” để giảm lệch diễn đạt như TC03/TC06/TC07, và đặt checklist đầu mỗi tuần: kiểm tra đủ tài liệu mentor đã phát trước khi bắt đầu làm.
