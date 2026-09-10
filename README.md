# TalentAudit — Project Blueprint

TalentAudit là hệ thống hỗ trợ tuyển dụng có kiểm soát, sử dụng LangGraph để điều phối các bước phân tích CV, đối chiếu yêu cầu công việc, đánh giá nhiều góc nhìn và yêu cầu nhà tuyển dụng phê duyệt trước khi gửi phản hồi.

> Hệ thống chỉ đưa ra **đề xuất có bằng chứng**. Quyết định tuyển dụng cuối cùng luôn thuộc về con người.

## Mục tiêu của bộ tài liệu

Bộ tài liệu này là nguồn ngữ cảnh dùng chung cho bạn và Codex trong suốt quá trình xây dựng dự án. Nó giúp:

- Khóa phạm vi MVP để tránh làm dự án quá lớn.
- Phân biệt đúng Router, Pipeline, Parallel Review và Debate.
- Thiết kế dự án Python chặt chẽ nhưng phù hợp với một portfolio Fresher.
- Quy định State, Reducer, persistence và Human-in-the-loop.
- Đặt tiêu chí nghiệm thu, evaluation và bảo mật ngay từ đầu.
- Hướng dẫn Codex qua file `AGENTS.md` ở thư mục gốc.

## Thứ tự đọc

1. [Tóm tắt dự án](docs/01_PROJECT_SUMMARY.md)
2. [Yêu cầu và phạm vi](docs/02_REQUIREMENTS.md)
3. [Kiến trúc hệ thống](docs/03_ARCHITECTURE.md)
4. [Cấu trúc source code](docs/04_PROJECT_STRUCTURE.md)
5. [State và workflow LangGraph](docs/05_STATE_AND_WORKFLOWS.md)
6. [Lộ trình triển khai](docs/06_ROADMAP.md)
7. [Evaluation, bảo mật và chất lượng](docs/07_EVALUATION_SECURITY.md)
8. [Câu hỏi phỏng vấn dự án](docs/08_PROJECT_INTERVIEW.md)

## Stack được đề xuất cho MVP

| Thành phần  | Lựa chọn                                   |
| ------------- | -------------------------------------------- |
| Ngôn ngữ    | Python 3.12                                  |
| API           | FastAPI                                      |
| Orchestration | LangGraph                                    |
| Validation    | Pydantic v2                                  |
| Database      | PostgreSQL + SQLAlchemy 2 + Alembic          |
| UI MVP        | Streamlit                                    |
| Test          | pytest                                       |
| Quality       | Ruff + mypy                                  |
| Runtime       | Docker Compose                               |
| Observability | Structured logging; LangSmith là tùy chọn |

## Milestone 0 — Bootstrap

Milestone 0 cung cấp nền móng chạy được, chưa triển khai pipeline CV, LangGraph, UI
Streamlit hoặc OpenAI:

- FastAPI với `GET /health` và `GET /ready`.
- Settings từ biến môi trường với tiền tố `TALENTAUDIT_`.
- Docker Compose gồm app và PostgreSQL 16.
- Ruff, mypy, pytest, pre-commit và GitHub Actions CI.

### Chạy kiểm tra local

Trong môi trường Python 3.12, sau khi cài dependency của project:

```bash
python -m pytest
python -m uvicorn --app-dir src talentaudit.main:app --reload
```

Sao chép `.env.example` thành `.env` khi cần ghi đè cấu hình local. Endpoint
`/health` không cần PostgreSQL; `/ready` chỉ trả trạng thái sẵn sàng khi database
truy cập được.

### Chạy bằng Docker Compose

```bash
docker compose up --build
```

Sau khi container healthy, API dùng tại `http://localhost:8000`.

## Milestone 2 — Day 08: extraction boundary

Đã có `LLMClient`, adapter OpenAI/fake, prompt v1 và `ProfileExtractor` kiểm chứng
evidence trước khi trả `CandidateProfile`. Đây là service độc lập; chưa nối vào
API hoặc LangGraph. Kết quả `NEEDS_REVIEW` không chứa profile để đưa vào matcher.

Tài liệu học và bàn giao:

- [Phân tích Day 08](docs/learning/M2_DAY08_ANALYSIS.md).
- [Báo cáo Day 08 và vai trò từng file](docs/reports/M2_DAY08_IMPLEMENTATION_REPORT.md).
- [Phân tích Day 09 và việc còn thiếu](docs/learning/M2_DAY09_ANALYSIS.md).

