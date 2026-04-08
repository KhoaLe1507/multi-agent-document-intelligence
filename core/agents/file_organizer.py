# core/agents/file_organizer.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.organizer_prompts import ORGANIZER_SYSTEM_PROMPT, get_organizer_user_prompt
from ..schemas.agent_outputs import OrganizeResult

VALID_FOLDERS = [
    "1. 背表紙・表紙",
    "2. 目次・インデックス",
    "3. 備品引渡リスト",
    "4. 工事完了報告書",
    "5. 工事工程表",
    "6. 竣工図面・施工図面",
    "7. 試験成績書・検査表",
    "8. 自主検査表",
    "10. 機器構成表・一覧",
    "11. PCS・パワコン",
    "12. モジュール",
    "13. 監視装置・通信機器",
    "14. 納入機器仕様書",
    "15. 取扱・操作説明書",
    "16. 行政手続き書類",
    "17. 電力手続き書類・回答",
    "18. 保証書",
    "19. 工事写真・写真帳",
    "20. 強度計算書類",
    "22. その他・マニフェスト",
]

class FileOrganizerAgent(BaseAgent):
    def __init__(self):
        # Nhiệt độ 0.0 để đảm bảo tính chính xác tuyệt đối khi map tên thư mục
        super().__init__(agent_name="FileOrganizer", temperature=0.0)

    def organize_files(self, task_prompt: str, file_list: list[str]) -> OrganizeResult:
        # Truyền thêm VALID_FOLDERS vào prompt
        user_prompt = get_organizer_user_prompt(task_prompt, file_list, VALID_FOLDERS)
        
        return self.call_llm(
            system_prompt=ORGANIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=OrganizeResult
        )