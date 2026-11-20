# Weekly Submission – W01 / Member Thư

**Feature (F01–F04 or Foundation):** Foundation — prompt engineering & phân loại issue (Tuần 1, slide 22–23 của Slide Package V12)

**What I studied (2–3 concepts):** phân loại issue theo category (Bug / Risk / Feature / Question) và mức ưu tiên P1/P2/P3; viết prompt theo phiên bản V1 → V2 → V3 và đo từng phiên bản trên cùng 20 case bằng script chấm của kit; kiểm tra môi trường của kit (smoke test, test mock Jira) và phân quyền theo project bằng header X-Allowed-Project.

**What I built (summary + key modules):** `run_classifier.py` (bản dynamic theo slide 23: prompt tách riêng thành `prompts/v1.md`, `prompts/v2.md`, `prompts/v3.md` — chạy từng phiên bản bằng `python run_classifier.py v2`, kết quả riêng từng bản ở `reports/results_v1.csv`, `reports/results_v2.csv`, `reports/results_v3.csv`). Script đọc 20 case từ `data/evaluation/issue_classification_gold.json` (chỉ dùng trường `text`, không gửi đáp án), gọi model, kiểm tra JSON bằng Pydantic, ghi CSV đúng định dạng của `scripts/evaluate_issue_classifier.py`.

**How to run:**

Chạy trong thư mục gốc của kit (Windows PowerShell) — chạy lại bản nộp V2 rồi chấm điểm:

```powershell
.venv\Scripts\Activate.ps1
# Bật môi trường ảo của dự án; thành công khi đầu dòng hiện (.venv).

python run_classifier.py v2
# Chạy prompt ở prompts/v2.md trên đúng 20 case của kit (chỉ gửi trường text,
# không gửi đáp án), kiểm tra JSON bằng Pydantic, ghi reports\results_v2.csv.
# Bỏ chữ v2 ở cuối thì script chạy cả 3 phiên bản V1/V2/V3.

python scripts\evaluate_issue_classifier.py reports\results_v2.csv
# Chấm bằng script chính thức của kit. Kết quả kỳ vọng:
#   Category accuracy: 20/20 = 100.0%
#   Priority accuracy: 19/20 = 95.0%
#   Critical P1 misses: []
```

Lưu ý khi chạy lại: lệnh `run_classifier.py` có gọi API OpenAI nên cần file `.env` chứa `OPENAI_API_KEY` và `OPENAI_MODEL` hợp lệ (key không nằm trong repo). Nếu chỉ cần kiểm chứng kết quả đã nộp mà không gọi lại API, chấm trực tiếp file kết quả đã commit — ra đúng 3 dòng kỳ vọng ở trên, không tốn thêm lượt gọi API nào:

```powershell
python scripts\evaluate_issue_classifier.py evidence\w1_predictions.csv
```

(`evidence\w1_predictions.csv` là bản sao của `reports\results_v2.csv` theo quy ước đặt file nộp của kit; chấm `reports\results_v1.csv` và `reports\results_v3.csv` để xem điểm hai phiên bản còn lại.)

**Results:**
- Phân loại 20 issue (model `gpt-4o-mini`, chấm bằng script của kit, chạy trên máy của mình):

| Phiên bản | Category | Priority | Critical P1 misses | Ca sai |
|---|---|---|---|---|
| V1 | 20/20 | 15/20 | [] | 05, 06, 08, 12, 13 |
| **V2 (bản nộp)** | **20/20** | **19/20** | **[]** | chỉ CASE-12 |
| V3 | 20/20 | 18/20 | [] | CASE-12, CASE-18 |

Bảng chi tiết từng case so với gold (chỉ so priority — category đúng 20/20 ở cả 3 phiên bản; ô ghi giá trị cụ thể là chấm khác gold, ô ✓ là chấm đúng gold):

