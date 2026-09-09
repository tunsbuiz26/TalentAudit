# Milestone 2 — Day 07: Phân tích deterministic parsing và language metadata

## 1. Mục tiêu ngày 07

Trạng thái: checklist mục 8 đã được kiểm chứng (80 tests pass).
Timeout cứng/resource isolation và persistence parser metadata ở mục 5.3/6
vẫn là phần việc mở, không được xem là đã hoàn thành bởi checklist này.

Chuyển một `ValidatedDocument` của Day 06 thành text có provenance, theo cách
xác định, giới hạn tài nguyên và không cần LLM/network.

```text
ValidatedDocument
  -> DocumentParser (TXT hoặc text-based PDF)
  -> ParsedDocument | DocumentParseError
  -> deterministic language detector
  -> ParsedDocument có document_language
```

Day 07 phải giữ nguyên text nguồn để Day 08–09 có thể xác minh offset và quote
của evidence. Không dịch, chuẩn hóa whitespace toàn cục hoặc làm biến đổi text
trước khi xác định offset.

## 2. Phạm vi được làm

1. Parse UTF-8 `.txt` và text-based `.pdf` đã qua `DocumentValidator`.
2. Dùng parser PDF text-only (khuyến nghị `pypdf`), chỉ đọc text; không OCR,
   không chạy link, macro, JavaScript hay embedded content.
3. Áp dụng limits từ `Settings`:
   `max_pdf_pages` và `max_extracted_text_chars`.
4. Trả kết quả thành công là `ParsedDocument`; lỗi parse là typed error code,
   không để exception thư viện đi thẳng ra application layer.
5. Detect language bằng code deterministic cho `vi`, `en`, `mixed`.
6. Thêm tối thiểu 5 fixture CV synthetic tiếng Việt và 5 fixture synthetic tiếng
   Anh, không chứa PII thật.
7. Test TXT/PDF happy path, text rỗng, PDF malformed, quá giới hạn trang/text,
   parser error, language metadata và 10 fixtures.

## 3. Không thuộc Day 07

| Hạng mục | Thuộc khi nào |
| --- | --- |
| LLMClient, OpenAI adapter, prompt versioned | Day 08 |
| Trích xuất `CandidateProfile`/`EvidenceRef` từ text | Day 08 |
| Retry structured output, `NEEDS_REVIEW` cho extraction | Day 08 |
| Claim-to-evidence mapping, quote/span validation, prompt-injection regression | Day 09 |
| FastAPI audit/upload endpoint, LangGraph node/state/checkpointer | Milestone 3 |
| OCR PDF scan, quyết định tuyển dụng | Ngoài MVP/phase sau |

`CandidateProfile` và `EvidenceRef` schemas hiện có từ Milestone 1, nhưng Day
07 không được dùng LLM hoặc tạo candidate profile từ CV.

## 4. Kiến trúc và data flow cần giữ

| Layer | Trách nhiệm Day 07 |
| --- | --- |
| `schemas/` | DTO `ParsedDocument`, language/parser status và contract parse failure nếu cần serialize. |
| `services/` | `document_parser.py`, language detector và mapping lỗi thư viện sang domain error. Không import FastAPI, LangGraph hoặc OpenAI SDK. |
| `domain/` | Enum/error code parse ổn định nếu các lỗi cần xuất hiện ở workflow sau này. |
| `adapters/db/` | Migration mới cho parser metadata khi contract được chốt. Không lưu raw document bytes. |
| `tests/fixtures/` | Chỉ CV synthetic bilingual và malformed fixtures, không PII thật. |

Parser nhận `ValidatedDocument`, không nhận upload thô. Hash đã được validator tính
trước parse (`sha256`); parser không được thay đổi `content` trước khi text/evidence
offset được tạo.

## 5. Contract đề xuất trước khi code

### 5.1 `ParsedDocument`

Contract tối thiểu nên chứa:

```python
document_id: str
sha256: str
text: str
document_language: Literal["vi", "en", "mixed"]
page_count: int | None  # None cho TXT
```

`text` chỉ tồn tại trong DTO/process memory ở Day 07. Không thêm raw PDF bytes
vào PostgreSQL. Quyết định persist parsed text hay chỉ persist parser metadata
phải được chốt riêng trước Milestone 3, vì text CV vẫn có thể là personal data.

### 5.2 Parse errors

Nên thêm `DocumentParseError` với error codes, ví dụ:

- `EMPTY_TEXT` — TXT/PDF không cho text hữu ích;
- `MALFORMED_PDF` — PDF không đọc được;
- `PASSWORD_PROTECTED_PDF` — PDF yêu cầu mật khẩu;
- `PAGE_LIMIT_EXCEEDED` — số trang vượt `max_pdf_pages`;
- `TEXT_LIMIT_EXCEEDED` — extracted text vượt `max_extracted_text_chars`;
- `PARSER_ERROR` — lỗi parser không phân loại được.

Public error chỉ có code/message tổng quát; không có raw text, filename hoặc
bytes trong exception/log.

### 5.3 Metadata persistence

Plan M2 yêu cầu parser status và language trong document metadata, trong khi
bảng `documents` hiện có mới chứa upload metadata/hash. Day 07 cần migration
tiếp theo, dự kiến thêm:

```text
parser_status
document_language  # nullable cho document chưa parse hoặc parse fail
page_count         # nullable cho TXT/parse fail
```

Không thêm cột `content` hoặc raw PDF bytes. `ParsedDocument.text` không được
tự động lưu vào bảng này.

## 6. Quyết định cần chốt trước implementation

