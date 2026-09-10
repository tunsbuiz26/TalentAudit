# M2 — Báo cáo Day 08: LLMClient và structured profile extraction

Ngày triển khai thực tế: 09/09/2026. Phạm vi: phần Day 08 trong
[plan M2](../milestones/02_DOCUMENT_AND_EXTRACTION_PLAN.md).
Đọc trước: [phân tích Day 08](../learning/M2_DAY08_ANALYSIS.md).

## 1. Kết quả chính

Đã có service trích xuất qua abstraction, fake programmable và OpenAI adapter.
Profile chỉ được trả khi schema và evidence qua kiểm tra. Hai acceptance criteria
của Day 08 được kiểm chứng bằng test: fake trả profile Pydantic hợp lệ; SDK chỉ
được import bên trong `src/talentaudit/adapters/llm`.

Chưa gọi API OpenAI thật; không có metric chất lượng extraction. Không thêm endpoint,
LangGraph, reviewer, quyết định tuyển dụng hoặc email. Chưa tuyên bố toàn bộ M2 xong.

## 2. Cách các phần phối hợp

1. `ProfileExtractor` nhận `ParsedDocument` đã parse, giữ nguyên text, ID và hash.
2. Load prompt `profile_extractor/v1` từ resource được đóng gói cùng application.
3. Gọi port `LLMClient` với instruction, version và `UntrustedDocument` riêng biệt.
4. Adapter trả `ExtractedProfile` đã validate bằng Pydantic hoặc typed exception.
5. Validator kiểm evidence của từng skill và từng duration trên text gốc.
6. Thành công: chuyển thành `CandidateProfile` với mapping evidence; thất bại:
   `ExtractionOutcome(status=NEEDS_REVIEW, profile=None, failure_code=...)`.

Ví dụ CV synthetic `Python: 3 years.`: skill được normalize thành `python`, số năm
là 3, nhưng quote vẫn là `Python: 3 years.` với start=0/end=16. Nếu đổi quote thành
một chuỗi không có trong source, profile không được đưa tới matcher.
Thiếu năm thì dictionary experience không có entry, **không phải 0 năm**.

## 3. File thêm và vai trò

| File trong`src/talentaudit/`      | Vai trò, vì sao cần                                                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ports/llm.py`                    | Protocol generic: cùng một hàm nhận`type[T]` và trả `T`; service không biết SDK nào đang chạy                                     |
| `schemas/llm.py`                  | PromptTemplate và UntrustedDocument; JSON escape dấu`<`/`>` để dữ liệu không tự đóng delimiter, decoded text không đổi          |
| `schemas/extraction.py`           | SkillClaim, ExtractedProfile, ExtractionOutcome; đóng schema, kiểm duplicate/years, không cho result lỗi mang profile dùng được         |
| `domain/extraction_errors.py`     | Enum/exception không phụ thuộc SDK, chỉ mang code an toàn thay vì raw response hoặc lỗi chứa input                                      |
| `adapters/llm/fake.py`            | Hàng đợi JSON/typed failures để test chủ động lỗi từng request; không network, không lưu CV trong call history                      |
| `adapters/llm/openai.py`          | Nơi duy nhất biết SDK: cấu hình từ Settings, structured outputs, timeout, refusal/incomplete, đóng HTTP client                           |
| `prompts/__init__.py`             | Loader dùng importlib.resources và tên resource cố định; không dùng đường dẫn từ input                                              |
| `prompts/profile_extractor_v1.md` | Instruction versioned: CV là data, bỏ qua lệnh nhúng, UNKNOWN khi thiếu evidence, không thuộc tính nhạy cảm/quyết định tuyển dụng |
| `services/evidence_validator.py`  | Logic xác định: evidence không rỗng, đúng document ID, span trong text, quote bằng source slice                                          |
| `services/profile_extractor.py`   | Điều phối extraction/retry/validation/mapping mà không cần LangGraph, FastAPI hoặc network                                                |

| File test thêm                          | Tác dụng                                                                                                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tests/unit/test_profile_extractor.py` | 29 case: generic fake, profile VI/EN, offsets/whitespace, missing/invalid evidence, UNKNOWN, invalid years, retry, provider failures, safe output, import boundary |
| `tests/unit/test_openai_adapter.py`    | 14 case: real SDK với MockTransport, settings/environment, schema request, refusal, response truncated, server/timeout, no retry, cleanup, secret exclusion       |

Hai module test đều chặn socket/DNS. MockTransport trả HTTP trong memory;
không dùng tài khoản hay credential thật. Giá trị placeholder cho client được sinh
ngẫu nhiên trong test, không có API key literal trong source/test.

## 4. File hiện có được sửa

