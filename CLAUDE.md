# Hướng dẫn cho Claude Code

Việc đang làm: nâng cấp Quant 3D Matrix từ V33 lên V34 theo docs/KE_HOACH_NANG_CAP_V34.md. Đọc toàn bộ file đó trước khi làm bất cứ việc gì.

Quy tắc bắt buộc:
- Làm tự động, liên tục, theo đúng thứ tự trong kế hoạch: viết → backtest → sửa → backtest lại → làm tầng tiếp theo, đến khi xong hết. Không dừng lại hỏi người dùng.
- Làm trên nhánh `nang-cap-v34`. Không sửa TOOL_Agent_Quant_Core_v32.py và .github/workflows/run_quant.yml cho tới bước tích hợp cuối cùng.
- Ghi mọi lần backtest vào docs/NHAT_KY_BACKTEST.md. Trước khi tiếp tục, đọc nhật ký để biết đã làm đến đâu.
- Tiếng Việt có dấu đầy đủ trong mọi nội dung; tên file, tên thư mục viết không dấu.
