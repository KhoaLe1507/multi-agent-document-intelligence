# core/parsers/table_extractor.py
import pandas as pd
from pathlib import Path
from ..utils.logger import agent_logger
from ..exceptions.agent_errors import ParsingError
from ..schemas.data_types import DocumentChunk

def extract_tables(file_path: str) -> list[DocumentChunk]:
    path = Path(file_path)
    chunks = []
    
    try:
        if path.suffix == '.csv':
            df = pd.read_csv(file_path)
            markdown_table = df.to_markdown(index=False)
            chunks.append(DocumentChunk(
                chunk_type="table", content=markdown_table, file_name=path.name
            ))
            
        elif path.suffix in ['.xlsx', '.xls']:
            # Đọc từng sheet trong Excel
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # Lọc bỏ các cột/hàng rỗng hoàn toàn để tiết kiệm token
                df.dropna(how='all', inplace=True)
                df.dropna(axis=1, how='all', inplace=True)
                
                markdown_table = f"### Sheet: {sheet_name}\n" + df.to_markdown(index=False)
                chunks.append(DocumentChunk(
                    chunk_type="table", content=markdown_table, file_name=path.name, page_number=1
                ))
                
        agent_logger.success(f"Đã chuyển đổi {path.name} thành Markdown Table.")
        return chunks
        
    except Exception as e:
        agent_logger.error(f"Lỗi đọc file bảng tính {path.name}: {e}")
        raise ParsingError(f"Không thể parse Excel/CSV: {str(e)}")