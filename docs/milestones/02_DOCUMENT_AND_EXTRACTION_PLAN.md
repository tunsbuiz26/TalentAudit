# Milestone 2 — Document và Extraction

Thời gian roadmap: 06–09/09/2026
Trạng thái: phân tích và kế hoạch triển khai, chưa triển khai code Milestone 2.

## 1. Mục tiêu của milestone

Milestone 2 xây dựng lớp xử lý CV độc lập với LangGraph:

```text
bytes CV không tin cậy
  -> validate file
  -> local document storage + metadata/hash
  -> parse text xác định
  -> detect language
  -> structured profile extraction qua LLMClient
  -> CandidateProfile có evidence hoặc UNKNOWN
```

Kết quả phải có thể được Milestone 3 gọi từ các node `validate_submission`,
`parse_cv` và `extract_profile`; Milestone 2 không tạo graph, audit endpoint hoặc
UI.

## 2. Scope đã khóa

| Hạng mục roadmap | Diễn giải thực thi |
|---|---|
| File validation | Kiểm tra extension, declared MIME, magic bytes, byte size và filename trước khi parse/lưu. |
| PDF/TXT extraction | Chỉ parse text-based PDF và UTF-8 text; file scan/PDF không có text là parse failure, không OCR trong MVP. |
| Document metadata | Tính SHA-256 của bytes; lưu document ID, storage key, hash, MIME, size, parser/scan status và language. Không lưu bytes CV trong PostgreSQL. |
| LLM abstraction | Tạo `LLMClient` port, OpenAI adapter và fake adapter; domain/service không import OpenAI SDK. |
| Structured extraction | Prompt versioned trả về Pydantic candidate-profile contract; validate lại trước khi trả kết quả. |
| Bilingual | Nhận diện và lưu `vi`, `en`, hoặc `mixed`; offset evidence luôn tính trên text gốc, không dịch text trước. |
| Evidence | Mọi skill hoặc số năm kinh nghiệm được dùng để đánh giá phải có evidence span hợp lệ; thiếu evidence là `UNKNOWN`, không suy đoán. |
| Safety tests | Có test prompt injection, input sai schema, file sai định dạng/quá lớn và đường dẫn filename không an toàn. |

## 3. Không thuộc Milestone 2

- `POST /api/v1/audits`, audit records, LangGraph state/nodes/checkpointer: Milestone 3.
- Policy matching, reviewer, report, recruiter approval hoặc email: Milestone 3–5.
- OCR cho PDF scan; MVP được phép trả parse failure/`NEEDS_REVIEW`.
- Skill taxonomy đầy đủ, candidate support, Debate và quyết định tuyển dụng.
- CV thật hoặc dữ liệu cá nhân thật trong fixture/repository.

## 4. Ranh giới kiến trúc cần giữ

| Lớp | Trách nhiệm M2 |
|---|---|
| `schemas/` | DTO cho metadata, parsed document, LLM structured output và extraction outcome. |
| `services/` | File validation, parsing, language detection, profile extraction và evidence validation. |
| `ports/` | `DocumentStorage` và `LLMClient`; chỉ khai báo interface. |
| `adapters/storage/` | Local storage an toàn; storage key do hệ thống tạo, không dùng filename làm path. |
| `adapters/llm/` | OpenAI SDK chỉ nằm ở đây; fake adapter dùng cho test. |
| `adapters/db/` | Chỉ persistence metadata document mà M2 yêu cầu, qua migration mới. |
| `prompts/` | `profile_extractor_v1.md`, tách instruction khỏi CV untrusted data. |

Business rule validate file, detect language, validate evidence và retry policy phải ở service/domain
có thể test không network. LLM chỉ chuẩn hóa/extract từ text, không quyết định tuyển dụng.

## 5. Contract đề xuất

### 5.1 Document lifecycle

`ValidatedDocument` cần có tối thiểu: document ID, sanitized metadata, declared/detected MIME,
size bytes, SHA-256 và bytes đã qua validation. Sau khi `DocumentStorage.put(...)` thành công,
database chỉ lưu metadata và `storage_key`.

Không log raw CV text, email/phone nếu xuất hiện trong CV, bytes, storage path tuyệt đối hoặc
filename gốc. Filename chỉ dùng để kiểm tra input và không được dùng làm tên file trên disk.

