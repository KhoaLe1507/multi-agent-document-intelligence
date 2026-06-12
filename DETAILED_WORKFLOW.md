# Detailed Multi-Agent Workflow

This document provides a detailed, code-aligned breakdown of the two primary workflows: Question-Answering (QA) and File Organization.

---
### Step 0: Task Route Agent
- **Objective:** Determine the user’s intent and decide whether the request is for Question Answering (QA) or File Organization. This is the first agent to operate in the system
- **Flow:**
    1.The agent receives the user’s request (task_prompt).
    2.It analyzes the request and compares it against predefined rules for the two main workflows.
    3.Based on this comparison, it decides and selects the most appropriate workflow (QA or Organization).
- **Input:** User request (task_prompt)
- **Output:** The name of the selected workflow (e.g., "QA") for the system to continue processing.

## 1. Question-Answering (QA) Workflow

**Objective:** To accurately extract specific information from a large set of documents to answer a user's query.

### Step 1: Pre-processing
- **Action:** All specified input files are exhaustively parsed into smaller `chunks`.
- **Details:** Each chunk is a dictionary containing its content (text or image), source filename, and its position within the document (e.g., page number). This creates a comprehensive list of all content (`all_chunks`) for detailed analysis.

### Step 2: File Location (`FileLocatorAgent`)
- **Objective:** To efficiently filter the initial `M` documents down to a smaller, relevant set of `N` target documents that likely contain the answer.
- **Flow:**
    1. The agent receives the user's query and summaries of all available documents.
    2. It analyzes this information to identify the most relevant files.
- **Input:** User query (`task_prompt`), document summaries.
- **Output:** A `FileLocatorResult` object containing a list of `target_files` that are highly likely to contain the required information.

### Step 3: Planning (`PlannerAgent`)
- **Objective:** To deconstruct the user's high-level query into a structured, actionable extraction plan.
- **Flow:**
    1. The agent analyzes the user's query (`task_prompt`).
    2. It formulates a detailed `Extraction Guideline` that specifies exactly what data points to look for.
    3. It also generates a list of `target_keywords` to help the next agent quickly find relevant sections.
- **Input:** User query (`task_prompt`).
- **Output:** A `PlannerResult` object containing the `guideline` and `keywords`.

### Step 4: Extraction (`ExtractorAgent`)
- **Objective:** To meticulously scan the `target_files` and extract the precise data requested by the `PlannerAgent`.
- **Flow:**
    1. All chunks belonging to the `target_files` are collected.
    2. The agent processes each chunk in parallel.
    3. For each chunk, it strictly follows the `Extraction Guideline` and uses `target_keywords` to locate information.
    4. If relevant data is found, it is extracted *exactly* as it appears in the chunk.
- **Input:** A single `DocumentChunk`, the `Extraction Guideline`, and `target_keywords`.
- **Output:** A list of `ExtractionResult` objects. Each object contains the found data, a `found_information` flag, and a confidence score. Only results with `found_information: True` are passed on.

### Step 5: Synthesis (`SynthesizerAgent`)
- **Objective:** To assemble the disparate pieces of extracted data into a single, coherent, and final answer.
- **Flow:**
    1. The agent receives the user's query and all successful `ExtractionResult` pieces.
    2. It prioritizes results with the highest confidence scores.
    3. It then constructs a complete, well-formatted answer that directly addresses the user's query.
- **Input:** User query (`task_prompt`), list of `ExtractionResult` objects.
- **Output:** A `SynthesisResult` object containing the `final_answer` and a `thought_log` detailing its reasoning.

### Step 6: Review (`ReviewerAgent`)
- **Objective:** To perform a final quality check on the answer for accuracy, completeness, and relevance.
- **Flow:**
    1. The agent examines the `final_answer`, the original `prompt_template`, and the `thought_log`.
    2. It validates that the answer is logical, non-fabricated, and perfectly addresses the user's request.
    3. If the review fails, the task can be re-routed to the `SynthesizerAgent` for correction.
- **Input:** `prompt_template`, `final_answer`, `thought_log`.
- **Output:** A `ReviewResult` object (`passed` or `failed`).

---

## 2. File Organization Workflow

**Objective:** To quickly classify documents into predefined folders based on their primary content, without needing to read them in full.

### Step 1: Pre-processing & Keyword Extraction (`KeywordExtractorAgent`)
- **Action:** Instead of reading the entire file, the workflow intelligently "skims" each document to find its core purpose. This is done in parallel for all files.
- **Details:**
    1. **Cache Check:** First, the system checks if keywords for a specific file have been extracted and cached previously. If so, it reuses the cached result to save time.
    2. **Iterative Skimming:** If no cache is found, the `KeywordExtractorAgent` begins an iterative process:
        - It parses and analyzes the document in batches (e.g., 3 chunks at a time).
        - After each batch, the agent decides if it has enough information (`needs_more_chunks: False`) or if it needs to read the next batch to understand the document's context.
        - This continues until the agent is confident about the document's keywords or a set limit is reached.
    3. **Content Handling:** The agent can process both text and images within the chunks to extract relevant keywords.
- **Input:** A file path.
- **Output:** A `KeywordExtractResult` object containing a list of `keywords` and a `thought_log`.

### Step 2: File Organization (`FileOrganizerAgent`)
- **Objective:** To map each file to its correct destination folder based on the extracted keywords.
- **Flow:**
    1. The agent receives an `enhanced_file_list`, which pairs each filename with its corresponding keywords generated in the previous step.
    2. It also receives the user's classification prompt and the list of valid destination folders.
    3. It then logically matches the keywords for each file to the most appropriate folder and plans the move.
- **Input:** `enhanced_file_list`, `prompt_template`, list of valid folders.
- **Output:** A `FileOrganizationResult` object containing a list of `file_moves` (e.g., `{"source": "a.pdf", "destination": "Reports/2023"}`) and a `thought_log`.


### Step 3: Review (`ReviewerAgent`)
- **Objective:** To ensure the classification logic is sound.
- **Flow:** The agent evaluates the `thought_log` from the `FileOrganizerAgent` against the user's `prompt_template` to confirm the classification decisions are reasonable and correct.
- **Input:** `prompt_template`, `thought_log`.
- **Output:** A `ReviewResult` object (`passed` or `failed`).
