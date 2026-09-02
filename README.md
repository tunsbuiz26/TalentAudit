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

| Thành phần | Lựa chọn |
|---|---|
| Ngôn ngữ | Python 3.12 |
| API | FastAPI |
| Orchestration | LangGraph |
| Validation | Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy 2 + Alembic |
| UI MVP | Streamlit |
| Test | pytest |
| Quality | Ruff + mypy |
| Runtime | Docker Compose |
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

## Các quyết định đã khóa — 02/09/2026

| Hạng mục | Quyết định |
|---|---|
| Mục tiêu portfolio | LLM/LangGraph Agent |
| Định vị CV hiện tại | Software Engineering Graduate — Python Backend & Applied AI/LLM |
| Deadline MVP | 20/09/2026 |
| Thời gian thực hiện | 2–3 giờ/ngày, có thể tăng khi cần |
| Người dùng MVP | Recruiter-only |
| Job demo | AI/ML Engineer |
| Ngôn ngữ | CV/JD tiếng Việt và tiếng Anh; UI ưu tiên tiếng Việt |
| LLM provider | OpenAI qua abstraction `LLMClient` |
| UI | Streamlit |
| Deployment | Docker Compose local |
| Email | Fake outbox |
| Data | Synthetic only trong MVP |
| Gold labels | Tự gắn nhãn theo rubric |
| Primary metric | Skill Extraction F1 trên held-out bilingual dataset |
| Debate | Sau MVP; chỉ giữ nếu evaluation chứng minh có ích |

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
