# 05 — State, Reducer và workflow LangGraph

## 1. State design principles

- State là dữ liệu workflow cần truyền giữa nodes, không phải nơi chứa mọi database record.
- Dùng ID/reference cho dữ liệu lớn; tránh giữ toàn bộ binary PDF.
- Node trả về delta, không trả lại toàn state.
- Field có concurrent write phải có reducer.
- LLM output đi qua Pydantic trước khi ghi vào state.
- State cần JSON-serializable nếu đi qua persistence/interrupt.

## 2. Suggested state

```python
from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class EvidenceRef(TypedDict):
    document_id: str
    section: str
    start: int
    end: int
    text: str


class ReviewOpinion(TypedDict):
    reviewer: Literal["TECH", "HIRING"]
    score: float
    confidence: float
    strengths: list[str]
    concerns: list[str]
    missing_information: list[str]
    evidence_refs: list[EvidenceRef]


class WorkflowError(TypedDict):
    node: str
    code: str
    retryable: bool
    public_message: str


class TalentAuditState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]

    audit_id: str
    thread_id: str
    job_id: str
    document_id: str
    workflow_status: str

    cv_text: str
    candidate_profile: dict
    policy_result: dict

    review_opinions: Annotated[list[ReviewOpinion], add]
    rebuttals: Annotated[list[dict], add]
    errors: Annotated[list[WorkflowError], add]

    review_report: dict
    email_draft: str
    recruiter_action: Literal[
        "APPROVE",
        "EDIT",
        "REJECT_PROPOSAL",
        "REQUEST_MORE_REVIEW",
    ]
    recruiter_edits: dict
```

Trong code thật, thay `dict` bằng Pydantic model/TypedDict cụ thể sau khi contract được khóa.

## 3. Reducer contract

Reviewer node chỉ trả về phần mới:

```python
def tech_review_node(state: TalentAuditState) -> dict:
    opinion = build_tech_opinion(state)
    return {"review_opinions": [opinion]}
```

Không làm:

```python
return {
    "review_opinions": state["review_opinions"] + [opinion]
}
```

Vì reducer sẽ append thêm lần nữa và có thể tạo duplicate.

Reducer append cần lưu ý retry/replay có thể tạo bản ghi trùng nếu node không idempotent. Mỗi opinion nên có stable `opinion_id` hoặc được persist với unique key `(audit_id, reviewer, round, prompt_version)`.

## 4. Graph nodes and contracts

| Node | Input chính | Output delta | Có LLM? |
|---|---|---|---:|
| `validate_submission` | IDs, metadata | status/error | Không |
| `parse_cv` | document_id | cv_text | Không |
| `extract_profile` | cv_text | candidate_profile | Có |
| `match_policy` | profile + job | policy_result | Không |
| `route_review` | policy result | route | Không |
| `tech_review` | profile + JD | one opinion | Có |
| `hiring_review` | profile + JD | one opinion | Có |
| `rebuttal_*` | both opinions | one rebuttal | Có, optional |
| `synthesize` | policy + opinions | report + draft | Có |
| `human_review` | report + draft | recruiter payload | Interrupt |
| `enqueue_email` | approved content | outbox id | Không |

## 5. Routing rules

- `parse failed` → `NEEDS_REVIEW`.
- `hard policy failure` vẫn tạo report; không tự gửi thư từ chối.
- `borderline` + feature enabled → debate subgraph.
- `normal review` → parallel reviewers → synthesize.
- `REQUEST_MORE_REVIEW` → review lại với recruiter note và giới hạn số vòng.
- `APPROVE` → outbox.
- `EDIT` → validate edit → interrupt lại hoặc approve theo UI action rõ ràng.
- `REJECT_PROPOSAL` → kết thúc không gửi.

## 6. HITL payload

Interrupt payload nên chứa dữ liệu cần cho UI, không chứa object không serialize được:

```python
{
    "audit_id": "...",
    "report": {...},
    "email_draft": "...",
    "allowed_actions": [
        "APPROVE",
        "EDIT",
        "REJECT_PROPOSAL",
        "REQUEST_MORE_REVIEW",
    ],
}
```

Resume payload phải validate:

```python
{
    "action": "APPROVE",
    "edited_email": None,
    "recruiter_note": "Reviewed evidence and approved.",
}
```

## 7. Persistence requirements

- Compile graph với checkpointer phù hợp.
- API tạo một `thread_id` ổn định cho mỗi audit.
- Resume luôn dùng đúng `thread_id`.
- External side effect phải nằm sau interrupt và có idempotency key.
- Production-like demo dùng PostgreSQL checkpointer; in-memory chỉ dùng unit/local smoke test.

## 8. Candidate-support subgraph

State riêng cho candidate support nên nhỏ hơn audit state:

- question;
- intent;
- route confidence;
- retrieved facts/sources;
- specialist answers;
- final answer;
- escalation flag.

Không đưa toàn bộ CV vào support subgraph nếu câu hỏi không cần CV.

