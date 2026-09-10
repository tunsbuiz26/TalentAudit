# M2 — Day 09: Evidence, security regression và acceptance run

## 1. Mục tiêu

Khóa chất lượng của đường chạy `validate → parse → extract → evidence validation`
trước khi nối workflow ở M3. Phần code, test offline và migration PostgreSQL đã
được kiểm chứng. Xem [báo cáo Day 09](../reports/M2_DAY09_IMPLEMENTATION_REPORT.md).
Tham chiếu [plan M2](../milestones/02_DOCUMENT_AND_EXTRACTION_PLAN.md)
và [báo cáo Day 08](../reports/M2_DAY08_IMPLEMENTATION_REPORT.md).

## 2. Đầu vào đã có

- Day 06: validation, local storage, metadata/hash persistence.
- Day 07: TXT/PDF parsing, language detection, 5 fixture VI và 5 EN.
- Day 08: port/fake/OpenAI, prompt v1, typed outcomes, một schema retry,
  mapping `skill_evidence` / `experience_evidence`, kiểm bounds/quote/document ID.
- Đã có test retry, UNKNOWN, missing evidence, delimiter escape và SDK mock.
  Không viết lại phần đã có; mở rộng regression ở những tình huống thiếu.

## 3. Công việc và ý nghĩa từng phần

| Phần | Cần làm | Tác dụng |
| --- | --- | --- |
| Evidence regression | Thêm span âm/đảo/zero, Unicode tổ hợp, nhiều claim, evidence bị lấy từ claim khác | Tránh sai offset, gán evidence nhầm hoặc mất dữ liệu ngôn ngữ |
| UNKNOWN và matcher boundary | Chứng minh profile bị review không đi tới matcher; năm thiếu không thành 0; còn claim tốt không che mất claim xấu | Tránh thiếu bằng chứng bị hiểu thành PASS/FAIL tuyển dụng |
| Prompt injection regression | CV VI/EN chứa lệnh đổi role/schema, đóng delimiter, yêu cầu bỏ evidence | Kiểm dữ liệu không sửa prompt, retry budget hoặc policy; không tuyên bố fake chứng minh model thật an toàn |
| Integration 10 fixtures | Mỗi fixture đi qua validator/parser/extractor fake với response được gắn nhãn trước | Kiểm các module kết nối đúng, không chỉ từng unit riêng lẻ |
| Manifest/hash | Lưu đường dẫn, SHA-256 bytes, language, provenance synthetic và kỳ vọng claim/parse status | Phát hiện fixture thay đổi, giúp người khác tái hiện regression |
| Kiểm tra an toàn | Chặn network trong test, không log text/response/key, SDK import boundary, không thêm thuộc tính nhạy cảm | Giữ trust boundary và phạm vi MVP |
| Acceptance run | Ruff/format/mypy/pytest và đối chiếu từng acceptance criterion | Có bằng chứng thực tế, không chỉ checklist được đánh dấu |

## 4. Hai việc tồn từ Day 07 phải được xử lý hoặc ghi rõ đang chặn

### 4.1 Timeout cứng / resource isolation cho parser

Hiện parser có byte/page/character limit nhưng không thể dừng một phép parse bị treo.
Cần thiết kế `document_parse_timeout_seconds` qua Settings và boundary có thể
terminate công việc, không dùng timeout thread rồi để worker tiếp tục chạy vô hạn.
Đánh giá process worker tương thích Windows/Docker và typed timeout failure.

Test tối thiểu: parser chậm bị dừng, trả code ổn định, cleanup worker, không lưu
partial text thành kết quả thành công; happy path không làm đổi document ID/hash.
Timeout OpenAI của Day 08 **không giải quyết** timeout PDF này.

### 4.2 Persistence metadata sau parse

Bảng documents mới lưu metadata upload/hash. Cần migration/repository cập nhật
`parser_status`, `document_language`, `page_count` theo contract của plan M2.
Database không chứa raw bytes/CV text. Parse failure không được đánh dấu parsed.

Test migration trên PostgreSQL rỗng riêng biệt, không xóa database đang dùng; test
cập nhật thành công/thất bại và nullability. Nếu cần bật Docker Desktop, thông báo
người dùng theo yêu cầu đã có. Không xóa volume hoặc reset database để chạy test.

## 5. Thứ tự triển khai đề xuất

1. Kiểm repo, đọc source of truth, xác nhận backlog Day 07 và phạm vi nghiệm thu.
2. Bổ sung regression dựa trên Day 08, ghi rõ provenance khác semantic correctness.
3. Thêm expected fake outputs cho 10 fixture và manifest/hash; không gọi OpenAI.
4. Giải quyết timeout/parser metadata trong phần tồn M2; chạy test/migration phù hợp.
5. Chạy toàn bộ quality gates, đối chiếu plan M2 và viết báo cáo Day 09 trong
   `docs/reports/`; phân tích công việc kế tiếp chỉ khi biết tiêu chí nào đã pass.

## 6. Checklist nghiệm thu dự kiến

- [x] 10 fixture VI/EN parse và extraction fake chạy end-to-end, có manifest/hash.
- [x] Thiếu/sai evidence hoặc UNKNOWN trả profile=None; chưa nối matcher/workflow ở M2.
- [x] Schema invalid→valid và invalid→invalid vẫn giữ trần hai request.
- [x] Prompt/data boundary và no-network/no-raw-log có regression offline.
- [x] PDF worker có timeout/kill/reap test; chưa có hard RAM cap hoặc OS sandbox.
- [x] Parser metadata migration chạy trên PostgreSQL rỗng và giữ dữ liệu khi nâng cấp.
- [x] Ruff, format, mypy, pytest pass: 157 tests; đã cập nhật báo cáo.

Migration đã chạy trên SQLite tạm và PostgreSQL 16 tạm: fresh upgrade, downgrade
về 0002, chèn dữ liệu synthetic, upgrade lại và repository round-trip đều pass.
Container/anonymous volume test đã được dọn. Worker riêng không được quảng bá
thành sandbox chống khai thác PDF. Evidence có lexical guard: tên skill phải
xuất hiện trong ít nhất một quote đã kiểm chứng; alias chưa có taxonomy sẽ cần
review. Guard không xác minh phủ định hoặc tính đúng ngữ nghĩa của duration.

## 7. Không thuộc ngày này

Không thêm audit/upload endpoint, LangGraph, parallel reviewer, recruiter approval
hay email. Fake fixtures là development/regression data, **không phải held-out**;
không tính Skill Extraction F1 từ output đã lập trình sẵn. Evaluation với model thật
và dữ liệu held-out thuộc phần đánh giá theo roadmap, cần lựa chọn model và cấu hình
riêng trước khi phát sinh request/chi phí.
