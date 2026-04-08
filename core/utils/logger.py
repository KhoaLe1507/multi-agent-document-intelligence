# core/utils/logger.py
import sys
from loguru import logger
from pathlib import Path

# Đảm bảo thư mục logs tồn tại
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Xóa cấu hình mặc định mờ nhạt của Python
logger.remove()

# 1. Log ra màn hình Terminal (Có màu sắc để dễ nhìn)
logger.add(
    sys.stdout, 
    colorize=True, 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO" # Đi thi thì để INFO cho đỡ rối mắt
)

# 2. Log ra file (Lưu giữ mọi thứ kể cả DEBUG để traceback khi submit sai)
logger.add(
    "logs/agent_pipeline.log", 
    rotation="10 MB",     # Đầy 10MB tự tạo file mới
    retention="3 days",   # Xóa log cũ sau 3 ngày
    compression="zip",    # Nén file log cũ
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

agent_logger = logger