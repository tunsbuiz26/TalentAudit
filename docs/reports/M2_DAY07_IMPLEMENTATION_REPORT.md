# Milestone 2 — Day 07: Deterministic parsing và language metadata

## 1. Mục tiêu đã hoàn thành

Day 07 chuyển `ValidatedDocument` từ Day 06 thành `ParsedDocument` có text,
SHA-256, document ID, page count và language metadata. Luồng này hoàn toàn
deterministic: không gọi LLM, network, FastAPI endpoint, LangGraph hoặc OpenAI.

```text
ValidatedDocument
  -> DocumentParser
  -> TXT UTF-8 hoặc PDF text-based
  -> LanguageDetector
  -> ParsedDocument | DocumentParseError
```

Parser chỉ nhận bytes đã qua validation. Nó kiểm tra lại SHA-256 trước khi parse
để bảo đảm document ID/hash/text cùng thuộc một input. Text trả về giữ nguyên
nội dung TXT; không dịch hoặc normalize whitespace trước khi evidence offsets
được dùng ở milestone sau.

## 2. Contracts và typed errors

| File                                     | Tác dụng                                                                                                                                                                                     |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/talentaudit/schemas/document.py`  | Thêm`ParsedDocument`: `document_id`, `sha256`, `text`, `document_language` (`vi`, `en`, `mixed`) và `page_count`. TXT có `page_count=None`; PDF có page count dương. |
| `src/talentaudit/domain/exceptions.py` | Thêm`DocumentParseError` cùng stable error codes. Public message không chứa text CV, filename hoặc bytes.                                                                               |

Các lỗi parser được phân loại:

- `HASH_MISMATCH`: bytes không khớp SHA-256 đã validate.
- `INVALID_TEXT_ENCODING`, `EMPTY_TEXT`, `TEXT_LIMIT_EXCEEDED`: lỗi TXT
  hoặc text extract.
- `MALFORMED_PDF`, `PASSWORD_PROTECTED_PDF`,
  `PAGE_LIMIT_EXCEEDED`: lỗi PDF có nguyên nhân xác định.
- `PARSER_ERROR`: lỗi thư viện bất ngờ, được che thông tin nội bộ.

## 3. Parser deterministic

| File                                            | Tác dụng                                                                                                                                                                            |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/talentaudit/services/document_parser.py` | Dispatch theo MIME type; decode TXT UTF-8; dùng`pypdf` để extract text-only PDF; áp dụng `max_pdf_pages` và `max_extracted_text_chars`; map exception thành typed error. |
| `tests/unit/test_document_parser.py`          | Test happy path TXT/PDF, page count, hash/ID, offsets, blank/encrypted/malformed PDF, parser error, page limit, text limit và Unicode.                                               |

PDF parser dùng `PdfReader` với `strict=True`. Nó chỉ đọc nội dung text; không
render, không OCR và không thực thi link, macro, JavaScript hoặc embedded content.

Với PDF nhiều trang, text của từng trang được nối bằng một newline. Evidence
offsets sau này phải tham chiếu chính xác chuỗi `ParsedDocument.text` này, không
tham chiếu PDF byte offsets hoặc tọa độ trên trang.

## 4. Language detector

| File                                              | Tác dụng                                                                                                                                                             |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/talentaudit/services/language_detector.py` | Nhận diện`vi`, `en`, `mixed` bằng từ vựng marker cố định; chỉ dùng Python standard library.                                                            |
| `tests/unit/test_language_detector.py`          | Test Vietnamese, English, mixed, text kỹ thuật mơ hồ, text trống và Unicode normalization; monkeypatch socket/DNS để chứng minh detector không gọi network. |

Detector chạy NFC/casefold trên một bản sao của text; `ParsedDocument.text`
không bị thay đổi. Nếu text có marker của cả hai ngôn ngữ, hoặc thiếu marker đủ
mạnh (ví dụ chỉ có `Python SQL Docker`), kết quả là `mixed`.

Đây là heuristic phục vụ MVP, chưa phải metric language-classification đã được
đánh giá trên held-out dataset.

## 5. Synthetic fixtures

| Vị trí                                                 | Tác dụng                                                                                                                                           |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/fixtures/documents/vi_1.txt` đến `vi_5.txt` | Năm CV development synthetic tiếng Việt.                                                                                                          |
| `tests/fixtures/documents/en_1.txt` đến `en_5.txt` | Năm CV development synthetic tiếng Anh.                                                                                                            |
| `tests/fixtures/documents/README.md`                   | Mô tả nguồn gốc synthetic, giới hạn sử dụng và quy ước filename.                                                                          |
| `tests/integration/test_document_fixtures.py`          | Chạy mỗi fixture qua`DocumentValidator -> DocumentParser`; chặn socket và DNS; kiểm tra language, text, hash, ID, page count và determinism. |

Các fixture không chứa tên người, email, số điện thoại, công ty thật hoặc dữ liệu
ứng viên thật. Đây là development/regression fixtures, chưa phải held-out
evaluation dataset.

PDF test fixture được tạo hoàn toàn trong memory bằng `reportlab`; không có
PDF CV thật trong repository.

## 6. Dependencies

| File               | Tác dụng                                                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `pyproject.toml` | Thêm`pypdf` vào runtime dependencies và `reportlab` vào development dependencies để tạo synthetic PDF test fixture. |

`pypdf` thuộc runtime vì `DocumentParser` cần nó. `reportlab` chỉ phục vụ test,
không cần thiết cho app production.

## 7. Xác minh đã chạy

Các quality gates đã chạy sau implementation:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
```

Kết quả: **80 tests passed**; Ruff, format check, mypy và `git diff --check`
đều pass.

Test parser bao gồm:

- TXT UTF-8 hợp lệ với `page_count=None`;
- PDF text-based hai trang với page count đúng;
- hash/document ID và text/offset ổn định;
- empty TXT/PDF, malformed PDF, encrypted PDF và lỗi parser bất ngờ;
- page limit và character limit;
- 5 fixture VI và 5 fixture EN;
- xác nhận không có network trong detector/fixture integration tests.

## 8. Phạm vi chưa làm

Day 07 không thêm FastAPI audit/upload endpoint, LangGraph workflow, OpenAI
adapter, prompt, `CandidateProfile` extraction hoặc `EvidenceRef` validation.
Các phần này thuộc Day 08–09 hoặc Milestone 3.

Hai giới hạn kỹ thuật vẫn cần xử lý ở công việc tiếp theo:

1. Timeout cứng/resource isolation cho PDF parser. Settings hiện chưa có
   `document_parse_timeout_seconds`, nên parser chưa có cơ chế dừng process
   parse bị treo.
2. Persistence parser metadata. Bảng `documents` hiện lưu upload metadata/hash;
   `parser_status`, `document_language` và `page_count` chưa có migration.

Không có API key, token, mật khẩu thật, raw CV hoặc PII ứng viên trong Day 07.
