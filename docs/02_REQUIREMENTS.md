# 02 — Yêu cầu và phạm vi

## 1. MVP scope

### 1.1 Functional requirements

| ID | Yêu cầu | Mức ưu tiên |
|---|---|---|
| FR-01 | Recruiter tạo Job Description và tiêu chí bắt buộc | Must |
| FR-02 | Upload CV PDF/TXT hợp lệ | Must |
| FR-03 | Extract text và candidate profile có cấu trúc | Must |
| FR-04 | Extract skills, kinh nghiệm và evidence | Must |
| FR-05 | Policy matcher chạy bằng rule xác định | Must |
| FR-06 | Tech và Hiring reviewer chạy song song | Must |
| FR-07 | Synthesizer tạo báo cáo và email draft | Must |
| FR-08 | Workflow interrupt trước khi gửi phản hồi | Must |
| FR-09 | Recruiter approve/edit/reject/resume workflow | Must |
| FR-10 | Lưu audit trail và workflow status | Must |
| FR-11 | Candidate hỏi về benefits/tech requirements | Should, sau `v0.1.0` |
| FR-12 | Debate round cho hồ sơ borderline | Could, sau `v0.1.0` |
| FR-13 | Gửi email thật | Could, sau khi fake outbox ổn định |

### 1.2 Non-functional requirements

- **Explainability:** mọi đánh giá quan trọng phải có evidence.
- **Reliability:** resume được sau interrupt và lỗi transient.
- **Security:** validate file, hạn chế kích thước, không log PII, secret chỉ qua environment.
- **Testability:** business rule chạy không cần network/LLM thật.
- **Observability:** có `request_id`, `workflow_id`, `node_name`, latency và error code.
- **Maintainability:** module boundaries rõ, prompt versioned, migration versioned.
- **Cost control:** giới hạn số token, số vòng review và model được dùng.
- **Bilingual input:** chấp nhận CV/JD tiếng Việt và tiếng Anh; lưu language metadata cho evaluation.

## 1.3 Product decisions đã khóa

- Người dùng `v0.1.0`: recruiter-only.
- Job demo: AI/ML Engineer.
- UI: Streamlit, ưu tiên tiếng Việt.
- LLM: OpenAI qua provider abstraction.
- Deployment: Docker Compose local.
- Email: fake outbox.
- Data: synthetic; không dùng CV thật trong repository/demo.
- Recruiter nhập hoặc xác nhận required skills, preferred skills và min years.
- Ứng viên không đạt hard rule vẫn được tạo report và chờ recruiter.
- Recruiter chỉ yêu cầu review lại tối đa một lần.

## 2. Out of scope cho MVP

- ATS hoàn chỉnh, payroll hoặc employee management.
- Tự động tìm ứng viên trên mạng xã hội.
- Face analysis, emotion analysis hoặc personality inference.
- Tự động quyết định tuyển/loại mà không có người duyệt.
- Microservices, Kubernetes hoặc event streaming phức tạp.
- Fine-tuning model.
- OCR chất lượng cao cho mọi mẫu CV scan; MVP có thể từ chối file không đọc được.

## 3. Core use cases

### UC-01: Audit một CV

1. Recruiter chọn job và upload CV.
2. Hệ thống validate file, extract text và chuẩn hóa profile.
3. Policy matcher trả kết quả cùng lý do.
4. Reviewer tạo opinion độc lập.
5. Synthesizer tạo report và draft.
6. Graph interrupt.
7. Recruiter approve/edit/reject.
8. Workflow lưu quyết định và kết thúc hoặc ghi email vào outbox.

### UC-02: Hỏi thông tin tuyển dụng

1. Candidate gửi câu hỏi.
2. Router phân loại intent và confidence.
3. Specialist truy xuất nguồn thông tin tương ứng.
4. Nếu confidence thấp hoặc thiếu dữ liệu, hệ thống yêu cầu làm rõ/chuyển recruiter.
5. Candidate nhận câu trả lời có nguồn.

### UC-03: Resume sau HITL

1. Recruiter mở workflow ở trạng thái `WAITING_FOR_REVIEW`.
2. Hệ thống dùng cùng `thread_id`.
3. Recruiter gửi decision payload hợp lệ.
4. Graph tiếp tục tại approval node.
5. Side effect chỉ chạy nếu decision cho phép.

## 4. Acceptance criteria cấp hệ thống

- Không có external side effect trước approval.
- Cùng một input rule-based tạo cùng một kết quả.
- Hai reviewer không ghi đè opinion của nhau.
- Nếu LLM output sai schema, workflow retry có giới hạn rồi chuyển `NEEDS_REVIEW`.
- Nếu CV chứa “ignore previous instructions”, nội dung đó được coi là dữ liệu CV, không phải lệnh.
- Báo cáo không sử dụng thuộc tính nhạy cảm.
- Có thể trace recommendation về đoạn evidence nguồn.
- Toàn bộ happy path chạy được từ một lệnh Docker Compose.
- Cùng bộ test phải có ít nhất một CV tiếng Việt và một CV tiếng Anh chạy end-to-end.

## 5. Status model

```text
CREATED
  -> VALIDATING
  -> PARSING
  -> MATCHING
  -> REVIEWING
  -> WAITING_FOR_RECRUITER
  -> APPROVED | EDIT_REQUIRED | REJECTED
  -> COMPLETED | FAILED | NEEDS_REVIEW
```

Không dùng `REJECTED` để ngầm hiểu ứng viên bị loại. Trong domain workflow, nó có nghĩa recruiter từ chối **đề xuất/draft của AI**; quyết định ứng viên cần field riêng và do recruiter nhập.
