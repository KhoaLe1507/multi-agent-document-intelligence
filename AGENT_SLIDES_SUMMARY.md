# Agent Roles for Presentation

---

## TaskRouter Agent (The Dispatcher)

-   **Role**: The first agent to act. It reads the user's request and decides which workflow to use.

-   **Objective**: To classify the task as either "Question Answering" (QA) or "File Organization".

-   **Input**: The user's initial prompt.

-   **Output**: A routing decision (e.g., "QA_WORKFLOW").

---

## QA | Planner Agent (The Architect)

-   **Role**: Deconstructs a complex question into a simple, actionable plan.

-   **Objective**: To create a detailed "what to find" guide for the Extractor Agent.

-   **Input**: The user's question.

-   **Output**: A structured extraction plan with guidelines and keywords.

---

## QA | FileLocator Agent (The Librarian)

-   **Role**: Scans the entire library to find the few documents relevant to the user's query.

-   **Objective**: To narrow down a large set of files to a small, targeted list.

-   **Input**: The user's query and document summaries.

-   **Output**: A list of relevant file paths.

---

## QA | Extractor Agent (The Miner)

-   **Role**: Reads the relevant documents and pulls out the exact pieces of information requested by the Planner.

-   **Objective**: To execute the extraction plan with high precision, finding and quoting data.

-   **Input**: A document chunk, extraction guidelines, and keywords.

-   **Output**: Pieces of extracted data, each with a confidence score.

---

## QA | Synthesizer Agent (The Author)

-   **Role**: Gathers all the extracted data pieces and assembles them into a final, coherent answer.

-   **Objective**: To write a complete, human-readable answer to the user's original question.

-   **Input**: The user's question and all extracted data pieces.

-   **Output**: The final, formatted answer.

---

## Organize | KeywordExtractor Agent (The Skimmer)

-   **Role**: Quickly reads the first few pages of a document to understand its main topic.

-   **Objective**: To identify the core purpose of a document by extracting key terms and titles.

-   **Input**: The first few chunks of a single file.

-   **Output**: A list of keywords that describe the file.

---

## Organize | FileOrganizer Agent (The Sorter)

-   **Role**: Uses the keywords from the Skimmer to decide which folder a file belongs in.

-   **Objective**: To map each file to its correct destination folder based on its content.

-   **Input**: A list of files with their associated keywords.

-   **Output**: A plan to move each file to a specific folder.

---

## Reviewer Agent (The Inspector)

-   **Role**: A quality control agent that checks the final output of either workflow.

-   **Objective**: To ensure the final answer (QA) or file classification (Organize) is accurate, logical, and complete.

-   **Input**: The final result and the original user request.

-   **Output**: A "pass" or "fail" judgment.
