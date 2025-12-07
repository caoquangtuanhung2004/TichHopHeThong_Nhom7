# services/logging_service.py

import logging
import os

# Tạo thư mục 'logs' nếu chưa có
os.makedirs("logs", exist_ok=True)

# Tạo logger riêng cho ứng dụng
logger = logging.getLogger("hrm_app")
logger.setLevel(logging.INFO)

# Tránh duplicate handler khi import nhiều lần
if not logger.handlers:
    # Handler ghi vào file
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Định dạng log: [2025-12-07 10:30:00] INFO - Nội dung
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optional: Ghi ra console khi debug (nếu muốn)
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)