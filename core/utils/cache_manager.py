# core/utils/cache_manager.py
from typing import Dict, Any, Optional

# Một Cache Dictionary toàn cục (Global) tồn tại trong suốt vòng đời của process.
# Mapping: file_name -> Dictionary chứa các thuộc tính.
_GLOBAL_FILE_CACHE: Dict[str, Dict[str, Any]] = {}

class CacheManager:
    """
    Quản lý bộ nhớ đệm (In-Memory Cache) chéo (Cross-Task).
    Giúp lưu trữ và tái sử dụng dữ liệu đã phân tích của các file xuất hiện nhiều lần ở nhiều Task khác nhau.
    Key sử dụng là file_name vì các định dạng thi đấu thường băm tên file thành mã MD5/UUID.
    """
    
    @classmethod
    def get_cache(cls, file_name: str) -> Optional[Dict[str, Any]]:
        """Lấy toàn bộ dữ liệu cache của một file."""
        return _GLOBAL_FILE_CACHE.get(file_name)

    @classmethod
    def update_cache(cls, file_name: str, key: str, value: Any):
        """Cập nhật một thuộc tính (VD: 'chunks', 'keyword_summary') vào cache của file."""
        if file_name not in _GLOBAL_FILE_CACHE:
            _GLOBAL_FILE_CACHE[file_name] = {}
        _GLOBAL_FILE_CACHE[file_name][key] = value

    @classmethod
    def get_cached_item(cls, file_name: str, key: str) -> Optional[Any]:
        """Lấy một thuộc tính cụ thể từ cache."""
        cache = cls.get_cache(file_name)
        if cache:
            return cache.get(key)
        return None

    @classmethod
    def clear_all(cls):
        """Làm sạch toàn bộ cache (hữu ích cho việc test)."""
        _GLOBAL_FILE_CACHE.clear()
