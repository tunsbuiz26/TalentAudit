# 01 — Tóm tắt nội dung cần làm

## 1. Bài toán

Quy trình tuyển dụng có nhiều bước lặp lại: đọc CV, chuẩn hóa thông tin, kiểm tra tiêu chí tối thiểu, ghi nhận nhiều góc nhìn và soạn phản hồi. TalentAudit tự động hóa phần hỗ trợ này nhưng giữ recruiter ở vị trí quyết định cuối cùng.

## 2. Người dùng chính

- **Recruiter:** tạo vị trí tuyển dụng, tải CV, xem báo cáo, phê duyệt/chỉnh sửa phản hồi.
- **Candidate:** gửi CV, đặt câu hỏi về quyền lợi hoặc yêu cầu kỹ thuật, nhận phản hồi đã được duyệt.
- **System administrator:** cấu hình policy, model, prompt version và xem audit log.

MVP có thể gộp recruiter và administrator thành một vai trò nội bộ.

## 3. Bốn năng lực cốt lõi

### A. Candidate Support — Router + specialist

- Phân loại câu hỏi: benefits, technical requirements, interview process hoặc unknown.
- Chuyển đến specialist phù hợp.
- Specialist chỉ đọc nguồn dữ liệu được phép.
- Supervisor tổng hợp hoặc yêu cầu làm rõ khi confidence thấp.

### B. CV Screening — Deterministic pipeline

1. Nhận và kiểm tra file.
2. Trích xuất text và chia section.
3. Chuẩn hóa candidate profile bằng structured output.
4. Trích xuất skill kèm evidence.
5. Chạy rule-based policy matcher.

### C. Structured Review — Parallel review, Debate tùy chọn

- Tech Reviewer đánh giá bằng chứng kỹ thuật.
- Hiring Reviewer đánh giá mức độ đáp ứng yêu cầu công việc và những điểm cần phỏng vấn thêm.
- Hai reviewer ghi kết quả song song vào shared state bằng reducer.
- MVP dùng Judge/Synthesizer để tổng hợp.
- Debate chỉ bật ở phase sau cho hồ sơ borderline và phải có rebuttal thật.

### D. Human-in-the-loop

- Graph dừng trước external side effect.
- Recruiter xem evidence, recommendation và email draft.
- Recruiter chọn Approve, Edit, Reject hoặc Request More Review.
- Chỉ khi Approve, hệ thống mới ghi vào outbox/gửi email.

## 4. Giá trị kỹ thuật cho portfolio

- Thể hiện tư duy chia deterministic logic và LLM logic.
- Có orchestration, state, reducer, persistence và resumability.
- Có dữ liệu có cấu trúc, API, database, test và Docker.
- Có evaluation thay vì chỉ demo prompt.
- Có bảo mật PII, prompt-injection defense và auditability.

## 4.1 Định vị CV đã chọn

Trong giai đoạn hiện tại, headline phù hợp là:

> **Software Engineering Graduate | Python Backend & Applied AI/LLM**

Nhóm vị trí nên ứng tuyển gồm Fresher Software Engineer, Python Backend Engineer và Junior Applied AI Engineer. Sau khi TalentAudit chạy end-to-end và có evaluation thật, có thể tăng trọng tâm sang AI Engineer Fresher. Chưa dùng “LLM Engineer” làm danh xưng chính nếu mới có demo gọi model mà chưa có testing, evaluation và deployment.

Primary portfolio metric của TalentAudit là **Skill Extraction F1 trên held-out bilingual dataset**. Unsupported-claim rate, policy accuracy, latency và cost là các metric bổ trợ.

## 5. Những điều không tuyên bố

- Không nói hệ thống “loại bỏ bias” hoặc “giảm hallucination 15–25%” nếu chưa đo.
- Không gọi hai review độc lập là Debate.
- Không nói “production-ready” nếu chưa có monitoring, security review và deployment ổn định.
- Không ghi metric giả hoặc metric chạy trên quá ít dữ liệu mà không nêu sample size.

## 6. Kết quả cuối dự kiến

- Repository công khai, không chứa dữ liệu cá nhân thật.
- README có kiến trúc, hướng dẫn chạy, demo và giới hạn.
- API + UI MVP chạy bằng Docker Compose.
- Bộ dữ liệu synthetic/anonymized dùng cho evaluation.
- Báo cáo metric và các case thất bại.
- Video demo 2–4 phút.

## 7. Phạm vi deadline 20/09/2026

Với 2–3 giờ/ngày, bản `v0.1.0` ưu tiên pipeline cốt lõi, parallel review, HITL và evaluation nhỏ. Candidate Support đầy đủ và Debate nằm sau deadline. Một router candidate-question tối giản chỉ được thêm khi toàn bộ acceptance criteria cốt lõi đã đạt.