| File                                     | Thay đổi và ý nghĩa                                                                                                            |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `src/talentaudit/config.py`            | Thêm optional SecretStr key (ẩn repr, loại khỏi dump), model, temperature, max output tokens, timeout. App/fake không cần key |
| `.env.example`                         | Liệt kê`TALENTAUDIT_OPENAI_*`; để trống key/model, không chứa credential thật                                             |
| `src/talentaudit/schemas/candidate.py` | Thêm skill_evidence/experience_evidence mặc định rỗng, giữ tương thích matcher M1 và evidence_refs phẳng                 |
| `src/talentaudit/schemas/evidence.py`  | Không strip quote; extra forbid, ẩn text khỏi repr và input trong thông báo validation                                        |
| `pyproject.toml`                       | Runtime dependency`openai>=2,<3`; package-data bảo đảm wheel chứa prompt Markdown                                             |
| `AGENTS.md`                            | Ghi nhớ lâu dài: analysis trước mỗi ngày, report sau mỗi ngày và phân tích việc kế tiếp                              |
| `README.md`                            | Liên kết analysis/report và lệnh setup/test Day 08 đã chạy, ghi rõ offline/live boundary                                    |

Tài liệu thêm: báo cáo này, `docs/learning/M2_DAY08_ANALYSIS.md` và
`docs/learning/M2_DAY09_ANALYSIS.md`. Không sửa các quyết định thiết kế đã khóa.

## 5. Retry và failure contract

| Tình huống                         | Kết quả                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------ |
| JSON/schema invalid lần đầu       | Gọi lại đúng một lần, cùng prompt version/input; không chèn raw error vào prompt |
| Schema invalid lần hai              | NEEDS_REVIEW / SCHEMA_INVALID, attempts=2                                                  |
| Claim UNKNOWN hoặc không có claim | NEEDS_REVIEW / UNKNOWN, không có usable profile                                          |
| Thiếu/sai evidence                  | NEEDS_REVIEW / EVIDENCE_INVALID, không retry                                              |
| Refusal                              | NEEDS_REVIEW / REFUSED, không retry                                                       |
| Response không completed            | NEEDS_REVIEW / INCOMPLETE, kiểm trước khi SDK parse JSON bị cắt                       |
| Provider/server/timeout failure      | NEEDS_REVIEW / PROVIDER_UNAVAILABLE, không retry                                          |

SDK `max_retries=0` để trần hai request ở service không bị nhân lên. `store=False`
giảm việc lưu response qua API, **không đồng nghĩa zero retention**. Model phải
được cấu hình rõ và hỗ trợ structured outputs cùng temperature; không chọn model
ngầm, không hard-code key trong service/adapter.

## 6. Kiểm tra thực tế

Chạy từ repo root với `.venv` Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_profile_extractor.py
.\.venv\Scripts\python.exe -m pytest tests/unit/test_openai_adapter.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
docker compose config --quiet
git diff --check
```

Kết quả:

- Cài editable thành công; SDK kiểm chứng trong môi trường là OpenAI 2.54.0.
- Test extraction: 29 pass; adapter/config mới: 14 pass.
- Toàn bộ suite: **123 passed** (80 test cũ + 43 test mới), không skip.
- Ruff check pass; format check pass (83 file); mypy pass (61 source file).
- `pip check`: No broken requirements found.
- Compose config hợp lệ. Không build/start/restart container trong Day 08 vì không
  đổi DB/API; đây không phải bằng chứng runtime Docker đã được chạy lại.
- `git diff --check` pass, có cảnh báo LF→CRLF từ Git trên Windows.
- Build wheel với pip build isolation mặc định thành công; kiểm ZIP xác nhận
  `talentaudit/prompts/profile_extractor_v1.md` được đóng gói và đọc được.

Lần thử wheel ban đầu dùng `--no-build-isolation` thất bại vì `.venv` không có
`setuptools.build_meta`; lần build chuẩn có isolation đã pass, không cần thay code.
Pip có cảnh báo môi trường sẵn có `Ignoring invalid distribution ~ip`; chưa dọn vì
không thuộc feature Day 08 và không ảnh hưởng kết quả test/kiểm dependency.

## 7. Giới hạn và việc chưa hoàn thành

- Live OpenAI chưa được gọi, chưa chứng minh chất lượng extraction/kháng prompt
  injection của model thật. Test chỉ chứng minh schema, controls và transport.
- Quote khớp nguồn chứng minh provenance, không chứng minh claim đúng ngữ nghĩa;
  evidence có thể tồn tại nhưng không hỗ trợ skill/year đó. Cần regression/evaluation
  tiếp theo; không dùng output để ra quyết định tuyển dụng tự động.
- Hai việc tồn Day 07: hard timeout/resource isolation PDF và migration/persistence
  parser_status/document_language/page_count. Timeout OpenAI không thay thế chúng.
- Chưa chạy 10 fixture qua extraction hoặc tạo manifest/hash trong Day 08 (Day 09).
- CandidateProfile M1 vẫn cho dữ liệu cũ không có evidence; đường extraction mới
  bắt buộc qua service validator. Code tích hợp sau này phải check outcome, không
  gọi matcher trực tiếp trên output LLM hoặc dùng model_construct bỏ validation.
- Không commit hoặc push; các thay đổi nằm trong working tree để người dùng review.

## 8. Bước tiếp theo

Thực hiện [phân tích Day 09](../learning/M2_DAY09_ANALYSIS.md): evidence/security
regression, integration 10 fixture + manifest, và đóng backlog M2 trước nghiệm thu.

Tài liệu adapter được đối chiếu bằng skill openai-docs với
[OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs):
dùng Pydantic structured parsing, giữ schema đóng, xử lý refusal/incomplete riêng.
Không coi schema hợp lệ là nội dung đúng.
