# Weekly Submission – W02 / Member Thư

**Feature (F01–F04 or Foundation):** Foundation — LLM API & structured responses (Tuần 2, slide 24–25 của Slide Package V12; Gate 1 chấm thứ Sáu 27/11/2026)

**What I studied (2–3 concepts):** structured output — model chỉ trả JSON đúng khuôn rồi kiểm tra lại bằng Pydantic phía server; xử lý lỗi theo từng request — timeout, 429, lỗi 5xx phía model và JSON hỏng được ánh xạ thành mã HTTP riêng (504 / 503 / 502) thay vì làm sập server; retry có giới hạn — tối đa 3 lần thử (1 lần gọi đầu + tối đa 2 lần thử lại) cho lỗi tạm thời, chờ 1s rồi 2s giữa các lần thử (cộng jitter nhỏ) và tôn trọng `Retry-After`, SDK đặt `max_retries=0` để retry không lồng nhau.

**What I built (summary + key modules):** endpoint `POST /analyze-meeting`, toàn bộ nằm trong thư mục `w2-starter/` (chép nguyên cả thư mục vào gốc kit, không chép lẻ từng file ra ngoài — kit đã có sẵn `app/`, `scripts/`, `tests/` trùng tên). Các module chính:

- `app/main.py` — cửa ngõ của chương trình: endpoint `POST /analyze-meeting` + `GET /health`; bảng ánh xạ lỗi: input sai → 422, timeout → 504, 429 dai dẳng → 503, lỗi phía model / JSON hỏng → 502.
- `app/schemas.py` — bộ khuôn mẫu: khuôn Pydantic `MeetingRequest` / `MeetingAnalysis` / `ActionItem`; `owner` và `due_date` được phép `null` (biên bản không ghi thì để trống, không bịa).
- `app/services/llm.py` — nơi duy nhất gọi OpenAI: prompt đọc từ `prompts/w2_v1.md`; `temperature=0`; timeout 20s; tối đa 3 lần thử (1 lần đầu + 2 lần thử lại).
- `scripts/run_w2.py` — người chạy thử hàng loạt: chạy endpoint qua cả 20 case luyện bằng FastAPI TestClient trong cùng tiến trình (không cần mở thêm cửa sổ uvicorn); ghi toàn bộ kết quả vào `reports/w2_results.json`.
- `scripts/evaluate_w2.py` — người chấm điểm: đối chiếu kết quả với đáp án kỳ vọng theo 52 dữ kiện; đạt là ≥ 45/52.

**How to run:**

Chạy trong thư mục gốc của kit (Windows PowerShell), dùng lại venv cũ của Tuần 1 — không tạo venv mới, không cần `pip install` lại:

```powershell
.venv\Scripts\Activate.ps1
# Bật môi trường ảo của dự án; thành công khi đầu dòng hiện (.venv).

cd w2-starter
Copy-Item ..\.env .env
# Chép key luyện tập vào thư mục w2-starter. An toàn: .gitignore của cả kit
# lẫn w2-starter đều chặn .env khỏi Git — kiểm tra bằng git status trước khi commit.

pytest -q tests\test_w2_errors.py
# Chạy 8 test kịch bản lỗi, không tốn API, không cần mạng.
# Kỳ vọng: 8 passed (happy path + input thiếu/rỗng → 422 + timeout → 504
# + 429 dai dẳng → 503 + lỗi 500 → 502 + JSON hỏng → 502 + health).

python scripts\run_w2.py
# Chạy endpoint qua 20 case luyện, ghi reports\w2_results.json.

python scripts\evaluate_w2.py
# Chấm 52 dữ kiện. Kỳ vọng in từng case x/y OK/MISS, cuối cùng Total: .../52
# và PASS khi ≥ 45/52 (đúng mốc ≥85% của Gate 1).
```

Chạy thử API bằng tay (tùy chọn): `uvicorn app.main:app --reload --port 8000`, mở `http://127.0.0.1:8000/docs` → `POST /analyze-meeting` → Try it out với `{"meeting_notes": "..."}`.

**Results:** [ĐÃ ĐIỀN ĐỦ — cả hai phần đều chạy thật trên máy của mình ngày 26/11/2026: test lỗi 8 passed trong 0,80 giây (kèm 1 warning vô hại của thư viện Starlette/httpx); trích xuất 46/52, PASS]

- Test kịch bản lỗi (chạy trên máy của mình ngày 26/11/2026): 8 passed / 8 (`pytest -q tests\test_w2_errors.py`).
- Trích xuất trên bộ luyện 20 case / 52 dữ kiện (model gpt-4o-mini, chấm bằng `scripts/evaluate_w2.py`): 46/52 = 88,5% — PASS (mốc ≥ 45/52). Bản nộp là V1.
- Output đúng schema: 100% (20/20 response qua được response_model + kiểm tra lại bằng Pydantic trong `llm.py`; output sai khuôn sẽ thành 502 chứ không lọt qua).
- Kịch bản lỗi Gate 1: 5/5 (422 input sai, 504 timeout, 503 khi 429 dai dẳng, 502 lỗi 5xx, 502 JSON hỏng) — đã đo thật ngày 26/11/2026, trong 8 test qua hết.
- API key / model: bài chạy bằng API key tự tạo để luyện tập (key nằm trong `.env` local, không commit). Key, model chính thức và trần chi phí của khóa do AI Lead cấp vẫn chưa nhận được.
- Xác nhận: repo không chứa secret — `.env` và `.venv` đã được chặn bằng `.gitignore`, đã kiểm tra bằng `git status` trước khi commit.

Bảng điểm theo phiên bản prompt (đo trên cùng bộ luyện, chỉ giữ thay đổi khi điểm đo thật tăng — như cách V1 → V2 của Tuần 1):

