Prompt để SOL sửa lỗi mới mà dự án đang gặp phải.

Hãy đọc:

- AGENTS.md
- docs/debugging/ISSUE-001.md
- Những file mã nguồn được ISSUE-001.md nhắc đến

Nhiệm vụ của bạn là chẩn đoán nguyên nhân gốc của lỗi.

Trước khi chỉnh sửa code:

1. Xác minh lỗi bằng các bước tái hiện trong báo cáo.
2. Kiểm tra những giả thuyết đã được ghi lại.
3. Phân biệt nguyên nhân gốc với triệu chứng.
4. Đề xuất phương án sửa nhỏ nhất, an toàn nhất và phù hợp với kiến trúc TalentAudit.
5. Nêu những test cần bổ sung để lỗi không tái diễn.

Nếu báo cáo thiếu dữ liệu quan trọng, hãy nêu chính xác dữ liệu hoặc lệnh còn thiếu. Không suy đoán giá trị cấu hình bí mật.

Sau khi xác định được nguyên nhân, hãy:

- Triển khai bản sửa nếu có đủ bằng chứng.
- Chạy test, lint và type checking liên quan.
- Cập nhật docs/debugging/ISSUE-001.md với:
  - Root cause
  - Fix applied
  - Verification results
  - Prevention
  - Status: RESOLVED hoặc BLOCKED

Không mở rộng sang tính năng khác và không commit/push khi chưa được yêu cầu.
