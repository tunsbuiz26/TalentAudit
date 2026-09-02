# 06 — Roadmap MVP đến 20/09/2026

## 1. Ràng buộc kế hoạch

- Thời gian: 02/09/2026–20/09/2026.
- Năng lực: 2–3 giờ/ngày, khoảng 36–54 giờ.
- Mục tiêu: bản portfolio `v0.1.0` chạy end-to-end bằng Docker local.
- Ưu tiên: core pipeline → parallel review → HITL → evaluation → demo.
- Post-MVP: Candidate Support đầy đủ, Debate, email thật, deployment cloud.

Quy tắc: không chuyển milestone nếu acceptance criteria của milestone trước chưa đạt. Khi chậm lịch, cắt tính năng post-MVP; không cắt approval gate, deterministic policy tests hoặc schema validation.

## 2. Definition of MVP

`v0.1.0` phải làm được:

1. Recruiter tạo AI/ML Engineer job policy.
2. Upload CV PDF/TXT tiếng Việt hoặc tiếng Anh.
3. Extract candidate profile có structured schema và evidence.
4. Chạy deterministic policy matcher.
5. Chạy Tech/Hiring reviewers song song và merge bằng reducer.
6. Synthesizer tạo report và fake email draft.
7. Interrupt để recruiter approve/edit/reject/request one re-review.
8. Chỉ ghi fake outbox sau approve.
9. Chạy evaluation nhỏ và công bố metric thật.

## 3. Sprint calendar

### Evaluation data track — chạy song song từ 06–17/09

- Tạo và tự kiểm tra trung bình 2–3 cặp CV/JD synthetic mỗi ngày.
- Khóa gold skills/policy labels trước khi dùng case đó để chỉnh prompt.
- Đến cuối 17/09 phải đủ 30 cặp; ngày 18/09 chỉ dùng để chạy held-out evaluation và viết report.

### 02–03/09 — Milestone 0: Bootstrap

**Tasks**

- Khởi tạo repository theo `04_PROJECT_STRUCTURE.md`.
- Python 3.12, dependency management, FastAPI app.
- Ruff, mypy, pytest, pre-commit và CI.
- Docker Compose cho app + PostgreSQL.
- `/health`, `/ready`, `.env.example`.

**Acceptance criteria**

- Fresh clone chạy được app và database.
- CI pass.
- Không có secret trong repository.

### 04–05/09 — Milestone 1: Domain và Job Policy

**Tasks**

- Pydantic schemas: Job, Requirement, CandidateProfile, EvidenceRef.
- SQLAlchemy models và migration đầu tiên.
- Job CRUD tối thiểu.
- Deterministic policy matcher.
- Unit tests: required/preferred skills, min years, missing/invalid values.

**Acceptance criteria**

- Policy matcher chạy không cần LangGraph/LLM/network.
- Cùng input luôn cho cùng output.
- Migration chạy được trên database rỗng.

### 06–09/09 — Milestone 2: Document và Extraction

**Tasks**

- File validation: MIME, magic bytes, size và filename.
- PDF/TXT extraction; lưu document hash/metadata.
- `LLMClient` port, OpenAI adapter và fake adapter.
- Structured candidate-profile extraction.
- Detect `vi`/`en`/`mixed`.
- Evidence refs cho skill/experience.
- Tests với prompt injection và schema failure.

**Acceptance criteria**

- Parse được ít nhất 5 CV VI và 5 CV EN synthetic.
- Skill quan trọng có evidence hoặc `UNKNOWN`.
- Output sai schema retry có giới hạn rồi chuyển review.

### 10–12/09 — Milestone 3: Screening Graph

**Tasks**

- Typed `TalentAuditState`.
- Nodes validate → parse → extract → match.
- Graph factory, error routing, checkpointer và `thread_id`.
- Node unit tests bằng fake services.
- Integration test không gọi OpenAI thật.

**Acceptance criteria**

- Pipeline end-to-end tạo policy result.
- Workflow status và lỗi được trace không lộ PII.
- Có test cho CV VI và EN.

### 13–15/09 — Milestone 4: Parallel Review

