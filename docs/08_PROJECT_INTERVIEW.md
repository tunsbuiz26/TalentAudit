# 08 — Project decisions đã khóa

Ngày cập nhật: **02/09/2026**

File này ghi lại câu trả lời phỏng vấn và các quyết định đã được giải quyết để Codex không hỏi lại hoặc tự thay đổi phạm vi.

## A. Mục tiêu portfolio

| Câu hỏi | Quyết định |
|---|---|
| Năng lực ưu tiên | LLM/LangGraph Agent |
| Nền tảng cá nhân | Software Engineering, đang phát triển năng lực Applied AI/LLM |
| Headline CV phù hợp hiện tại | **Software Engineering Graduate \| Python Backend & Applied AI/LLM** |
| Vai trò mục tiêu | Fresher Software Engineer, Python Backend Engineer, Junior Applied AI Engineer |
| Deadline MVP | 20/09/2026 |
| Thời gian mỗi ngày | 2–3 giờ, có thể tăng khi cần |

Không dùng “LLM Engineer” làm danh xưng chính trước khi dự án có evaluation và luồng end-to-end. Sau `v0.1.0`, có thể điều chỉnh headline theo chất lượng kết quả thực tế.

## B. Product scope

| Câu hỏi | Quyết định |
|---|---|
| User MVP | Recruiter-only |
| Job demo | AI/ML Engineer |
| CV/JD | Tiếng Việt và tiếng Anh |
| UI language | Ưu tiên tiếng Việt |
| Candidate account | Không có trong MVP |
| Candidate Support | Post-MVP; chỉ thêm router tối giản nếu còn thời gian |
| Debate | Post-MVP, cần rebuttal thật và evaluation |

## C. Technical choices

| Thành phần | Quyết định |
|---|---|
| LLM provider | OpenAI |
| Provider design | `LLMClient` abstraction; một OpenAI adapter trong MVP |
| API | FastAPI |
| UI | Streamlit |
| Database | PostgreSQL |
| Deployment | Docker Compose local |
| Email | Fake outbox |
| Architecture | Modular monolith |

## D. Data và evaluation

| Câu hỏi | Quyết định |
|---|---|
| Dataset | Synthetic only trong MVP |
| Gold labels | Tự gắn nhãn theo rubric |
| Primary metric | **Skill Extraction F1 trên held-out bilingual dataset** |
| Secondary metrics | Unsupported-claim rate, policy accuracy, latency, cost |
| Minimum dataset | 30 CV/JD pairs: 15 VI, 15 EN |

Primary metric được chọn vì có gold labels rõ ràng, phù hợp bài toán mất cân bằng skill và dễ giải thích khi phỏng vấn. Không ghi một con số vào CV trước khi evaluation thật được chạy.

## E. Recruiter policy

| Câu hỏi | Quyết định |
|---|---|
| Job requirements | Recruiter nhập/xác nhận thủ công |
| Không đạt hard rule | Vẫn tạo report và chờ recruiter |
| Re-review limit | Tối đa một lần |
| Final candidate decision | Human recruiter only |
| External side effect | Chỉ sau approval |

## F. Resolved assumptions

- Deadline được hiểu là **20/09/2026** theo thời điểm lập kế hoạch.
- “Song ngữ” nghĩa là chấp nhận cả CV/JD VI và EN, dùng schema chung và báo cáo metric tách theo ngôn ngữ.
- Deadline 18 ngày không đủ để hoàn thiện cả ba pattern ở mức production-like. `v0.1.0` tập trung Pipeline, Parallel Review và HITL; Router/Supervisor-Worker đầy đủ cùng Debate chuyển sang version sau.
- Candidate Support và Debate vẫn nằm trong product vision, không bị loại khỏi toàn dự án.

## G. Change-control rule

Nếu muốn thay đổi một quyết định trong file này:

1. Ghi rõ quyết định cũ và mới.
2. Nêu ảnh hưởng tới deadline, architecture và tests.
3. Cập nhật các tài liệu liên quan.
4. Chỉ triển khai sau khi người dùng xác nhận thay đổi phạm vi.

