# ISSUE-001 — PostgreSQL driver thiếu làm lỗi import app và readiness

## 1. Tiêu đề và mô tả ngắn

Trong quá trình bootstrap Milestone 0, môi trường local không có package
`psycopg`, dù package này đã được khai báo trong `pyproject.toml`. Vì app tạo
database checker ngay khi import module, việc chạy test bị fail ở bước
collection. Khi chạy server bằng Uvicorn, một lần kiểm tra `/ready` còn trả
HTTP 500 thay vì trạng thái not-ready có cấu trúc.

Issue này đã được xử lý trong working tree hiện tại, nhưng việc xác nhận đầy đủ
trên Python 3.12 và Docker Compose vẫn còn chờ môi trường có đủ công cụ.

## 2. Mục tiêu hoặc hành vi mong đợi

- Project yêu cầu Python `3.12` và dependencies phải được cài từ
  `pyproject.toml`.
- `talentaudit.main` phải import được để test `/health`, kể cả khi PostgreSQL
  chưa chạy.
- `GET /health` phải trả HTTP `200` và không cần database.
- `GET /ready` phải:
  - trả HTTP `200` với database đang hoạt động;
  - trả HTTP `503` với JSON `{"status": "not_ready", "database": "down"}`
    khi database/driver chưa sẵn sàng;
  - không làm lộ connection string, secret hoặc PII.
- `python -m pytest` phải chạy được sau khi cài dependency.
- Docker Compose phải khởi động app sau khi PostgreSQL healthy.

## 3. Hành vi thực tế

### Trước khi sửa

1. `python -m pytest` fail khi import `talentaudit.main` vì
   `SqlAlchemyDatabaseHealthChecker` tạo engine ngay trong constructor và
   SQLAlchemy import driver `psycopg`.
2. Lần đầu chạy Uvicorn không có `--app-dir src` fail vì Python không tìm thấy
   package `talentaudit`.
3. Sau khi thêm `--app-dir src`, `/health` trả `200` nhưng `/ready` trả
   `500 Internal Server Error` vì `ModuleNotFoundError` xảy ra trong readiness
   check và chưa được chuyển thành `503`.

### Sau các thay đổi hiện tại

- `python -m pytest`: `5 passed` trên Python `3.11.9` của môi trường hiện tại.
- Uvicorn chạy được với `--app-dir src`.
- `/health`: HTTP `200`, body `{"status":"ok","service":"TalentAudit"}`.
- `/ready` khi driver/database chưa sẵn sàng: HTTP `503`.
- Chưa kiểm tra được `/ready` = `200` với PostgreSQL thật vì Docker và
  `psycopg` chưa có trong môi trường hiện tại.

## 4. Các bước tái hiện lỗi

### Tái hiện lỗi test collection ban đầu

Điều kiện:

- Đứng tại root repository.
- Có các package FastAPI, Pydantic, SQLAlchemy và pytest, nhưng không có
  `psycopg` trong interpreter đang chạy.
- Code ban đầu tạo SQLAlchemy engine ngay trong
  `SqlAlchemyDatabaseHealthChecker.__init__`.

Chạy:

```powershell
python -m pytest
```

Kết quả: lỗi import ở phần stack trace bên dưới.

### Tái hiện lỗi readiness ban đầu

Chạy server từ root:

```powershell
python -m uvicorn --app-dir src talentaudit.main:app --host 127.0.0.1 --port 8765
```

Gọi endpoint:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8765/health -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8765/ready -UseBasicParsing
```

Trong code ban đầu, `/health` trả `200`, còn `/ready` trả `500` nếu `psycopg`
chưa được cài.

## 5. Toàn bộ thông báo lỗi và stack trace liên quan

### 5.1. Pytest fail vì thiếu `psycopg`

```text
==================================== ERRORS ====================================
_________________ ERROR collecting tests/unit/test_health.py __________________
ImportError while importing test module 'D:\TalentAudit – Multi-Agent Recruitment Audit System\tests\unit\test_health.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python311\Lib\importlib\__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\unit\test_health.py:4: in <module>
    from talentaudit.main import create_app
src\talentaudit\main.py:34: in <module>
    app = create_app()
