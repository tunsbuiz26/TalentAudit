# 04 — Cấu trúc source code đề xuất

```text
talentaudit/
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── alembic.ini
├── docs/
│   ├── 01_PROJECT_SUMMARY.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_ARCHITECTURE.md
│   ├── 04_PROJECT_STRUCTURE.md
│   ├── 05_STATE_AND_WORKFLOWS.md
│   ├── 06_ROADMAP.md
│   ├── 07_EVALUATION_SECURITY.md
│   ├── 08_PROJECT_INTERVIEW.md
│   └── adr/
├── migrations/
│   └── versions/
├── src/
│   └── talentaudit/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── dependencies.py
│       │   ├── errors.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── jobs.py
│       │       ├── audits.py
│       │       └── questions.py
│       ├── application/
│       │   ├── commands/
│       │   ├── queries/
│       │   └── services/
│       ├── domain/
│       │   ├── entities/
│       │   ├── enums.py
│       │   ├── exceptions.py
│       │   ├── policies/
│       │   └── rubrics/
│       ├── schemas/
│       │   ├── api.py
│       │   ├── candidate.py
│       │   ├── job.py
│       │   ├── review.py
│       │   └── workflow.py
│       ├── workflows/
│       │   ├── state.py
│       │   ├── routing.py
│       │   ├── graph.py
│       │   ├── nodes/
│       │   │   ├── validate.py
│       │   │   ├── parse_cv.py
│       │   │   ├── extract_profile.py
│       │   │   ├── match_policy.py
│       │   │   ├── review_tech.py
│       │   │   ├── review_hiring.py
│       │   │   ├── rebuttal.py
│       │   │   ├── synthesize.py
│       │   │   ├── human_review.py
│       │   │   └── enqueue_email.py
│       │   └── subgraphs/
│       │       └── candidate_support.py
│       ├── services/
│       │   ├── document_parser.py
│       │   ├── profile_extractor.py
│       │   ├── evidence_service.py
│       │   └── report_service.py
│       ├── ports/
│       │   ├── llm.py
│       │   ├── repositories.py
│       │   ├── storage.py
│       │   └── email.py
│       ├── adapters/
│       │   ├── db/
│       │   ├── llm/
│       │   ├── storage/
│       │   └── email/
│       ├── prompts/
│       │   ├── profile_extractor_v1.md
│       │   ├── tech_reviewer_v1.md
│       │   ├── hiring_reviewer_v1.md
│       │   └── synthesizer_v1.md
│       └── observability/
│           ├── logging.py
│           └── metrics.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── workflow/
│   └── fixtures/
├── evals/
│   ├── datasets/
│   ├── graders/
│   ├── run_eval.py
│   └── reports/
├── scripts/
│   ├── seed_demo_data.py
│   └── create_synthetic_dataset.py
└── ui/
    └── streamlit_app.py
```

## Quy tắc đặt code

- HTTP-specific code chỉ nằm trong `api`.
- LangGraph node mỏng: đọc state, gọi service, trả state delta.
- Policy matcher nằm trong `domain/policies`, không nằm trong prompt.
- Interface với dịch vụ ngoài nằm trong `ports`; implementation nằm trong `adapters`.
- Pydantic schemas dùng chung phải có version khi lưu lâu dài.
- `evals` không trộn với `tests`: test kiểm tra code đúng; eval đo AI hoạt động tốt đến đâu.
- Prompt là source-controlled artifact, không hard-code trong node.

## Dependency direction

```text
api -> application -> domain
workflows -> application/domain/ports
adapters -> ports/domain
domain -> standard library only (ưu tiên)
```

Domain không được import ngược lại từ FastAPI, Streamlit, LangGraph hay SDK provider.

## Tách package khi nào?

Chưa tách package/microservice trong MVP. Chỉ xem xét tách khi có bằng chứng:

- Worker xử lý document cần scale khác API.
- Email/outbox cần process riêng.
- Team ownership hoặc deployment lifecycle khác nhau.
- Performance measurement cho thấy một boundary cần độc lập.

