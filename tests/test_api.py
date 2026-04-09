import os
from dotenv import load_dotenv
from dataProvider import ProviderService

# 1. Load biến môi trường từ file .env
load_dotenv()

API_KEY = os.getenv("COMPETITION_API_KEY")
BASE_URL = os.getenv("BASE_URL")

def main():
    if not API_KEY or not BASE_URL:
        print("Lỗi: Chưa tìm thấy COMPETITION_API_KEY hoặc BASE_URL trong file .env!")
        exit(1)

    print("Bắt đầu test module dataProvider...\n")
    
    # Khởi tạo Service
    provider = ProviderService(base_url=BASE_URL, api_key=API_KEY)
    
    # Bước 1: Tạo Session
    print(" Đang tạo session mới...")
    session = provider.create_session()
    print("Đã tạo Session thành công!")
    print(f"   - Session ID: {session.session_id}")
    print(f"   - Token hết hạn sau: {session.expires_in} giây\n")
    
    # Bước 2: Lấy Task
    print(" Đang lấy task tiếp theo...")
    task = provider.get_next_task()
    print("Đã lấy Task thành công!")
    print(f"   - Task ID: {task.task_id}")
    print(f"   - Prompt: {task.prompt_template}")
    print(f"   - Số lượng tài liệu đính kèm: {len(task.resources)} file\n")
    
    # Bước 3: Download file (Dạng stream)
    if not task.resources:
        print("ℹ️ Task này không có tài liệu đính kèm.")
        return

    print(" Đang tiến hành tải tài liệu...")
    
    # Thư mục gốc để lưu data tải về
    base_download_dir = "downloaded_data"
    
    for i, res in enumerate(task.resources, 1):
        # res.file_path có dạng: "Public/01_masked_.../xxx.pdf"
        # Tạo đường dẫn local: "downloaded_data/Public/01_masked_.../xxx.pdf"
        local_file_path = os.path.join(base_download_dir, res.file_path)
        
        # Lấy phần thư mục để tạo trước (VD: "downloaded_data/Public/01_masked_...")
        local_dir = os.path.dirname(local_file_path)
        os.makedirs(local_dir, exist_ok=True)
        
        print(f"   [{i}/{len(task.resources)}] Đang tải: {res.file_path.split('/')[-1]} ...")
        
        try:
            # Gọi hàm download
            saved_path = provider.download_file(download_token=res.token, save_path=local_file_path)
            print(f"   ️ Đã lưu tại: {saved_path}")
        except Exception as e:
            print(f"   Lỗi khi tải file {res.file_path}: {e}")

    print("\n Hoàn tất quá trình test (Chưa submit).")

if __name__ == "__main__":
    main()