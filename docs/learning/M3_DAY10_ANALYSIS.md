# M3 — Day 10: Chuẩn bị Screening Graph

## 1. Điều kiện bắt đầu

Đây là phân tích, **chưa triển khai M3**. Milestone 2 đã được nghiệm thu, gồm
PostgreSQL 16 theo [báo cáo Day 09](../reports/M2_DAY09_IMPLEMENTATION_REPORT.md).
Day 10 có thể bắt đầu. Giới hạn RAM/sandbox PDF vẫn được theo dõi như hardening;
không quảng bá process riêng thành sandbox đầy đủ.

## 2. Nghiệm thu đầu vào đã hoàn thành

1. Docker Engine và PostgreSQL 16 container tạm đã chạy thành công.
2. Fresh migration, đường upgrade có dữ liệu và repository round-trip đều pass.
3. Container/anonymous volume test đã cleanup; volume dự án không bị tác động.
4. Quality gates pass: 157 tests, Ruff, format và mypy.

## 3. Mục tiêu Day 10 sau nghiệm thu M2

Theo [roadmap](../06_ROADMAP.md), M3 kéo dài 10–12/09: typed state, nodes
validate→parse→extract→match, graph factory, error routing, checkpointer/thread_id
và integration offline. Day 10 nên khóa state/node contracts trước, không cố làm
toàn bộ M3 một lần.

| Thành phần | Cần phân tích/triển khai | Vai trò |
| --- | --- | --- |
| Typed TalentAuditState | ID/hash, status, profile, policy result, errors có kiểu | Node trao đổi dữ liệu rõ ràng, tránh dictionary tùy ý |
| Node input/output | Mỗi node chỉ trả delta, không clone toàn state | Giữ ownership và chuẩn bị reducer đúng ở phase review |
| Service injection | Node gọi validator/parser/extractor/matcher qua dependency | Test không cần OpenAI; business rule không chuyển vào graph |
| Error routing | Parse/extraction failure → NEEDS_REVIEW; không gọi matcher với profile=None | Không biến thiếu bằng chứng thành quyết định loại ứng viên |
| Workflow identity | Chốt thread_id/checkpointer contract, phân biệt in-memory test với PostgreSQL runtime | Chuẩn bị khả năng truy vết/resume, không giả vờ có durability bằng memory |
| Node tests | Happy/failure VI/EN, delta-only, không lộ CV trong lỗi | Chứng minh wiring đúng trước integration toàn graph |

## 4. Cách học và kiểm chứng

Đọc state đề xuất trong `05_STATE_AND_WORKFLOWS.md`, rồi ánh xạ từng field sang DTO
M2 đã có. Viết test node trước khi nối StateGraph. Ví dụ khi extraction trả
NEEDS_REVIEW, state phải có error/status nhưng không được tạo policy result.

Chốt nơi chứa text trong state và cách không log nó; không đưa PDF bytes vào state.
Nếu một collection sẽ được nhiều node cập nhật, phải nêu reducer/deduplication
contract, không chọn reducer chỉ để hết lỗi chạy.

## 5. Checklist đề xuất

- [x] PostgreSQL acceptance của M2 đã pass và có báo cáo.
- [ ] Typed state và node contracts được tài liệu hóa.
- [ ] Nodes tách orchestration khỏi business logic, chỉ trả field cập nhật.
- [ ] Failure không gọi matcher trên profile thiếu/không đáng tin cậy.
- [ ] Unit tests fake VI/EN, safe error và quality gates pass.
- [ ] Viết báo cáo Day 10, phân tích phần graph/checkpointer còn lại cho Day 11.

Không thêm parallel reviewer, HITL endpoint, Streamlit hoặc email trong Day 10.
