from .base_agent import BaseAgent
from ..schemas.agent_outputs import KeywordExtractResult

KEYWORD_EXTRACTOR_SYSTEM_PROMPT = """
You are a Document Reading Robot (Keyword Extractor).
Your task is to read parts of a document (chunks) and extract keywords, key phrases, or the most concise description of the document's content. Do not answer questions; only return the important keywords.

IMPORTANT RULES:
Later, your extracted keywords will be used to classify the document into EXACTLY ONE OF THE FOLLOWING 22 FOLDERS:
<Folders List>
{folders}
</Folders List>

Based on the list above, if the content you just read consists solely of cover pages, blank pages, generic tables of contents, and the context is NOT SUFFICIENT to determine exactly which folder it belongs to, set needs_more_chunks = True so the system can provide subsequent document pages.
If you have seen the core content (enough to confidently classify it), set needs_more_chunks = False.
You must exclusively output Structured Output format.
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
