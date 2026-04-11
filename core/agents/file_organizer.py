# core/agents/file_organizer.py
from .base_agent import BaseAgent
from ..config.settings import settings
from ..prompts.organizer_prompts import ORGANIZER_SYSTEM_PROMPT, get_organizer_user_prompt
from ..schemas.agent_outputs import OrganizeResult

VALID_FOLDERS = [
    "1. 背表紙・表紙: 完成図書の背表紙および表紙。物件名、プロジェクト名、作成時期などの基本情報が含まれる書類。",
    "2. 目次・インデックス: 完成図書の目録、インデックス、引渡し書類目録。ドキュメント全体の構成および項目リストを定義する書類。",
    "3. 備品引渡リスト: 鍵、予備部材、マニュアル等の備品一式を顧客に引き渡した際のリストおよび受領書。",
    "4. 工事完了報告書: 工事完了届、引渡書、工事完了報告書。プロジェクトの完成および引渡しを証明する書類。",
    "5. 工事工程表: 工事の計画および実績を示すスケジュール表。着工日、完了日、各工程の進捗が記録されたもの。",
    "6. 竣工図面・施工図面: 位置図、配置図、単線結線図、ストリング図、機器配置図等、施工完了時の状態を正確に示す図面一式。",
    "7. 試験成績書・検査表: 機器の動作試験、絶縁抵抗測定、接地抵抗測定等の検査結果を記録した合格判定書類。",
    "8. 自主検査表: 施工業者による竣工検査、社内検査の記録。自主検査チェックシートや是正事項の報告書。",
    "10. 機器構成表・一覧: 採用された主要機器（モジュール、PCS、監視装置等）のメーカー、型式、スペック、数量を一覧化した書類。",
    "11. PCS・パワコン: パワーコンディショナ（PCS）に関連する個別仕様書、試験成績書、納品書、承認図等。",
    "12. モジュール: 太陽電池モジュールに関連する仕様書、フラッシュレポート（検査成績書）、納品書、シリアル番号リスト等。",
    "13. 監視装置・通信機器: スマートロガー、ゲートウェイ、ルーター等の通信機器に関する仕様書、試験成績書、アカウント設定、接続図等。",
    "14. 納入機器仕様書: プロジェクトに納入された上記以外の各種機器（集電盤、架台、金具、計測器等）のカタログおよび仕様書。",
    "15. 取扱・操作説明書: 機器の操作マニュアル、クイックスタートガイド、自立運転時の操作手順や復帰手順書。",
    "16. 行政手続き書類: 経済産業省（保安規程、自己確認結果届出等）や消防署、自治体への申請・届出・認可書類。",
    "17. 電力手続き書類・回答: 電力会社への接続検討、系統連系申込、工事負担金、連系契約のご案内、回答書、整定値リスト等。",
    "18. 保証書: 各主要機器および施工内容に対するメーカー保証書、システム保証書、品質保証規定。",
    "19. 工事写真・写真帳: 施工プロセス、各工程の完了、機器の設置状態、定点観測、メーターの製造番号・指針等を記録した写真。",
    "20. 強度計算書類: 架台や金具の耐風圧、積雪荷重、地耐力等の設備強度検討書。行政届出の根拠資料。",
    "22. その他・マニフェスト: 産業廃棄物管理票（マニフェスト）、校正証明書（日射計・気温計）、主任技術者情報、上記に属さない雑書類。",
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