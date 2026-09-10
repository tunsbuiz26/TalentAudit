# M2 — Báo cáo Day 09: Evidence, parser isolation và metadata

## 1. Kết quả và trạng thái

Đã triển khai regression, 10 fixture bilingual qua extraction fake, manifest/hash,
PDF worker có timeout và persistence parser metadata. **157 tests pass**; Ruff,
format check, mypy, Compose config và migration PostgreSQL 16 đều pass. Các
acceptance criteria của Milestone 2 đã được đối chiếu và hoàn thành.

Tham chiếu [phân tích Day 09](../learning/M2_DAY09_ANALYSIS.md),
[plan M2](../milestones/02_DOCUMENT_AND_EXTRACTION_PLAN.md),
[phân tích Day 10](../learning/M3_DAY10_ANALYSIS.md).

## 2. Những phần đã làm và vai trò từng file

Các đường dẫn source trong bảng tính từ `src/talentaudit/`.

| File mới | Vai trò / tác dụng |
| --- | --- |
| `services/pdf_text.py` | Tách PDF decoding khỏi lifecycle process; giữ text nguyên trạng, kiểm page/character limit, trả typed error |
| `adapters/parsing/pdf_process.py` | Gọi worker bằng stdin/stdout, timeout, kill và thu hồi child; bỏ stderr, không chuyển Settings/key vào process |
| `adapters/parsing/pdf_worker.py` | Entrypoint process riêng; chỉ nhận request tối thiểu và trả text/page count hoặc error code |
| `adapters/parsing/__init__.py` | Package chứa hạ tầng thực thi parser |
| `schemas/pdf_worker.py` | Contract Pydantic cho limits, request base64 và response; bytes không xuất hiện trong command line |
| `application/services/document_parsing_service.py` | Use case `parse_and_persist`: kiểm document đã tồn tại/hash/MIME, gọi parser, lưu metadata thành công hoặc thất bại |
| `migrations/versions/0003_parse_metadata.py` (repo root) | Thêm parser_status, language, page_count, error code; bản ghi cũ giữ trạng thái PENDING |
| `tests/fixtures/documents/manifest.json` (repo root) | 10 hash bytes cố định, language và expected skills/status; development regression, không phải held-out |
| `.gitattributes` (repo root) | Khóa LF cho fixture TXT để Git trên Windows/Linux không làm đổi hash/offset |

| File hiện có sửa | Ý nghĩa |
| --- | --- |
| `services/document_parser.py` | PDF chuyển sang worker; TXT vẫn decode trực tiếp với giới hạn, hash/language/offset contract giữ nguyên |
| `config.py`, `.env.example` | Thêm `TALENTAUDIT_DOCUMENT_PARSE_TIMEOUT_SECONDS`, mặc định 15 giây, giá trị phải >0 và <=300 |
| `domain/exceptions.py` | Thêm `PARSE_TIMEOUT` và public message an toàn |
| `schemas/document.py` | ParseState và DocumentParseMetadata; PENDING/PARSED/FAILED có invariant; metadata không chứa text/bytes |
| `ports/repositories.py` | Thêm `update_parse_metadata`, giữ persistence sau interface |
| `adapters/db/models.py`, `document_repository.py` | ORM và thao tác lưu parser metadata; kiểm hash, MIME/page count và rollback khi commit lỗi; create chỉ nhận trạng thái PENDING |
| `services/evidence_validator.py` | Thêm lexical guard tên skill trong quote để chặn gán quote của skill khác |
| `services/profile_extractor.py` | Áp dụng guard cho evidence skill và duration trước khi trả profile |
| `migrations/env.py` (repo root) | Hỗ trợ connection được truyền rõ ràng, giúp test migration trên DB tạm không dùng cấu hình runtime |
| `alembic.ini` (repo root) | `path_separator=os`, loại cảnh báo cấu hình đường dẫn Alembic |
| `README.md` (repo root) | Liên kết báo cáo, trạng thái nghiệm thu và lệnh test đã chạy |

Skill clean-code được dùng theo hướng test-first: test timeout/metadata/migration
và regression evidence được viết trước phần sửa tương ứng. PDF decoding, quản lý
process và lưu DB được tách để có thể giải thích/test độc lập.

## 3. Test thêm và cập nhật

