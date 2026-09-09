# Milestone 2 — Day 06: Document trust boundary và persistence

## 1. Mục tiêu đã hoàn thành

Day 06 xây phần ranh giới tin cậy (trust boundary) cho tài liệu đầu vào. CV/JD
là dữ liệu không tin cậy: file có thể quá lớn, giả MIME type, chứa bytes nhị
phân hoặc cố gắng dùng filename để đi ra ngoài thư mục lưu trữ.

Luồng đã triển khai là:

```text
DocumentUpload (bytes không tin cậy)
  -> DocumentValidator
  -> ValidatedDocument (bytes đã được kiểm tra)
  -> DocumentStorage
  -> DocumentMetadata (không có bytes)
  -> DocumentRepository / bảng documents
```

Điểm quan trọng: database chỉ nhận `DocumentMetadata`; raw bytes của CV/JD
không có field, cột hoặc log trong persistence layer.

## 2. Cấu hình document processing

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/config.py` | Thêm các Settings đọc từ environment: đường dẫn storage, MIME type cho phép, giới hạn upload bytes, số trang PDF và số ký tự text sau extraction. Service không tự hard-code các giới hạn này. |
| `.env.example` | Công bố các biến `TALENTAUDIT_DOCUMENT_*`, `TALENTAUDIT_MAX_*` với default local không nhạy cảm. MIME types được biểu diễn bằng JSON array. |
| `tests/unit/test_config.py` | Kiểm tra default an toàn, giới hạn dương và MIME configuration chỉ cho phép loại MVP hỗ trợ. |

Các values hiện tại là cấu hình local-dev, không phải business rule cố định:

- `5 MiB` cho upload;
- `25` trang PDF;
- `1,000,000` ký tự text;
- `application/pdf` và `text/plain`.

`Settings` không tạo thư mục. Việc đó là side effect và thuộc về adapter storage.

## 3. Contracts và lỗi nghiệp vụ

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/schemas/document.py` | Chứa Pydantic DTOs. `DocumentUpload` là input không tin cậy; `ValidatedDocument` là bytes đã qua validation; `DocumentMetadata` là DTO persistable và cố ý không có `content`. Schema cũng chặn storage key tuyệt đối, `.`/`..` và backslash. |
| `src/talentaudit/domain/exceptions.py` | Định nghĩa `DocumentValidationError` và error codes ổn định như `FILE_TOO_LARGE`, `MIME_MISMATCH`, `INVALID_FILENAME`. Message public tổng quát, không đưa filename hay bytes vào exception. |
| `tests/unit/test_document_contracts.py` | Kiểm tra schema loại dữ liệu sai, raw bytes bị loại khỏi serialized result và storage key traversal bị từ chối. |

`DocumentMimeType` chỉ là literal `application/pdf` hoặc `text/plain`. Điều này
ngăn code MVP vô tình nhận một file type chưa có parser hỗ trợ.

## 4. Deterministic validator

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/services/document_validator.py` | Kiểm tra filename, extension, declared MIME, magic bytes và size. Đây là code thuần, không gọi network, LangGraph hoặc LLM. Nó tạo SHA-256 và `document_id` cho document hợp lệ. |
| `tests/unit/test_document_validator.py` | Kiểm tra PDF/TXT hợp lệ; mismatch extension/MIME/magic bytes; oversized input; filename có path separator; bytes binary giả `.txt`. |

Validator yêu cầu ba tín hiệu thống nhất:

1. Extension (`.pdf` hoặc `.txt`);
2. MIME type do client khai báo;
3. Nội dung thực tế: PDF bắt đầu với `%PDF-`; text phải là UTF-8 và không chứa
   NUL/control byte không hợp lệ.

Đây chưa phải parser PDF hoàn chỉnh. Nó chỉ xác minh nhanh ở trust boundary;
parse PDF có giới hạn page/text thuộc Day 07.

## 5. Storage port và local adapter

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/ports/storage.py` | Định nghĩa `DocumentStorage` interface với `put`, `get`, `delete`. Application service phụ thuộc port, không phụ thuộc filesystem cụ thể. |
| `src/talentaudit/adapters/storage/local.py` | Hiện thực local filesystem. Key được sinh theo `documents/<uuid>.pdf|txt`, không dùng filename từ người upload. Mỗi `get`/`delete` resolve path và xác nhận path vẫn ở dưới configured root. |
| `src/talentaudit/adapters/storage/__init__.py` | Cập nhật mô tả package storage adapters. |
| `tests/unit/test_local_document_storage.py` | Kiểm tra key được sinh, lưu/đọc/xóa bytes hợp lệ và từ chối `../`, absolute path, backslash traversal. |

