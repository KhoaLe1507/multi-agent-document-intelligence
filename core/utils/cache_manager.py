# core/utils/cache_manager.py
import os
import pickle
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")

# Một Cache Dictionary toàn cục (Global) tồn tại trong suốt vòng đời của process.
# Mapping: file_name -> Dictionary chứa các thuộc tính.
_GLOBAL_FILE_CACHE: Dict[str, Dict[str, Any]] = {}

class CacheManager:
    """
    Quản lý bộ nhớ đệm (Disk Cache + In-Memory Cache) chéo (Cross-Task).
    Giúp lưu trữ và tái sử dụng dữ liệu đã phân tích của các file xuất hiện nhiều lần ở nhiều Task khác nhau.
    Key sử dụng là file_name vì các định dạng thi đấu thường băm tên file thành mã MD5/UUID.
    Dữ liệu được lưu trữ trực tiếp dưới dạng file PICKLE tại thư mục ./cache để duy trì session.
    """
    
    @staticmethod
    def _get_file_path(file_name: str) -> str:
        # Tách lấy tên file thực tế (đề phòng file_name là một chuỗi path chứa / hoặc \)
        safe_name = file_name.replace("\\", "/").split("/")[-1]
        
        # Đảm bảo có thư mục cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, f"{safe_name}.pkl")

    @classmethod
    def get_cache(cls, file_name: str) -> Optional[Dict[str, Any]]:
        """Lấy toàn bộ dữ liệu cache của một file."""
        if file_name not in _GLOBAL_FILE_CACHE:
            # Thử load từ disk (ROM) nếu chưa có trong RAM
            file_path = cls._get_file_path(file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        _GLOBAL_FILE_CACHE[file_name] = pickle.load(f)
                except Exception:
                    pass
        return _GLOBAL_FILE_CACHE.get(file_name)

    @classmethod
    def update_cache(cls, file_name: str, key: str, value: Any):
        """Cập nhật một thuộc tính (VD: 'chunks', 'keyword_summary') vào cache của file (cả RAM và ROM)."""
        if file_name not in _GLOBAL_FILE_CACHE:
            # Thử load trước khi khởi tạo trắng
            cls.get_cache(file_name)
            if file_name not in _GLOBAL_FILE_CACHE:
                _GLOBAL_FILE_CACHE[file_name] = {}
                
        _GLOBAL_FILE_CACHE[file_name][key] = value

        # Sync xuống disk (ROM) để duy trì
        file_path = cls._get_file_path(file_name)
        try:
            with open(file_path, "wb") as f:
                pickle.dump(_GLOBAL_FILE_CACHE[file_name], f)
        except Exception as e:
            print(f"Error saving cache to disk for {file_name}: {e}")

    @classmethod
    def get_cached_item(cls, file_name: str, key: str) -> Optional[Any]:
        """Lấy một thuộc tính cụ thể từ cache."""
        cache = cls.get_cache(file_name)
        if cache:
            return cache.get(key)
        return None

    @classmethod
    def clear_all(cls):
        """Làm sạch toàn bộ cache trong RAM và ROM (hữu ích cho việc test)."""
        _GLOBAL_FILE_CACHE.clear()
        if os.path.exists(CACHE_DIR):
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith(".json") or filename.endswith(".pkl"):
                    try:
                        os.remove(os.path.join(CACHE_DIR, filename))
                    except Exception:
                        pass