**Tasks**

- Tech/Hiring rubric v1 cho AI/ML Engineer.
- Structured ReviewOpinion schema.
- Chạy hai reviewer song song.
- Reducer merge delta; chống duplicate khi retry.
- Deterministic weighted score.
- Synthesizer + evidence validator + email draft.

**Acceptance criteria**

- Không reviewer nào ghi đè reviewer còn lại.
- Tối đa một opinion/reviewer/round.
- Report phân biệt fact, inference và unknown.
- Không sử dụng thuộc tính nhạy cảm.

### 16–17/09 — Milestone 5: HITL và Streamlit

**Tasks**

- `interrupt()` payload và resume endpoint/service.
- Streamlit: upload, status, report, evidence, decision form.
- Approve/edit/reject/request one re-review.
- Recruiter decision record.
- Fake email outbox + idempotency key.

**Acceptance criteria**

- Không có outbox trước approve.
- Resume đúng audit bằng cùng `thread_id`.
- Submit lặp không tạo hai outbox messages.
- Restart app vẫn resume được.

### 18/09 — Milestone 6: Evaluation

**Tasks**

- Hoàn thiện 30 cặp CV/JD synthetic: 15 VI, 15 EN.
- Gold labels cho skills và policy results.
- Development/held-out split.
- Chạy Skill Extraction Precision/Recall/F1.
- Đo unsupported-claim rate, latency và token/cost.
- Ghi model, prompt, schema và dataset version.

**Acceptance criteria**

- Evaluation chạy lại được bằng một command.
- Report có sample size, metric theo ngôn ngữ và failure cases.
- Không có metric viết tay.

### 19/09 — Milestone 7: Portfolio packaging

**Tasks**

- README công khai: problem, architecture, setup, trade-offs.
- Seed demo data không có PII.
- Screenshots và video demo 2–4 phút.
- Docker smoke test trên môi trường sạch.
- Viết CV bullets bằng metric đã xác minh.

**Acceptance criteria**

- Người khác chạy được theo README.
- Demo thể hiện pipeline, reducer và HITL.
- Repository không chứa secret/CV thật.

### 20/09 — Release buffer

- Chỉ sửa blocker, test failure, setup instructions và demo issue.
- Tag `v0.1.0` khi quality gates pass.
- Không thêm tính năng mới trong ngày release.

## 4. Scope-cut order nếu chậm lịch

Cắt theo đúng thứ tự:

1. UI styling nâng cao.
2. Candidate question router tối giản.
3. PostgreSQL persistence cho dữ liệu phụ; giữ graph checkpoint và core records.
4. Report visualization không bắt buộc.

Không cắt:

- Human approval trước side effect.
- Deterministic policy matcher.
- Reducer test.
- Schema validation.
- Fake outbox/idempotency.
- Ít nhất một held-out evaluation run.

## 5. Post-MVP backlog

### v0.2 — Candidate Support

- Benefits/tech requirements knowledge base.
- Intent router + confidence threshold.
- Specialist workers + source references + escalation.

### v0.3 — Debate experiment

- Borderline routing.
- Một vòng rebuttal thật.
- So sánh quality/cost/latency với Parallel Review.
- Chỉ bật mặc định nếu evaluation chứng minh có ích.

### v0.4 — Production-like hardening

- Authentication/RBAC.
- S3-compatible storage.
- Email sandbox/real adapter.
- Cloud deployment và monitoring.
- Retention/delete workflow.

## 6. Task đầu tiên giao cho Codex

```text
Đọc AGENTS.md và docs/02_REQUIREMENTS.md, docs/03_ARCHITECTURE.md,
docs/04_PROJECT_STRUCTURE.md, docs/06_ROADMAP.md.

Chỉ thực hiện Milestone 0:
- scaffold repository Python 3.12;
- FastAPI health/readiness;
- settings và .env.example;
- Ruff, mypy, pytest;
- Docker Compose app + PostgreSQL;
- CI;
- README setup tối thiểu.

Không implement LangGraph nodes, UI hoặc OpenAI trong task này.
Chạy quality checks và báo cáo kết quả.
```
