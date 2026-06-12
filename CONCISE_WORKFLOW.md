# Concise Multi-Agent Workflow

---

## 1. Question-Answering (QA) Workflow

### Step 1: Pre-processing
- **Objective:** To break down all input files into a comprehensive list of content chunks for detailed analysis.
- **Flow:** Every file is exhaustively parsed into smaller `chunks`, with each chunk containing its content (text/image), source filename, and position.

### Step 2: File Location (`FileLocatorAgent`)
- **Objective:** To efficiently filter down to a small, relevant set of documents that likely contain the answer.
- **Flow:** The agent analyzes the user's query against document summaries to identify the most relevant files for the task.

### Step 3: Planning (`PlannerAgent`)
- **Objective:** To deconstruct the user's query into a structured, actionable extraction plan.
- **Flow:** The agent analyzes the query to formulate a detailed `Extraction Guideline` and a list of `target_keywords` for the next agent.

### Step 4: Extraction (`ExtractorAgent`)
- **Objective:** To meticulously scan target documents and extract the precise data requested by the plan.
- **Flow:** The agent processes chunks from target files in parallel, strictly following the guideline to locate and extract information exactly as it appears.

### Step 5: Synthesis (`SynthesizerAgent`)
- **Objective:** To assemble the disparate pieces of extracted data into a single, coherent final answer.
- **Flow:** The agent receives all successful extractions, prioritizes those with high confidence, and constructs a complete, well-formatted answer.

### Step 6: Review (`ReviewerAgent`)
- **Objective:** To perform a final quality check on the answer for accuracy, completeness, and relevance.
- **Flow:** The agent examines the final answer against the original query and thought process to validate its logic and correctness.

---

## 2. File Organization Workflow

### Step 1: Pre-processing & Keyword Extraction (`KeywordExtractorAgent`)
- **Objective:** To intelligently "skim" each document to find its core purpose without reading the entire file.
- **Flow:** The workflow first checks for cached keywords. If none exist, it iteratively parses the document in small batches, deciding after each batch if it has enough information or needs to continue reading.

### Step 2: File Organization (`FileOrganizerAgent`)
- **Objective:** To map each file to its correct destination folder based on the extracted keywords.
- **Flow:** The agent receives a list of files paired with their keywords and logically matches them to the most appropriate folder to plan the move.

### Step 3: Review (`ReviewerAgent`)
- **Objective:** To ensure the classification logic is sound and correct.
- **Flow:** The agent evaluates the organizer's thought process against the original request to confirm the classification decisions are reasonable.
