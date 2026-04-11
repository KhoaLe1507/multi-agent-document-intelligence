# core/schemas/agent_outputs.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class TaskRoutingResult(BaseModel):
    """Output of TaskRouterAgent: Determines the pipeline branch."""
    task_type: Literal["QA", "ORGANIZE"] = Field(
        ..., 
        description="If the request is to sort/move files, choose ORGANIZE. If it's to extract information/answer questions, choose QA."
    )
    reasoning: str = Field(
        ..., 
        description="Briefly explain the reasoning for classifying the task into the chosen category."
    )

class KeywordExtractResult(BaseModel):
    """Output of KeywordExtractorAgent: Generates keywords representing the document content."""
    thought_log: str = Field(
        ...,
        description="Brief explanation of why these keywords were selected."
    )
    keywords: List[str] = Field(
        ...,
        description="A list of keywords, main ideas, or structural summaries extracted from this chunk."
    )
    needs_more_chunks: bool = Field(
        False,
        description="True if the current chunks only contain cover pages, blank pages, or meaningless indexes, and you CANNOT confidently map the document into one of the 22 Valid Folders yet. False if you have seen enough core content to confidently classify it."
    )


class PlannerResult(BaseModel):
    """Output of PlannerAgent: The tactical extraction plan."""
    thought_log: str = Field(
        ...,
        description="Full analytical reasoning: What does this document contain? Where should we look? What are the specific target goals?"
    )
    extraction_guidelines: str = Field(
        ..., 
        description="Detailed, step-by-step instructions for the ExtractorAgent on how to find the information in the document."
    )
    target_keywords: List[str] = Field(
        ..., 
        description="A list of keywords or patterns that require special attention."
    )

class ExtractionResult(BaseModel):
    """Output of ExtractorAgent: The result of data scraping from a single chunk."""
    thought_log: str = Field(
        ...,
        description="The process of scanning details in the chunk: What was seen? Why is it useful or not useful?"
    )
    found_information: bool = Field(
        ..., 
        description="True if useful information fulfilling the task requirement was found, False if the chunk contains no relevant information."
    )
    extracted_data: Optional[str] = Field(
        None, 
        description="The extracted data. Preserve original formatting if possible. Return null if found_information is False."
    )
    confidence_score: float = Field(
        ..., 
        description="The agent's confidence score for the extracted information, ranging from 0.0 to 1.0."
    )

class SynthesisResult(BaseModel):
    """Output of SynthesizerAgent: Finalizes the ultimate result for submission."""
    final_answers: List[str] = Field(
        ..., 
        description="The list of final answers, formatted strictly according to the system's requested format (e.g., tag format)."
    )
    thought_log: str = Field(
        ..., 
        description="The thought log: How did the AI analyze the documents to arrive at this answer? (Used by the evaluator for transparency scoring)."
    )

class FileAllocation(BaseModel):
    file_name: str = Field(..., description="The exact file name (e.g., 'abc.pdf').")
    folder_name: str = Field(..., description="The assigned folder name from the Taxonomy list.")

class OrganizeResult(BaseModel):
    """Output of FileOrganizerAgent: The thought_log is the core deliverable for grading."""
    thought_log: str = Field(
        ..., 
        description="The full reasoning process and list of file-to-folder allocations. (e.g., 'Based on the instruction, I classified file A into folder X because...')"
    )
    file_allocations: list[FileAllocation] = Field(
        ...,
        description="List of file allocation objects, mapping each file to its target folder."
    )

class FileLocatorResult(BaseModel):
    """Output of FileLocatorAgent: Identifies the exact files to process or requests more data."""
    target_file_names: list[str] = Field(
        ..., 
        description="The files currently confirmed for selection. If uncertain, DO NOT include the file in this array."
    )
    reasoning: str = Field(
        ..., 
        description="Explanation of why these specific file(s) were chosen or why more information is needed."
    )
    requires_more_info: bool = Field(
        False,
        description="Signals True if any file cannot be determined yet (e.g., current page is a cover, index, empty table, etc.) and requires the next page/chunk to be loaded for analysis."
    )
    files_needing_more_chunks: List[str] = Field(
        default_factory=list,
        description="A list of specific filenames that require the system to load their next page/chunk (used if requires_more_info = True)."
    )

class ReviewResult(BaseModel):
    """Output of ReviewerAgent: Quality assurance of the agent's output before submission."""
    is_acceptable: bool = Field(
        ...,
        description="True if the answer and thought log strictly satisfy the task instruction. False if there are deviations, missing information, or illogical reasoning."
    )
    issues: List[str] = Field(
        default_factory=list,
        description="If is_acceptable = False, detail the errors that need fixing (e.g., 'File A classified illogically' or 'Answer missing building information')."
    )