| Case | Gold | V1 | V2 | V3 |
|---|---|---|---|---|
| CASE-01 | Bug / P1 | ✓ | ✓ | ✓ |
| CASE-02 | Bug / P1 | ✓ | ✓ | ✓ |
| CASE-03 | Bug / P1 | ✓ | ✓ | ✓ |
| CASE-04 | Bug / P1 | ✓ | ✓ | ✓ |
| CASE-05 | Feature / P3 | P2 ✗ | ✓ | ✓ |
| CASE-06 | Feature / P3 | P2 ✗ | ✓ | ✓ |
| CASE-07 | Feature / P2 | ✓ | ✓ | ✓ |
| CASE-08 | Feature / P3 | P2 ✗ | ✓ | ✓ |
| CASE-09 | Question / P3 | ✓ | ✓ | ✓ |
| CASE-10 | Question / P3 | ✓ | ✓ | ✓ |
| CASE-11 | Question / P3 | ✓ | ✓ | ✓ |
| CASE-12 | Question / P2 | P3 ✗ | P3 ✗ | P3 ✗ |
| CASE-13 | Risk / P2 | P1 ✗ | ✓ | ✓ |
| CASE-14 | Risk / P1 | ✓ | ✓ | ✓ |
| CASE-15 | Risk / P2 | ✓ | ✓ | ✓ |
| CASE-16 | Risk / P1 | ✓ | ✓ | ✓ |
| CASE-17 | Bug / P2 | ✓ | ✓ | ✓ |
| CASE-18 | Feature / P2 | ✓ | ✓ | P3 ✗ |
| CASE-19 | Question / P3 | ✓ | ✓ | ✓ |
| CASE-20 | Risk / P2 | ✓ | ✓ | ✓ |

- Mốc Tuần 1 (category ≥ 17/20, JSON đúng schema 100%, đúng cả 6 ca P1: CASE-01, 02, 03, 04, 14, 16): **V2 đạt cả 3 mốc**.
- Smoke test (chạy trên máy của mình): **PASS** - fixture files and counts are consistent (documents 15, jira_issues 30, issue_cases 20, retrieval_cases 20, rag_cases 30, agent_cases 20, security_cases 10).
- Test mock Jira (chạy trên máy của mình): **3 passed** (`pytest -q tests/test_mock_jira.py`).
- API key / model: bài chạy bằng API key tự tạo để luyện tập (key nằm trong `.env` local, không commit). Key, model chính thức và trần chi phí của khóa do AI Lead cấp vẫn chưa nhận được.
- Xác nhận: repo không chứa secret — `.env` và `.venv` đã được chặn bằng `.gitignore` của kit, đã kiểm tra bằng `git status` trước khi commit.

**Known failures / trade-offs:**
- CASE-12 ("Who must approve an incident report?") vẫn sai ở cả V2 và V3: model chấm P3 thay vì P2 — câu hỏi về phê duyệt vẫn bị model đọc như câu hỏi tra cứu sự kiện.
- V3 (18/20) thấp hơn V2 (19/20): V3 không sửa được CASE-12, lại làm CASE-18 ("Change status report frequency from weekly to daily") lật từ P2 đúng thành P3 sai. Bài học: đuổi theo ca sai cuối cùng có thể làm hỏng ca đang đúng — giữ phiên bản đo được tốt nhất (V2), không phải phiên bản mới nhất.
- Cài Docker Desktop lần đầu lỗi do chưa bật Virtual Machine Platform; đã xử lý bằng cách cài WSL 2 trước rồi cài lại Docker.

**Demo link:** (để trống ở Tuần 1)

**Next action:** Tuần 2 — chuyển prompt classifier thành API endpoint có structured output; học retry / xử lý lỗi 429 và timeout theo slide Tuần 2, không nhồi thêm quy tắc vào prompt Tuần 1 nữa.

**Một điều làm tốt / một điều thất bại / một cải tiến tiếp theo:** làm tốt — V2 sửa được 4/5 ca sai của V1 mà vẫn giữ nguyên cả 6 ca P1; thất bại — V3 không cứu được CASE-12 và làm hỏng CASE-18; cải tiến tiếp theo — đo mọi thay đổi trên cùng một bộ case và chỉ giữ thay đổi khi điểm đo thật tăng.