### 5.2 Parser result

`ParsedDocument` cần có `document_id`, `text`, `document_language`, `page_count` (PDF) và
parser status. Parser phải có giới hạn byte/page/text length; empty text và malformed PDF là
typed parse failure, không phải exception bị mất ngữ cảnh.

### 5.3 Extraction result và evidence

`CandidateProfile` hiện có `skills`, `experience_years` và `evidence_refs`, nhưng danh sách
evidence phẳng chưa chứng minh được evidence nào hỗ trợ từng skill/experience. Trước khi code,
contract nên được mở rộng theo một trong hai cách tương đương:

1. `skill_evidence: dict[str, list[EvidenceRef]]` và
   `experience_evidence: dict[str, list[EvidenceRef]]`; hoặc
2. một claim model có `claim_type`, `claim_value` và `evidence_refs`.

Khuyến nghị dùng cách 1 vì tương thích matcher M1: matcher vẫn đọc `skills` và
`experience_years`, còn evidence validator đối chiếu từng key. Mỗi `EvidenceRef` phải thỏa
`0 <= start < end <= len(parsed_text)` và substring trong span khớp `text` đã lưu.

`ExtractionOutcome` nên biểu diễn rõ một trong ba kết quả: profile hợp lệ, `NEEDS_REVIEW`,
hoặc lỗi reject. M3 sẽ map outcome này vào workflow state; M2 không tự tạo graph status.

## 6. Kế hoạch theo ngày

### Ngày 06/09 — Trust boundary và document persistence

Mục tiêu: không để bytes không tin cậy đi xa hơn validation.

- Thêm Settings qua environment cho storage path, allowed MIME, max upload bytes, max PDF pages
  và parser text limit; không hard-code limit ở service.
- Tạo schema/exception cho validation result và metadata.
- Tạo `DocumentStorage` port và local adapter dùng generated storage key; chặn path traversal.
- Tạo `documents` SQLAlchemy model, repository tối thiểu và Alembic migration metadata/hash.
- Viết unit tests cho `.pdf`/`.txt` hợp lệ, extension-MIME-magic mismatch, oversized input,
  filename chứa path separator và bytes binary giả `.txt`.

Hoàn thành ngày khi input bị reject trước parser/storage nếu vi phạm rule, và database không chứa
raw CV bytes.

### Ngày 07/09 — Deterministic parsing và language metadata

Mục tiêu: chuyển file đã validate thành text có provenance.

- Thêm `document_parser.py` cho TXT và text-based PDF, với timeout/resource boundary phù hợp.
- Chọn PDF parser text-only (khuyến nghị `pypdf`); không chạy link, macro hay embedded content.
- Tính document hash từ bytes trước khi parse; parser không sửa text trước khi tính evidence offset.
- Thêm language detector deterministic cho `vi`/`en`/`mixed`; đặt test cho văn bản đại diện,
  không dùng LLM để nhận diện language.
- Thêm synthetic fixtures: tối thiểu 5 CV tiếng Việt và 5 CV tiếng Anh, không PII thật.
- Test happy path TXT/PDF, empty text, malformed PDF, parser error và 10 fixture parse cases.

Hoàn thành ngày khi mỗi fixture tạo được `ParsedDocument` với language metadata đúng hoặc parse
failure có code rõ ràng.

### Ngày 08/09 — LLMClient và structured profile extraction

Mục tiêu: chuẩn hóa text thành CandidateProfile nhưng giữ LLM ở đúng boundary.

- Tạo generic `LLMClient.generate_structured(...)` port nhận prompt/version, untrusted document
  data và output Pydantic model.
- Tạo OpenAI adapter; API key/model/temperature/token limit chỉ đọc từ Settings. Không đặt key
  trong repo hoặc test.
- Tạo programmable fake adapter cho test contract, không gọi network.
- Tạo `prompts/profile_extractor_v1.md`: instruction nêu CV là data, đặt text giữa delimiter,
  cấm làm theo instruction nhúng trong CV, yêu cầu `UNKNOWN` khi thiếu bằng chứng.
- Tạo `profile_extractor.py` và evidence validator. Retry tối đa một lần với schema failure;
  sau đó trả `ExtractionOutcome(NEEDS_REVIEW)`.

