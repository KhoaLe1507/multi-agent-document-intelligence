import sys
from datetime import datetime
from dotenv import load_dotenv

# Thêm logic để file chạy trực tiếp hiểu được module core/dataProvider
import os
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from core.config.settings import settings
from dataProvider import ProviderService
from core.pipeline import SystemPipeline
from core.utils.logger import agent_logger

def run_test():
    # 1. Load biến môi trường
    load_dotenv()
    
    # 2. Sinh tên file log gắn Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/test_pipeline_{timestamp}.txt"
    
    # 3. Phân nhánh Logger ra file mới chỉ dành cho lần bật test này
    agent_logger.add(
        log_filename,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | Agent Log - {message}",
        level="DEBUG",
        enqueue=True, # Xử lý đa luồng an toàn
        backtrace=True,
        diagnose=True
    )
    
    agent_logger.info(f"BẮT ĐẦU E2E TEST: Log toàn bộ luồng hoạt động sẽ lưu tại {log_filename}")
    
    try:
        # Bước 1 & 2: Khởi tạo Sessions
        agent_logger.info("Giai đoạn 1: Khởi tạo DataProvider & Gọi Session Token...")
        provider = ProviderService(
            base_url=settings.BASE_URL, 
            api_key=settings.COMPETITION_API_KEY
        )
        provider.create_session()
        
        # Bước 3: Lắp ráp Pipeline
        agent_logger.info("Giai đoạn 2: Lắp ráp DataProvider vào SystemPipeline...")
        pipeline = SystemPipeline(provider)
        
        # Bước 4: Chạy đúng 1 vòng lặp Task
        agent_logger.info("Giai đoạn 3: Bắt đầu xử lý 1 Task duy nhất (Fetch -> Download -> Suy Luận -> Submit)...")
        pipeline.process_single_task()
        
        agent_logger.success(f"THÀNH CÔNG: Đã xử lý và submit 1 Task hoàn chỉnh. Kiểm tra chi tiết tại: {log_filename}")
        
    except Exception as e:
        agent_logger.exception(f"THẤT BẠI: Vòng lặp Test E2E gặp lỗi. Trích xuất: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