1. **Timeout parser:** roadmap yêu cầu timeout/resource boundary, nhưng
   `Settings` chưa có `document_parse_timeout_seconds`. Không hard-code timeout
   trong parser. Khuyến nghị thêm setting environment riêng và chọn cơ chế timeout
   phù hợp Windows/container trước khi code.
2. **PDF library:** dùng `pypdf` text-only như roadmap khuyến nghị; thêm nó vào
   production dependencies, không dùng OCR library.
3. **Text limit behavior:** khi vượt `max_extracted_text_chars`, khuyến nghị
   reject với `TEXT_LIMIT_EXCEEDED`, không truncate âm thầm vì truncation làm
   evidence offsets không còn phản ánh toàn document.
4. **Language heuristic:** cần deterministic rule rõ ràng cho text ngắn/không
   phân biệt được. Khuyến nghị trả `mixed` khi không đủ evidence để khẳng định
   riêng `vi` hoặc `en`, thay vì đoán.
5. **PDF không có text:** PDF scan/image-only là `EMPTY_TEXT` hoặc parse failure;
   không đưa OCR vào Day 07.

Các mục này là quyết định thiết kế cần được xác nhận khi bắt đầu code Day 07;
tài liệu này không tự thay đổi contract hay Settings.

## 7. Kế hoạch file dự kiến

| File dự kiến | Vai trò |
| --- | --- |
| `src/talentaudit/schemas/document.py` | Bổ sung `ParsedDocument` và types/enums cần thiết. |
| `src/talentaudit/domain/exceptions.py` | Bổ sung typed parse errors/code nếu dùng exception boundary. |
| `src/talentaudit/services/document_parser.py` | Parse TXT/PDF, enforce page/text/resource limits, giữ offset ổn định. |
| `src/talentaudit/services/language_detector.py` | Detect `vi`/`en`/`mixed` thuần deterministic. |
| `src/talentaudit/config.py` và `.env.example` | Chỉ cập nhật nếu timeout setting được chốt. |
| `pyproject.toml` | Thêm `pypdf` runtime dependency đã pin version range phù hợp. |
| `src/talentaudit/adapters/db/models.py` | Bổ sung parser metadata sau khi contract được chốt. |
| `migrations/versions/0003_*.py` | Migration parser metadata, không thay đổi migration `0002`. |
| `tests/fixtures/documents/` | 5 VI + 5 EN synthetic, TXT/PDF hợp lệ và fixtures lỗi cần thiết. |
| `tests/unit/test_document_parser.py` | Unit tests parser và resource/error paths. |
| `tests/unit/test_language_detector.py` | Unit tests `vi`, `en`, `mixed`, ambiguous text. |
| `tests/integration/test_document_parser_persistence.py` | Test parser metadata mapping/migration nếu persistence được thêm. |

Tên file migration chính xác sẽ được Alembic sinh theo revision thực tế; không
tạo/sửa migration Day 06 đã được kiểm chứng.

## 8. Acceptance checklist Day 07

- [x] TXT UTF-8 hợp lệ tạo `ParsedDocument`, `page_count is None`.
- [x] PDF text-based hợp lệ tạo `ParsedDocument` với page count đúng.
- [x] Hash/document ID vẫn khớp `ValidatedDocument`; parser không thay đổi text
  trước khi offsets được dùng.
- [x] TXT/PDF không có text, malformed PDF, password-protected PDF và parser
  error trả typed failure code.
- [x] PDF vượt page limit và text vượt character limit bị reject rõ ràng.
- [x] Detector không gọi LLM/network và phân loại được `vi`, `en`, `mixed`.
- [x] Có ít nhất 5 fixtures VI và 5 fixtures EN synthetic; không có PII thật.
- [x] Tất cả fixture tạo `ParsedDocument` đúng language hoặc typed parse failure.
- [x] `ruff check .`, `ruff format --check .`, `mypy src`, `pytest` pass.
- [x] Không có FastAPI audit endpoint, LangGraph, OpenAI adapter hoặc extraction
  profile được thêm sớm.

## 9. Thứ tự triển khai an toàn

### Kết quả triển khai checklist

- ParsedDocument trả language bắt buộc. Detector dùng từ vựng VI/EN và phân tích
  bản sao NFC/casefold. Có tín hiệu cả hai hoặc không có tín hiệu: mixed.
  Đây là heuristic MVP; chưa đo accuracy trên held-out data.
- TXT giữ CRLF/tab/Unicode. PDF giữ text trích xuất của mỗi trang và nối bằng
  một newline. Evidence offsets tham chiếu chuỗi kết quả, không phải PDF bytes.
- Test bao gồm hash mismatch, blank/encrypted/malformed PDF, parser error,
  character limit (kể cả newline giữa trang), page limit và Unicode.
- 10 fixtures TXT synthetic ở tests/fixtures/documents, 5 VI và 5 EN;
  integration tests chặn socket/DNS và chạy validator rồi parser cho từng file.
- Ruff, format check, mypy src, pytest pass: 80 tests.
- Không thay đổi API, workflow, OpenAI adapter hoặc profile extractor.

### Kế hoạch ban đầu

1. Chốt timeout/error/status contracts.
2. Thêm dependency `pypdf`, DTO/error schemas và unit tests trước.
3. Implement parser TXT trước, sau đó PDF text-only và limits.
4. Implement language detector độc lập, fixture synthetic và tests.
5. Chỉ sau khi parser contract ổn định mới thêm migration metadata.
6. Chạy quality gates và migration trên PostgreSQL rỗng; không bắt đầu Day 08
   cho đến khi checklist trên pass.
