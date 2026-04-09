# main.py
from dotenv import load_dotenv
from core.config.settings import settings
from dataProvider import ProviderService
from core.pipeline import SystemPipeline
from core.utils.logger import agent_logger

def main():
    # 1. Load các biến môi trường
    load_dotenv()
    
    agent_logger.info("HỆ THỐNG OCR MULTI-AGENTS ĐÃ KHỞI ĐỘNG ")
    
    try:
        # 2. Khởi tạo DataProvider (Giao tiếp Server)
        provider = ProviderService(
            base_url=settings.BASE_URL, 
            api_key=settings.COMPETITION_API_KEY
        )
        provider.create_session()
        
        # 3. Gắn DataProvider vào Pipeline
        pipeline = SystemPipeline(provider)
        
        # 4. Kích hoạt vòng lặp thi đấu tự động
        # (Nếu đang test, bạn có thể gọi pipeline.process_single_task() thay vì run_continuous)
        pipeline.process_single_task()
        # pipeline.run_continuous()
        
    except Exception as e:
        agent_logger.critical(f"Hệ thống sập do lỗi ở cấp cao nhất: {e}")

if __name__ == "__main__":
    main()