Các lệnh đã kiểm chứng từ thư mục gốc trên Windows, với `.venv` Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_profile_extractor.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_openai_adapter.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
```

Test dùng fake hoặc HTTP transport trong memory, chặn network và không cần API key.
Adapter thật chỉ được dùng khi cấu hình các biến `TALENTAUDIT_OPENAI_*` trong
environment/`.env` riêng; `.env.example` để trống key/model. Model phải hỗ trợ
Responses structured outputs và tham số temperature. Chưa kiểm chứng API thật hoặc
đo extraction F1; test fake không phải đánh giá chất lượng model.

## Milestone 2 — Day 09: regression và parser metadata

Đã có 10 fixture VI/EN qua extraction fake kèm manifest/hash, evidence regression,
PDF subprocess timeout và parser metadata migration 0003. Suite hiện có **157 tests**.
Các quality gate ở phần trên đã chạy lại và pass.

- [Báo cáo Day 09 và vai trò từng file](docs/reports/M2_DAY09_IMPLEMENTATION_REPORT.md).
- [Phân tích Day 10, có điều kiện nghiệm thu M2](docs/learning/M3_DAY10_ANALYSIS.md).

Migration đã pass trên SQLite tạm và PostgreSQL 16 container tạm, gồm fresh upgrade,
upgrade giữ dữ liệu và repository round-trip. Milestone 2 đã hoàn tất acceptance.
PDF worker không phải OS sandbox/hard RAM cap; fake regression không phải kết quả
chất lượng model thật.

## Các quyết định đã khóa — 02/09/2026

| Hạng mục               | Quyết định                                                    |
| ------------------------ | ---------------------------------------------------------------- |
| Mục tiêu portfolio     | LLM/LangGraph Agent                                              |
| Định vị CV hiện tại | Software Engineering Graduate — Python Backend & Applied AI/LLM |
| Deadline MVP             | 20/09/2026                                                       |
| Thời gian thực hiện   | 2–3 giờ/ngày, có thể tăng khi cần                         |
| Người dùng MVP        | Recruiter-only                                                   |
| Job demo                 | AI/ML Engineer                                                   |
| Ngôn ngữ               | CV/JD tiếng Việt và tiếng Anh; UI ưu tiên tiếng Việt     |
| LLM provider             | OpenAI qua abstraction`LLMClient`                              |
| UI                       | Streamlit                                                        |
| Deployment               | Docker Compose local                                             |
| Email                    | Fake outbox                                                      |
| Data                     | Synthetic only trong MVP                                         |
| Gold labels              | Tự gắn nhãn theo rubric                                       |
| Primary metric           | Skill Extraction F1 trên held-out bilingual dataset             |
| Debate                   | Sau MVP; chỉ giữ nếu evaluation chứng minh có ích          |

Thiết kế theo **modular monolith**, chưa dùng microservices. Đây là lựa chọn có chủ đích để giảm độ phức tạp triển khai trong khi vẫn tách module rõ ràng.

Do deadline ngắn, `v0.1.0` tập trung vào đường chạy cốt lõi: upload → extract → deterministic match → parallel review → recruiter interrupt → fake outbox. Candidate Support đầy đủ, Debate và email thật thuộc post-MVP.

## MVP được xem là hoàn thành khi

- Nhận được CV PDF và Job Description.
- Trích xuất hồ sơ ứng viên thành dữ liệu có cấu trúc.
- Đối chiếu tiêu chí bắt buộc bằng rule xác định.
- Chạy hai reviewer song song và merge kết quả bằng Reducer.
- Tạo báo cáo kèm evidence từ CV/JD; không suy đoán dữ liệu không có.
- Dừng tại cổng recruiter review và resume bằng quyết định của con người.
- Chỉ gửi hoặc giả lập gửi phản hồi sau khi được phê duyệt.
- Có test, Docker, README chạy dự án và bộ evaluation nhỏ.

## Nguyên tắc CV

Chỉ ghi TalentAudit là dự án hoàn thành khi luồng MVP chạy end-to-end. Chỉ đưa metric vào CV sau khi evaluation thật đã tạo ra metric đó. Không dùng các con số ước lượng như “giảm hallucination 15–25%”.