`LocalDocumentStorage` dùng chế độ tạo file độc quyền (`xb`) để không ghi đè
file nếu hiếm khi xảy ra UUID collision.

## 6. Metadata persistence và migration

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/adapters/db/models.py` | Thêm `DocumentModel` với `id`, `storage_key`, `sha256`, `mime_type`, `size_bytes`, `created_at`. Không có cột `content`. |
| `src/talentaudit/ports/repositories.py` | Thêm `DocumentRepository` port chỉ nhận/trả `DocumentMetadata`. |
| `src/talentaudit/adapters/db/document_repository.py` | SQLAlchemy adapter. ORM record được validate lại qua Pydantic khi đọc ra; `commit` lỗi sẽ rollback session trước khi re-raise. |
| `migrations/versions/0002_documents.py` | Alembic revision tạo bảng `documents`, unique `storage_key` và index SHA-256. Nó nối tiếp `0001_initial`. |
| `tests/integration/test_document_repository.py` | Kiểm tra persist/get metadata, khẳng định model không có raw bytes column, unknown ID trả `None`, và session vẫn dùng được sau unique-constraint failure. |

SHA-256 được index để hỗ trợ tra cứu/truy vết sau này. Nó **không** unique vì hai
lần upload cùng nội dung có thể là các document records hợp lệ khác nhau.

## 7. Application orchestration và cleanup

| File | Tác dụng |
| --- | --- |
| `src/talentaudit/application/services/document_ingestion_service.py` | Điều phối `validate -> store -> persist metadata`. Service này là nơi đảm bảo thứ tự trust boundary; không biết FastAPI hay SQLAlchemy implementation cụ thể. Nếu repository lỗi sau storage thành công, service gọi `delete(storage_key)` rồi re-raise lỗi gốc. |
| `tests/unit/test_document_ingestion_service.py` | Kiểm tra validation failure không gọi storage/repository; happy path chỉ đưa metadata vào repository; persistence failure sẽ cleanup file vừa lưu. |

Chưa có upload API ở Day 06. Khi API được thêm, route phải gọi
`DocumentIngestionService`, không được tự ghi file hay gọi repository trực tiếp.

## 8. Xác minh đã chạy

Các lệnh đã pass sau implementation:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
```

Kết quả cuối cùng: **49 tests passed**, Ruff và mypy không báo lỗi.

Alembic/PostgreSQL cũng đã được xác minh qua Docker:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

- Database hiện có nâng từ `0001_initial` lên `0002_documents` thành công.
- Một database rỗng tạm đã chạy toàn bộ chain `base -> 0001 -> 0002`, sau đó
  được xóa.
- Container app chứa `0002_documents`; `/health` và `/ready` đều trả thành công.

## 9. Phạm vi cố ý chưa làm

Các phần sau thuộc Day 07 hoặc phase sau, không được giả vờ đã hoàn thành:

- parse nội dung PDF thật và giới hạn số trang;
- parse TXT/PDF thành text bị giới hạn `max_extracted_text_chars`;
- phát hiện password-protected/corrupt PDF ở parser;
- language detection;
- extraction CandidateProfile/EvidenceRef;
- upload endpoint FastAPI và workflow/LangGraph.

Không có API key, token, password thật hoặc dữ liệu ứng viên thật trong Day 06.
