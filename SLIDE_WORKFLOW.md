# High-Level Agent Workflow (for Slides)

---

## Two Core Workflows

Based on the user's request, the **TaskRouter Agent** dispatches the job to one of two pipelines:

1.  **QA Workflow**: Extracts specific answers from documents.
2.  **Organize Workflow**: Classifies documents into folders.

---

## 1. QA (Question-Answering) Workflow

**Goal:** Find a precise answer to a user's question.

-   **`FileLocatorAgent` (The Librarian)**
    -   **Role:** Scans all documents to find the few that are relevant to the query.

-   **`PlannerAgent` (The Architect)**
    -   **Role:** Breaks down the user's question into a detailed "what to find" extraction plan.

-   **`ExtractorAgent` (The Miner)**
    -   **Role:** Executes the plan, reading only the relevant documents to pull out the exact pieces of information.

-   **`SynthesizerAgent` (The Author)**
    -   **Role:** Collects all the extracted pieces and writes the final, complete answer.

-   **`ReviewerAgent` (The Inspector)**
    -   **Role:** Double-checks the final answer for accuracy and completeness.

---

## 2. Organize (File Organization) Workflow

**Goal:** Quickly sort files into the correct folders.

-   **`KeywordExtractorAgent` (The Skimmer)**
    -   **Role:** Quickly reads the first few pages of each file to identify its main topic and keywords.

-   **`FileOrganizerAgent` (The Sorter)**
    -   **Role:** Uses the keywords to decide which folder each file belongs in.

-   **`ReviewerAgent` (The Inspector)**
    -   **Role:** Verifies that the classification logic is sound and the files are sorted correctly.
