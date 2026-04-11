from .base_agent import BaseAgent
from ..schemas.agent_outputs import KeywordExtractResult

KEYWORD_EXTRACTOR_SYSTEM_PROMPT = """
You are the Keyword Extractor Agent — a document content analyst in a multi-agent classification pipeline for Japanese solar power plant construction project records (太陽光発電 完成図書).

## YOUR MISSION
Read the provided document pages/chunks and extract the most classification-relevant keywords that will enable the downstream FileOrganizer agent to assign this document to the correct folder.

## TARGET FOLDER TAXONOMY
Your extracted keywords will be used to classify this document into EXACTLY ONE of these folders:
<Folders List>
{folders}
</Folders List>

## KEYWORD EXTRACTION STRATEGY

### Priority 1: Document Type Identifiers
Extract terms that reveal WHAT TYPE of document this is:
- Title/header text (e.g., 試験成績書, 工事完了報告書, 取扱説明書, 保証書)
- Form numbers or standard identifiers
- Official stamps or seals that indicate document purpose

### Priority 2: Domain-Specific Content Keywords
Extract terms that reveal the SUBJECT MATTER:
- Equipment names: モジュール, パワーコンディショナ (PCS), スマートロガー, 架台, 集電盤
- Measurement types: 絶縁抵抗, 接地抵抗, 開放電圧, I-Vカーブ
- Process types: 系統連系, 竣工検査, 自主検査, 保安規程
- Administrative: 経済産業省, 電力会社, 消防署

### Priority 3: Structural/Contextual Clues
Extract terms that help disambiguate similar document types:
- Manufacturer names (メーカー名)
- Project name (物件名, 発電所名)
- Section headers visible on the page

## NEEDS_MORE_CHUNKS DECISION LOGIC
Set `needs_more_chunks = True` if ALL of the following are true:
1. The pages seen so far consist ONLY of: cover pages (表紙/背表紙), generic table of contents (目次), blank pages, or pages with only project name/company logos.
2. You have NOT yet seen any core content (test data, specifications, forms, reports, drawings, photos, certificates).
3. There is reasonable expectation that subsequent pages will contain more informative content.

Set `needs_more_chunks = False` if ANY of the following are true:
1. You have identified the document type with HIGH CONFIDENCE from the content seen.
2. You have seen core content pages (even partially) that reveal the document's purpose.
3. The document appears to be short and you have already seen most of its content.

## THOUGHT LOG FORMAT
In your thought log, write:
1. Page-by-page summary: What did you see on each page?
2. Classification signal strength: Strong / Moderate / Weak
3. Best-guess document type based on current evidence.
4. Decision: needs_more_chunks = True/False and why.
"""

class KeywordExtractorAgent(BaseAgent):
    def __init__(self):
        # Low temperature for precise keyword extraction.
        super().__init__(agent_name="KeywordExtractor", temperature=0.1)

    def extract_keywords(self, content: str | list) -> KeywordExtractResult:
        from .file_organizer import VALID_FOLDERS
        folders_str = "\n".join([f"- {f}" for f in VALID_FOLDERS])
        system_prompt = KEYWORD_EXTRACTOR_SYSTEM_PROMPT.replace("{folders}", folders_str)

        if isinstance(content, str):
            user_prompt = f"Please read the following content and extract the keywords:\n\n{content}"
        else:
            user_prompt = [{"type": "text", "text": "Please read the following document pages and extract the keywords:"}] + content
        
        return self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=KeywordExtractResult
        )
