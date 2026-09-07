# Bài thực hành M2 ngày 06 — Document Settings

Mục tiêu: tự mở rộng `src/talentaudit/config.py` để mọi giới hạn xử lý document
đều đi qua environment. Service validate file ở bước sau chỉ đọc `Settings`; nó
không được tự đặt số byte, số trang hoặc MIME type.

File này là bài thực hành, **không được import bởi ứng dụng**. Hãy tự gõ phần
`TODO` vào code thật thay vì chép nguyên khối.

## 1. Các setting cần thêm

| Python field | Environment variable | Vai trò |
|---|---|---|
| `document_storage_path` | `TALENTAUDIT_DOCUMENT_STORAGE_PATH` | Thư mục local adapter dùng để lưu bytes CV. |
| `allowed_document_mime_types` | `TALENTAUDIT_ALLOWED_DOCUMENT_MIME_TYPES` | Danh sách MIME được validator cho phép. |
| `max_upload_bytes` | `TALENTAUDIT_MAX_UPLOAD_BYTES` | Chặn file quá lớn trước parse/lưu. |
| `max_pdf_pages` | `TALENTAUDIT_MAX_PDF_PAGES` | Giới hạn tài nguyên khi parse PDF. |
| `max_extracted_text_chars` | `TALENTAUDIT_MAX_EXTRACTED_TEXT_CHARS` | Chặn parser trả text quá dài. |

## 2. Code khung cho `src/talentaudit/config.py`

Thêm `Path` vào import và đặt các field sau trong `class Settings`. Các giá trị
mặc định chỉ được đặt tại đây, không đặt lại trong service.

```python
from pathlib import Path

from pydantic import Field, field_validator


class Settings(BaseSettings):
    # ... giữ nguyên model_config và các field đang có ...

    # TODO 1:
    # Path chỉ mô tả cấu hình. Settings không nên tạo thư mục vì đó là side effect;
    # LocalDocumentStorage ở milestone sau sẽ tạo thư mục khi cần.
    document_storage_path: Path = Path("var/documents")

    # TODO 2:
    # tuple là immutable, phù hợp với configuration. pydantic-settings nhận biến
    # môi trường dạng JSON array, ví dụ:
    # TALENTAUDIT_ALLOWED_DOCUMENT_MIME_TYPES=["application/pdf","text/plain"]
    allowed_document_mime_types: tuple[str, ...] = (
        "application/pdf",
        "text/plain",
    )

    # TODO 3:
    # Field đặt constraint ngay tại boundary configuration. Các service sau này chỉ
    # so sánh kích thước thực tế với settings.max_upload_bytes.
    max_upload_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    max_pdf_pages: int = Field(default=25, ge=1, le=1_000)
    max_extracted_text_chars: int = Field(default=1_000_000, ge=1)

    # TODO 4:
    # Chỉ cho phép loại mà validator M2 thực sự biết xử lý. Điều này tránh cấu hình
    # "cho phép" Word/image trong khi code không thể parse chúng.
    @field_validator("allowed_document_mime_types")
    @classmethod
    def validate_allowed_document_mime_types(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        supported = {"application/pdf", "text/plain"}

        if not value:
            raise ValueError("at least one document MIME type must be allowed")
        if any(mime not in supported for mime in value):
            raise ValueError("unsupported document MIME type configured")
        if len(value) != len(set(value)):
            raise ValueError("document MIME types must be unique")
        return value
```

### Vì sao các defaults này đặt ở Settings?

- `5 MiB`, `25` trang và `1,000,000` ký tự là các giá trị local-dev có thể thay
  đổi qua environment, không phải business rule bất biến.
- `Field(ge=...)` làm configuration lỗi fail sớm khi app khởi động.
- `Path` không gọi `.resolve()` hoặc `.mkdir()` tại Settings: configuration phải
  không có side effect và production có thể dùng absolute path qua environment.

## 3. Cập nhật `.env.example`

Thêm các giá trị không nhạy cảm sau. Đây là default local; không đưa path máy cá
nhân, credential hoặc API key vào file này.

```dotenv
# Local document-processing limits. Override in the deployment environment.
TALENTAUDIT_DOCUMENT_STORAGE_PATH=var/documents
TALENTAUDIT_ALLOWED_DOCUMENT_MIME_TYPES=["application/pdf","text/plain"]
TALENTAUDIT_MAX_UPLOAD_BYTES=5242880
TALENTAUDIT_MAX_PDF_PAGES=25
TALENTAUDIT_MAX_EXTRACTED_TEXT_CHARS=1000000
```

Lưu ý: value cho `TALENTAUDIT_ALLOWED_DOCUMENT_MIME_TYPES` phải là JSON array,
không phải chuỗi `application/pdf,text/plain`.

## 4. Test mẫu cho `tests/unit/test_config.py`

Viết test trước hoặc sau implementation. Các test này không cần đọc `.env` thật;
truyền keyword arguments trực tiếp vào `Settings` để độc lập với môi trường máy.

```python
def test_document_settings_have_safe_defaults() -> None:
    settings = Settings(environment="test")

    assert settings.document_storage_path == Path("var/documents")
    assert settings.allowed_document_mime_types == (
        "application/pdf",
        "text/plain",
    )
    assert settings.max_upload_bytes > 0
    assert settings.max_pdf_pages > 0
    assert settings.max_extracted_text_chars > 0


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("max_upload_bytes", 0),
        ("max_pdf_pages", 0),
        ("max_extracted_text_chars", 0),
    ],
)
def test_document_limits_reject_non_positive_values(
    field_name: str,
    value: int,
) -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", **{field_name: value})


def test_document_settings_reject_unknown_mime_type() -> None:
    with pytest.raises(ValidationError, match="unsupported document MIME"):
        Settings(
            environment="test",
            allowed_document_mime_types=("application/pdf", "image/png"),
        )
```

## 5. Tự kiểm tra sau khi bạn code

```bash
python -m pytest tests/unit/test_config.py
ruff check .
ruff format --check .
mypy src
```

Nếu test pass, bạn đã hoàn thành phần Settings của ngày 06. Bước kế tiếp mới là
tạo validator sử dụng các giá trị này; validator không được có các literal như
`5 * 1024 * 1024` hoặc `"application/pdf"` làm giới hạn riêng.
