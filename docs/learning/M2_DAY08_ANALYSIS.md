# M2 — Day 08: LLMClient và structured profile extraction

## 1. Mục tiêu và phạm vi

Theo [kế hoạch M2](../milestones/02_DOCUMENT_AND_EXTRACTION_PLAN.md), ngày 08 chuyển
`ParsedDocument` của ngày 07 thành `CandidateProfile` có bằng chứng, không quyết định
tuyển dụng. Không thêm endpoint, LangGraph, reviewer hoặc thay đổi policy matcher.

## 2. Các phần cần làm và vì sao

| Thành phần | Công việc | Vai trò / tác dụng |
| --- | --- | --- |
| `ports/llm.py` | Generic `generate_structured` nhận prompt/version, dữ liệu và model Pydantic | Service không phụ thuộc provider; thay fake/OpenAI mà không đổi nghiệp vụ |
| `schemas/llm.py` | Prompt và untrusted input riêng | Giữ instruction đáng tin cậy tách khỏi nội dung CV |
| Settings | Key dạng SecretStr, model, temperature, token limit, timeout | Cấu hình runtime tập trung; fake không cần key |
| `adapters/llm/openai.py` | Responses structured outputs | Nơi duy nhất trong source import SDK; không tự quyết retry nghiệp vụ |
| `adapters/llm/fake.py` | Hàng đợi JSON hoặc typed exception | Chủ động tái hiện thành công/lỗi, không network |
| Prompt v1 | Instruction cố định và input được đóng delimiter | CV là dữ liệu; không làm theo lệnh nhúng, không suy luận thuộc tính nhạy cảm |
| Extraction DTO | Claim kỹ năng/năm có evidence riêng | Tránh danh sách evidence phẳng không biết chứng minh claim nào |
| Evidence validator | Kiểm document ID, bounds, quote bằng text slice | Chặn evidence không tồn tại; không chỉnh text hay offsets |
| Extractor | Validate rồi chuyển DTO sang profile; retry schema một lần | Chỉ trả profile sử dụng được khi qua kiểm tra, nếu không NEEDS_REVIEW |

## 3. Contract và quyết định triển khai

- Không thay contract matcher M1. Bổ sung `skill_evidence` và `experience_evidence`
  vào CandidateProfile, mặc định rỗng để tương thích dữ liệu cũ.
- Wire output dùng danh sách claim thay dictionary có key động, phù hợp strict
  JSON Schema của provider. Claim gồm skill, status KNOWN/UNKNOWN, years nullable,
  evidence cho skill và years. UNKNOWN không mang giá trị năm được đoán.
- Trường required nhưng nullable thể hiện thiếu số năm; không biến thiếu thành 0.
- Claim UNKNOWN, thiếu evidence hoặc evidence sai: toàn bộ outcome NEEDS_REVIEW,
  không cung cấp profile cho matcher. Đây là lựa chọn bảo thủ để tránh dữ liệu thiếu
  bị hiểu thành ứng viên không có kỹ năng.
- Schema failure: tối đa hai lần gọi tổng cộng. Evidence failure, refusal, incomplete,
  timeout/provider failure: không retry. SDK retry bị tắt để không nhân số request.
- OpenAI model phải được chọn bằng environment trước khi dùng adapter thật; không
  chọn ngầm model. Không cần key để khởi động app hoặc chạy fake.
- Quote giữ nguyên whitespace/Unicode, offsets là Python character index, end exclusive.
- Request không lưu response ở provider (`store=False`); điều này không phải cam kết
  zero retention. Không log CV, key hoặc thông báo lỗi thô từ provider/Pydantic.

## 4. Cách kiểm chứng

Test generic fake với nhiều output model; schema invalid→valid và invalid→invalid;
UNKNOWN; thiếu/sai evidence; năm âm; quote VI/EN và whitespace; lỗi provider;
contract OpenAI dùng mock, không gọi API; kiểm SDK import boundary và prompt đóng gói.
Chạy Ruff, format check, mypy và toàn bộ pytest.

Fake chỉ chứng minh wiring/control flow, không chứng minh model thật chống prompt
injection hoặc đạt Skill Extraction F1. Quote khớp nguồn không đủ chứng minh claim
đúng ngữ nghĩa. Không công bố metric chưa đo.

## 5. Việc còn theo dõi

Day 07 còn hard timeout/resource isolation và persistence metadata parser; không
âm thầm coi đã xong. Day 09 bổ sung regression sâu, chạy 10 fixture VI/EN qua
parse/extraction fake và manifest/hash. M2 chưa hoàn tất chỉ vì Day 08 pass.

Tham khảo triển khai adapter: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