| Phiên bản | Điểm | Ca sai |
|---|---|---|
| V1 (bản nộp) | 46/52 | W2P-06 thiếu 1 action; W2P-07 thiếu 2 action; W2P-14 thiếu 1 decision + 1 action; W2P-20 thiếu 1 action — tổng 6 dữ kiện ở 4 case |
| V2 | — | Không làm V2: V1 đã PASS trên mốc (46/52 ≥ 45/52); sửa prompt sát Gate 1 có rủi ro lật các ca đang đúng (bài học V3 của Tuần 1 tụt 19 → 18), nên chốt V1 và ghi phân tích ca MISS vào mục trade-offs |

**Known failures / trade-offs:**

- **Lỗi đã gặp và sửa trong lúc đo V1 (26/11/2026) — lượt chạy thật đầu tiên gục 20/20:**
  - Hiện tượng: `run_w2.py` trả `HTTP 502` cho cả 20 case, nhãn `upstream_error` trong `reports/w2_results.json` — không phải prompt kém, vì chưa case nào có đáp án để chấm.
  - Nguyên nhân: `FileNotFoundError` trong hàm `_load_prompt` của `app/services/llm.py` — đường dẫn prompt đi lên 2 tầng (`.parent.parent`) thì dừng ở `app/`, trong khi thư mục `prompts/` nằm ở gốc `w2-starter` nên phải đi lên 3 tầng; lỗi xảy ra trước cả khi gọi API.
  - Vì sao 8 test lỗi không bắt được: chúng thay nguyên hàm `analyze_meeting` bằng bản giả qua monkeypatch nên không chạm vào dòng nạp prompt — đúng loại lỗi chỉ lượt chạy API thật mới lôi ra được.
  - Cách sửa: thêm đúng một `.parent` vào đường dẫn (sửa bằng Notepad trên máy của mình), chạy lại `run_w2.py` → cả 20 case đều `HTTP 200`.
  - Bài học giữ lại: cần cả hai lớp kiểm chứng — test giả lập cho logic xử lý lỗi, lượt chạy thật cho cấu hình/đường dẫn.
- **6 dữ kiện MISS ở 4 case (đo 26/11/2026):**
  - W2P-06 (2/3): thiếu action “Write the code review checklist” (owner=Bao, due=2026-11-26).
  - W2P-07 (1/3): thiếu cả 2 action — “Prepare the release notes” (Dung, 2026-12-03) và “Run the smoke tests” (Nam, 2026-12-04); quyết định vẫn đúng.
  - W2P-14 (2/4): thiếu decision “Start onboarding on 7 Dec 2026” và action “Mentor the new QA engineer” (Nam, 2026-12-07).
  - W2P-20 (1/2): thiếu action “Update the API docs” (Hanh, due=null).
  - Mẫu chung: các ca trượt đều là biên bản có nhiều việc, dữ kiện bị mất là việc/quyết định thứ hai trong biên bản; không có ca nào bịa thêm dữ kiện.
  - Điểm giữ được: cả 3 ca bẫy “không bịa” trọng điểm đều qua — W2P-03 (ngày tương đối → null) đạt 2/2, W2P-12 (họp chỉ bàn) đạt điểm kỷ luật 1/1, W2P-17 đạt trọn 5/5.

- Bộ 20 case đi kèm là **bộ luyện tự soạn, KHÔNG PHẢI GOLD** (`w2-practice-cases.json`, xem `w2-practice-cases-README.md`): kit chính thức không có bộ case biên bản họp trong `data/evaluation/`. Nếu mentor/AI Lead cấp bộ chính thức thì bộ đó mới là chuẩn chấm Gate 1, điểm trên bộ luyện chỉ để tập đo.
- Case W2P-20 ("due tomorrow" trong khi biết ngày họp 24/11) là ca để ngỏ: theo luật nghiêm của slide 25 thì `due_date` vẫn là `null`; nếu bộ chính thức tính là 2026-11-25 thì theo bộ chính thức. Ca này tiện hỏi mentor khi họ trả lời. Ở lượt đo 26/11, W2P-20 là một trong 4 ca MISS — script chấm không tìm thấy action nào khớp đủ task + owner + `due_date: null`.
- Tin nhắn hỏi mentor về bộ case chính thức Tuần 2: [CHƯA XÁC NHẬN — ghi rõ đã gửi ngày nào / mentor trả lời ra sao khi có].

**Demo link:** (để trống)

**PR link:** (để trống — repo cá nhân: https://github.com/thudoanct/tma-ai-engineering-fast-track)

**Next action:** Tuần 3 (30/11) — RAG / document search theo slide của tuần đó; không nhồi thêm quy tắc vào prompt Tuần 2 sau khi đã chốt bản nộp cho Gate 1.

**Một điều làm tốt / một điều thất bại / một cải tiến tiếp theo:**

- **Làm tốt:** cả hai bằng chứng Gate 1 đều là số đo thật trên máy của mình (test lỗi 8 passed; trích xuất 46/52 PASS) và kỷ luật “không bịa” giữ được ở mọi ca bẫy.
- **Thất bại:** lượt chạy thật đầu tiên gục 20/20 vì một lỗi đường dẫn prompt mà bộ test giả lập không bắt được; chỉ lượt chạy API thật mới lôi ra được.
- **Cải tiến tiếp theo:** thử prompt V2 nhắm vào nhóm ca nhiều-việc-bị-sót (nhắc model liệt kê đủ mọi action trong biên bản) và đo lại trên cùng bộ luyện, chỉ giữ khi điểm đo thật tăng; đồng thời chờ bộ case chính thức của mentor để đối chiếu.