Hoàn thành ngày khi fake adapter tạo profile Pydantic hợp lệ và không adapter/domain nào ngoài
`adapters/llm` import OpenAI SDK.

### Ngày 09/09 — Evidence, security regression và acceptance run

Mục tiêu: khóa contract bằng test và chứng minh acceptance criteria.

- Bổ sung claim-to-evidence mapping đã chọn ở ngày 08; reject span ngoài text hoặc quote mismatch.
- Test profile có skill/experience không evidence: claim phải là `UNKNOWN` hoặc bị loại khỏi dữ liệu
  dùng cho matcher; không được bịa evidence.
- Test CV chứa prompt injection như “Ignore previous instructions ...”; test prompt boundary và fake
  adapter chứng minh chuỗi này chỉ là document data, không thay đổi policy/controls.
- Test schema failure lần đầu rồi thành công ở retry; test schema failure hai lần thành
  `NEEDS_REVIEW`.
- Chạy parse/extraction với 5 CV VI và 5 CV EN synthetic, lưu manifest/hash fixture cho track
  evaluation.
- Chạy Ruff, format check, mypy, pytest; cập nhật README chỉ với lệnh đã chạy.

Hoàn thành milestone khi toàn bộ acceptance criteria ở mục 8 pass.

## 7. Ma trận test tối thiểu

| Nhóm | Case bắt buộc |
|---|---|
| File validation | Valid PDF/TXT; filename traversal; extension/MIME/magic mismatch; binary masquerading as TXT; oversized; malformed PDF. |
| Storage | Generated key không chứa filename; read/write đúng bytes; không truy cập path ngoài storage root. |
| Parsing | TXT UTF-8; PDF text; empty/malformed/over-page-limit; offset ổn định. |
| Language | Ít nhất một `vi`, một `en`, một `mixed`; 5 fixture VI và 5 fixture EN. |
| LLM contract | Fake success; invalid structured output; one retry success; second failure `NEEDS_REVIEW`; OpenAI adapter không gọi trong test. |
| Evidence | Span bounds; quote match; claim không có evidence thành `UNKNOWN`; evidence giữ nguyên language source. |
| Security | Prompt injection; no raw CV/PII in logs; no secret in settings/fixtures; no network in unit/integration tests. |

## 8. Đối chiếu acceptance criteria

| Acceptance criterion | Bằng chứng cần có |
|---|---|
| Parse ít nhất 5 CV VI và 5 CV EN synthetic | 10 fixture synthetic, test parameterized và manifest/hash. |
| Skill quan trọng có evidence hoặc UNKNOWN | Claim-to-evidence contract, evidence validator và negative tests. |
| Sai schema retry giới hạn rồi chuyển review | Fake adapter sequence test: invalid → valid; invalid → invalid → `NEEDS_REVIEW`. |

## 9. Điểm cần chốt trước khi code

Các tài liệu không mâu thuẫn, nhưng chưa khóa chi tiết sau:

1. **Evidence association:** schema M1 có evidence phẳng; cần chốt mapping theo skill/experience
   trước khi triển khai extractor. Khuyến nghị các mapping dictionary ở mục 5.3.
2. **`NEEDS_REVIEW` trước LangGraph:** M2 chưa có workflow, nên service nên trả typed outcome;
   M3 chịu trách nhiệm map outcome vào `TalentAuditState`.
3. **Giới hạn tài nguyên:** architecture yêu cầu config nhưng chưa nêu default cho max bytes,
   max pages và max extracted text. Cần chọn các default an toàn, có thể override qua environment.
4. **PDF library:** docs không khóa thư viện. Khuyến nghị `pypdf` text-only; OCR là out of scope.
5. **OpenAI runtime configuration:** cần chốt model name và biến environment tương ứng trước khi
   chạy adapter thật. Test của M2 vẫn phải dùng fake adapter và không cần API key.

## 10. Definition of done cho M2

- Tất cả code nằm đúng module boundary ở mục 4; không có LangGraph node/API audit sớm.
- Không có CV thật, API key hoặc PII trong fixture/log/repository.
- `documents` migration chạy trên database rỗng.
- Mười fixture bilingual synthetic parse được theo acceptance criteria.
- Extraction structured-output, retry limit, prompt-injection handling và evidence validation có test.
- `ruff check .`, `ruff format --check .`, `mypy src` và `pytest` đều pass.