src\talentaudit\main.py:20: in create_app
    resolved_checker = database_health_checker or SqlAlchemyDatabaseHealthChecker(
src\talentaudit\adapters\db\health.py:20: in __init__
    self._engine: Engine = create_engine(
C:\Users\FPTSHOP\AppData\Roaming\Python\Python311\site-packages\sqlalchemy\util\deprecations.py:281: in warned
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
C:\Users\FPTSHOP\AppData\Roaming\Python\Python311\site-packages\sqlalchemy\engine\create.py:617: in create_engine
    dbapi = dbapi_meth(**dbapi_args)
C:\Users\FPTSHOP\AppData\Roaming\Python\Python311\site-packages\sqlalchemy\dialects\postgresql\psycopg.py:495: in import_dbapi
    import psycopg
E   ModuleNotFoundError: No module named 'psycopg'
=========================== short test summary info ============================
ERROR tests/unit/test_health.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

### 5.2. Uvicorn import fail khi thiếu `--app-dir src`

Lệnh ban đầu:

```powershell
python -m uvicorn talentaudit.main:app --host 127.0.0.1 --port 8765
```

Stack trace chính:

```text
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "...site-packages\uvicorn\__main__.py", line 4, in <module>
    uvicorn.main()
  File "...site-packages\click\core.py", line 1569, in __call__
    return self.main(*args, **kwargs)
  File "...site-packages\click\core.py", line 1434, in main
    rv = self.invoke(ctx)
  File "...site-packages\click\core.py", line 907, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "...site-packages\click\core.py", line 907, in invoke
    return callback(*args, **kwargs)
  File "...site-packages\uvicorn\main.py", line 423, in main
    run(...)
  File "...site-packages\uvicorn\main.py", line 593, in run
    server.run()
  File "...site-packages\uvicorn\server.py", line 67, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
  File "...site-packages\uvicorn\_compat.py", line 23, in asyncio_run
    return runner.run(main)
  File "C:\Program Files\Python311\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "C:\Program Files\Python311\Lib\asyncio\base_events.py", line 654, in run_until_complete
    return future.result()
  File "...site-packages\uvicorn\server.py", line 71, in serve
    await self._serve(sockets)
  File "...site-packages\uvicorn\server.py", line 78, in _serve
    config.load()
  File "...site-packages\uvicorn\config.py", line 438, in load
    self.loaded_app = import_from_string(self.app)
  File "...site-packages\uvicorn\importer.py", line 22, in import_from_string
    raise exc from None
  File "...site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "C:\Program Files\Python311\Lib\importlib\__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "C:\Program Files\Python311\Lib\importlib\__init__.py", line 1176, in _find_and_load
    return _bootstrap._find_and_load_unlocked(name, import_)
  File "C:\Program Files\Python311\Lib\importlib\_bootstrap.py", line 1140, in _find_and_load_unlocked
ModuleNotFoundError: No module named 'talentaudit'
```

### 5.3. `/ready` trả 500 vì thiếu driver chưa được fail-closed

```text
Traceback (most recent call last):
  File "...site-packages\uvicorn\protocols\http\httptools_impl.py", line 409, in run_asgi
    result = await app(scope, receive, send)
  File "...site-packages\uvicorn\middleware\proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
  File "...site-packages\fastapi\applications.py", line 1133, in __call__
    await super().__call__(scope, receive, send)
  File "...site-packages\starlette\middleware\errors.py", line 186, in __call__
    raise exc
  File "...site-packages\starlette\middleware\exceptions.py", line 63, in wrapped_app
    await wrap_app_handling_exceptions(app, conn)(scope, receive, send)
  File "...site-packages\fastapi\routing.py", line 109, in app
    raw_response = await run_endpoint_function(
  File "...site-packages\fastapi\routing.py", line 290, in run_endpoint_function
    return await dependant.call(**values)
  File "...site-packages\starlette\concurrency.py", line 38, in run_in_threadpool
    return await anyio.to_thread.run_sync(func)
  File "...site-packages\anyio\to_thread.py", line 65, in run_sync
    return await get_async_backend().run_sync_in_worker_thread(func, *args)
  File "...site-packages\anyio\_backends\_asyncio.py", line 2641, in run_sync_in_worker_thread
    return await future
  File "...site-packages\anyio\_backends\_asyncio.py", line 1033, in run
    result = context.run(func, *args)
  File "D:\TalentAudit – Multi-Agent Recruitment Audit System\src\talentaudit\api\health.py", line 41, in readiness
    if not database_health_checker.check():
  File "D:\TalentAudit – Multi-Agent Recruitment Audit System\src\talentaudit\adapters\db\health.py", line 29, in check
    self._engine = create_engine(...)
  File "...site-packages\sqlalchemy\util\deprecations.py", line 281, in warned
    return fn(*args, **kwargs)
  File "...site-packages\sqlalchemy\engine\create.py", line 617, in create_engine
    dbapi = dbapi_meth(**dbapi_args)
  File "...site-packages\sqlalchemy\dialects\postgresql\psycopg.py", line 495, in import_dbapi
    import psycopg
ModuleNotFoundError: No module named 'psycopg'
```

## 6. Các lệnh đã chạy

### Kiểm tra môi trường

```powershell
python --version                 # Python 3.11.9
py -3.12 --version               # không có Python 3.12 khả dụng
ruff --version                   # command not found
mypy --version                   # command not found
pytest --version                 # có pytest
docker --version                 # command not found
docker compose version           # command not found
uv --version                     # command not found
```

Các package import được trong interpreter local: FastAPI, Pydantic v2,
`pydantic-settings`, SQLAlchemy v2, pytest và httpx. `psycopg` không import
được.

### Kiểm tra code và runtime

```powershell
python -m pytest
python -m compileall -q src tests
python -m uvicorn talentaudit.main:app --host 127.0.0.1 --port 8765
python -m uvicorn --app-dir src talentaudit.main:app --host 127.0.0.1 --port 8765
Invoke-WebRequest -Uri http://127.0.0.1:8765/health -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:8765/ready -UseBasicParsing
python -c "import tomllib; ..."
python -c "import yaml; ..."
```

### Quality/security/Git

```powershell
ruff check .
ruff format --check .
mypy src
rg -n -i "sk-[A-Za-z0-9]|api[_-]?key|password\s*=|secret\s*=" --glob '!docs/**' .
git status --short
git init -b main
git add -A
git diff --cached --stat
git commit -m "chore: bootstrap TalentAudit project"
git log -1 --oneline --decorate
git remote -v
git diff HEAD -- src/talentaudit/adapters/db/health.py src/talentaudit/main.py src/talentaudit/api/health.py pyproject.toml
```

Kết quả quality hiện tại: pytest, compileall, TOML/YAML parse và secret scan
pass; Ruff/mypy/Docker không chạy được vì thiếu executable.

## 7. Các file và thành phần liên quan

- `pyproject.toml`: khai báo Python `>=3.12,<3.13` và dependency
  `psycopg[binary]`.
- `src/talentaudit/main.py`: tạo FastAPI app ở module scope qua `app = create_app()`.
- `src/talentaudit/adapters/db/health.py`: database health checker dùng
  SQLAlchemy/psycopg.
- `src/talentaudit/api/health.py`: route `/health` và `/ready`.
- `src/talentaudit/config.py`: `Settings`, database URL và timeout.
- `tests/unit/test_health.py`: fake checker cho happy/failure path.
- `tests/unit/test_config.py`: kiểm tra settings và chặn non-PostgreSQL URL.
- `Dockerfile`: cài project vào image Python 3.12.
- `docker-compose.yml`: PostgreSQL 16 và app, app phụ thuộc healthcheck của DB.
- `.env.example`: local configuration mẫu; mọi giá trị nhạy cảm phải được
  thay bằng [REDACTED] trong báo cáo.

## 8. Những thay đổi đã thực hiện trước khi lỗi xuất hiện

Trước lỗi, Milestone 0 đã được scaffold với:

1. `pyproject.toml` và dependency metadata.
2. FastAPI health/readiness routes.
3. `SqlAlchemyDatabaseHealthChecker`.
4. `app = create_app()` ở module scope.
5. Dockerfile, Compose, CI, pre-commit và unit tests.
6. Các package directory theo modular monolith architecture.

Implementation ban đầu của database checker tạo engine ngay trong constructor:

```python
self._engine: Engine = create_engine(
    database_url,
    connect_args={"connect_timeout": connect_timeout_seconds},
    pool_pre_ping=True,
)
```

Thay đổi này xảy ra trước khi chạy `python -m pytest`, và là nguyên nhân khiến
thiếu driver ảnh hưởng đến import/test collection thay vì chỉ ảnh hưởng đến
endpoint `/ready`.

## 9. Các cách sửa đã thử và kết quả

### Cách 1 — Chạy test với code ban đầu

- Kết quả: fail ở collection với `ModuleNotFoundError: No module named
  'psycopg'`.
- Nguyên nhân trực tiếp: eager engine construction trong module import path.

### Cách 2 — Chuyển database engine sang lazy initialization

Đã đổi `health.py` để lưu database URL/timeout và đặt
`self._engine: Engine | None = None`; `create_engine(...)` chỉ chạy trong
`check()`.

- Kết quả: `python -m pytest` pass `5 passed`.
- Lợi ích: `/health` và test app không còn yêu cầu import DB driver ngay khi
  process/module được load.

### Cách 3 — Chạy Uvicorn với `--app-dir src`

- Kết quả: server khởi động được và `/health` trả `200`.
- Lỗi `No module named 'talentaudit'` được xác định là vấn đề Python import
  path khi chạy từ source tree chưa được install editable.

### Cách 4 — Fail-closed cho lỗi import driver

Đã bổ sung `ImportError` vào nhóm exception được bắt trong database checker:

```python
except (ImportError, SQLAlchemyError, OSError):
    return False
```

- Kết quả: `/ready` trả `503` thay vì `500` khi `psycopg` chưa có.
- Không kiểm tra giả lập `/ready` = `200` với PostgreSQL thật trong môi trường
  hiện tại.

Không có cách sửa nào khác được thử sau thay đổi này.

## 10. Giả thuyết nguyên nhân hiện tại

### Nguyên nhân đã xác định

Interpreter local là Python `3.11.9`, không có package `psycopg`, trong khi
project khai báo driver này cho PostgreSQL. Code ban đầu eager-load engine trong
import path, làm lỗi dependency trở thành lỗi import/test collection.

### Nguyên nhân phụ đã xác định

Uvicorn không tự thêm `src` vào `sys.path` khi chạy từ repository root nếu
package chưa được cài; cần cài editable hoặc dùng `--app-dir src`.

### Cần xác minh thêm

- Python 3.12 clean environment có cài thành công `psycopg[binary]` từ
  `pyproject.toml` không.
- PostgreSQL Compose có đạt healthcheck và `/ready` có trả `200` không.
- Ruff/mypy có pass trên Python 3.12/CI không.
- Có cần tạo `uv.lock` hay không, vì tài liệu structure liệt kê file này nhưng
  Milestone 0 chưa khóa uv là dependency manager.

## 11. Ràng buộc kiến trúc cần tuân thủ

- Giữ modular monolith; không tách microservice trong MVP.
- FastAPI route chỉ xử lý HTTP; database check nằm ở adapter/interface được
  inject.
- Domain không được import FastAPI, Streamlit hoặc LLM SDK.
- PostgreSQL là database MVP; không thay bằng SQLite cho runtime chính.
- Cấu hình phải đi qua `Settings` và environment; không hard-code API key,
  secret, recipient hoặc connection string thật.
- `/health` là liveness; `/ready` là readiness và phải fail-closed khi DB chưa
  sẵn sàng, không làm lộ chi tiết nội bộ.
- Không log CV thô, email, số điện thoại, secret hoặc connection string.
- Python target là `3.12`; quality gates bắt buộc gồm Ruff, format check, mypy
  và pytest.
- Email thật mặc định tắt; không triển khai side effect ở Milestone 0.
- Không triển khai LangGraph nodes, OpenAI adapter, Streamlit UI, policy matcher
  hoặc workflow business logic trong issue này.

## 12. Trạng thái Git hiện tại và diff liên quan

### Trạng thái trước khi tạo báo cáo này

- Repository đã được khởi tạo local bằng `git init -b main`.
- Branch hiện tại: `main`.
- HEAD: `3f0d394 (HEAD -> main) chore: bootstrap TalentAudit project`.
- Working tree trước khi tạo file này: clean.
- Chưa cấu hình remote `origin`; chưa push lên GitHub.
- Commit gồm toàn bộ scaffold Milestone 0, 60 file.

### Trạng thái sau khi tạo báo cáo

File này là thay đổi mới chưa commit:

```text
?? docs/debugging/ISSUE-001.md
```

Không có code diff chưa commit trong các file liên quan. Lệnh sau đây trước
khi tạo issue report không trả output:

```text
git diff HEAD -- src/talentaudit/adapters/db/health.py src/talentaudit/main.py src/talentaudit/api/health.py pyproject.toml
```

### Diff logic liên quan đã nằm trong commit hiện tại

So với implementation gây lỗi ban đầu, thay đổi quan trọng là:

```diff
- self._engine: Engine = create_engine(...)
+ self._database_url = database_url
+ self._connect_timeout_seconds = connect_timeout_seconds
+ self._engine: Engine | None = None

+ if self._engine is None:
+     self._engine = create_engine(...)

- except (SQLAlchemyError, OSError):
+ except (ImportError, SQLAlchemyError, OSError):
```

## 13. Câu hỏi cụ thể cần agent chuyên sâu giải quyết

1. Trên Python 3.12 clean environment, dependency set hiện tại có cài và
   import được `psycopg[binary]` đúng cách không?
2. Với `docker compose up --build`, PostgreSQL có healthy trước khi app start
   và `GET /ready` có trả `200` không?
3. Có nên giữ `--app-dir src` trong README hay bắt buộc editable install để
   command runtime ngắn hơn?
4. Ruff và mypy strict có phát hiện lỗi typing/format nào trong implementation
   hiện tại không?
5. Theo dependency-management policy của project, có cần tạo và commit
   `uv.lock` trong Milestone 0 không, hay để sau khi uv được chọn chính thức?

Không tiếp tục thay đổi code trong phạm vi ISSUE-001 này cho đến khi các câu hỏi
trên được xác minh trong môi trường Python 3.12/Docker phù hợp.