| File | Kiểm chứng |
| --- | --- |
| `tests/unit/test_pdf_process.py` | Worker ngủ bị kill/reap; worker crash không lộ diagnostics; timeout Settings được chuyển đúng và request không chứa secrets |
| `tests/unit/test_day09_evidence.py` | Span âm/đảo/rỗng/quá dài, Unicode tổ hợp/CRLF, một claim tốt không che claim thiếu evidence, prompt injection VI/EN và delimiter, trần hai lần gọi |
| `tests/integration/test_extraction_fixtures.py` | 5 VI + 5 EN qua validator/parser/extractor fake; kiểm manifest/hash, skill labels, evidence slices, language, ID và attempts; chặn socket/DNS |
| `tests/integration/test_parse_metadata.py` | Service lưu thành công/thất bại; hash sai/ID thiếu; trạng thái metadata không hợp lệ; không lưu raw CV |
| `tests/integration/test_document_migrations.py` | Alembic 0001→0002→0003 trên SQLite tạm, bản ghi cũ giữ PENDING, downgrade 0003 giữ bản ghi và bỏ đúng cột mới; chặn engine runtime |
| Các test document parser/contracts/repository/ingestion cũ | Điều chỉnh theo metadata mới và PDF decoding được tách; giữ test hash, limits, PDF lỗi và provenance |

Tổng suite tăng từ 123 của Day 08 lên 157. Không gọi API LLM thật. Fixture có ghi
kinh nghiệm chung nhưng không gắn duration rõ cho từng skill, nên label years=null;
không suy diễn số năm hoặc biến thiếu dữ liệu thành 0.

## 4. Lỗi tìm được bằng regression

Trước khi sửa: source `Python and SQL`, claim Python gắn quote `SQL` tại offsets
đúng vẫn trả SUCCESS, vì validator cũ mới kiểm provenance.

Sau khi sửa: tên skill phải xuất hiện (normalize và word boundary) trong ít nhất
một quote đã qua kiểm provenance. Trường hợp trên trả NEEDS_REVIEW, profile=None.

Đây là kiểm tra bảo thủ: không tự suy luận alias, không chứng minh phủ định hoặc
ngữ nghĩa/numeric duration đúng. Một quote thật vẫn có thể bị model hiểu sai.
Không coi test fake là bằng chứng model thật chống prompt injection hoặc đạt F1.

## 5. Cách kiểm chứng và kết quả thực tế

Các lệnh đã chạy từ repo root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_pdf_process.py tests/unit/test_document_parser.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_day09_evidence.py tests/integration/test_extraction_fixtures.py
.\.venv\Scripts\python.exe -m pytest tests/integration/test_document_migrations.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
docker compose config --quiet
git diff --check
```

Kết quả cuối: Ruff pass, 95 Python files đúng format, mypy pass trên 67 source
files, **157 passed**, Compose config pass, diff whitespace check pass.
Git có cảnh báo LF→CRLF ở file khác; fixture TXT đã có rule LF riêng.

## 6. Kiểm chứng PostgreSQL và giới hạn còn lại

Sau khi người dùng bật Docker Desktop, Engine 29.7.2 chạy một PostgreSQL 16 Alpine
container tạm tại localhost:55432, không dùng volume dự án. Đã kiểm chứng:

- database rỗng upgrade đến `0003_parse_metadata (head)`;
- downgrade về 0002, chèn metadata synthetic, upgrade lại 0003;
- bản ghi cũ giữ nguyên và có `parser_status=PENDING`, ba trường còn lại NULL;
- repository SQLAlchemy tạo record và round-trip trạng thái `PARSED/en`;
- bảng không có cột raw `content`.

Container test chạy với `--rm`; sau kiểm tra, container và anonymous volume đúng
của nó đã được dừng/xóa và xác nhận không còn tồn tại. Không chạm volume dự án.
Docker image ứng dụng chưa build/smoke lại vì Day 09 không thay API startup;
Compose config đã pass.

PDF worker có deadline và process riêng nhưng chưa có hard RAM cap, OS sandbox,
seccomp hoặc Windows Job Object. Giới hạn byte/page/text không bảo đảm chặn mọi
decompression bomb trước khi cấp phát. Timeout không bao gồm đầy đủ mọi độ trễ
OS khi tạo process; đây là boundary thực thi MVP, không phải sandbox bảo mật hoàn chỉnh.

Không thêm API audit/upload, graph, reviewer, email, dữ liệu ứng viên thật, API key
hoặc metric chưa đo. Matcher chưa được nối trong M2; kết quả lỗi không có profile,
nhưng M3 vẫn phải kiểm outcome trước khi gọi matcher.

## 7. Git và bàn giao

Working tree có cả thay đổi Day 08 chưa commit và phần Day 09 này. Không reset,
commit hoặc push. Báo cáo Day 08 giữ kết quả lịch sử 123 tests, không bị sửa thành
số mới. File analysis Day 09 đã cập nhật toàn bộ acceptance checkbox.

Bước tiếp theo duy nhất: bắt đầu typed state và node contracts của Screening Graph
theo [Day 10](../learning/M3_DAY10_ANALYSIS.md).
