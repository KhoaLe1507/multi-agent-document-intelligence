# 🌟 OCR Multi-Agents System

This project is a fully automated **Multi-Agent system** designed for complex document handling, data extraction, question answering (QA), and automated file organization. It leverages the latest AI architectures (such as OpenAI's Vision capabilities and Gemini) combined with structured data flows (Pydantic) to process PDFs, scan images, and spreadsheets effectively.

---

## 🏗 System Architecture

The system operates continuously as an autonomous AI engine rather than a static script.
- **DataProvider**: The interface coordinating with the server/API. It fetches new tasks, streams file downloads, and submits results back to the external system.
- **SystemPipeline**: The orchestrator that establishes an automated loop (`run_continuous`), routing tasks to the appropriate workflows.
- **Core Agents**: Decentralized AI "brains", each specialized for a specific role and collaborating within the overall workflow.

### Interaction Flow:
`Server/API` 🔄 **DataProvider** ➡️ **SystemPipeline** ➡️ **Workflow (QA / ORGANIZE)** ➡️ `Submit Results`

---

## 🌊 Core Workflows

Tasks are classified by the **TaskRouterAgent** into two primary categories and routed accordingly.

### 1. Data Organization Workflow
*Goal: Analyze document content, extract keywords, and classify the file into the correct target directory.*

1. **Download & Parse:** Downloads files and parses them (PDF/Image/Excel) into standard `DocumentChunk` elements.
2. **Parallel Keyword Extraction:** Utilizing `ThreadPoolExecutor`, the `KeywordExtractorAgent` concurrently skims multiple document chunks simultaneously (up to 5 parallel threads), extracting a comprehensive list of keywords without blocking the main workflow.
3. **Smart Classification:** The `FileOrganizerAgent` takes the list of files, empowered by their extracted keywords, and maps them to the appropriate folders according to the prompt's instructions.
4. **Submit & Report:** Pushes the classification response and the full step-by-step reasoning (`thought_log`) to the server.

### 2. Question Answering (QA) Workflow
*Goal: Automatically locate specific files out of a bundle, extract targeted data points, and synthesize a final answer.*

1. **Download & Parse:** Files are broken down into chunks (both text blocks and Vision-ready Base64 images).
2. **Iterative Multimodal Locator (The Scout):** 
   - `FileLocatorAgent` utilizes **Vision API Batching** to inherently "see" the first pages/chunks of all downloaded files concurrently in a single request.
   - **Iterative Loop Mechanism:** If the initial chunks lack sufficient context (e.g., just a blank cover page), the agent signals `requires_more_info = True`. The workflow automatically injects the subsequent pages into the next API query until the target files are confidently locked.
3. **Strategic Planning:** The `PlannerAgent` breaks down the user prompt into detailed OCR extraction guidelines.
4. **Parallel Extraction (The Sniper):** Driven by `ThreadPoolExecutor`, the `ExtractorAgent` systematically analyzes multiple specified chunks **in parallel**. This heavily mitigates API latency bottlenecks.
5. **Synthesis:** The `SynthesizerAgent` aggregates all extracted metrics and formulates the concise final answer.
6. **Submit & Report:** Synthesizer constructs a complete Thought Log of the whole procedure and sends it back alongside the response.

---

## 🤖 The AI Agents

All agents inherit from `BaseAgent`, ensuring consistent capabilities like `llm_retry` loops, Vision support, and Pydantic-driven Structured Outputs.

1. **`TaskRouterAgent`**: The gatekeeper determining if a task belongs to QA or Organize logic.
2. **`KeywordExtractorAgent`**: The speed-reader summarizing pages into robust keywords.
3. **`FileOrganizerAgent`**: The organizational expert mapping files to directories.
4. **`FileLocatorAgent`**: The multimodal scout accurately filtering relevant files by visually inspecting them.
5. **`PlannerAgent`**: The strategist formulating specific OCR search criteria.
6. **`ExtractorAgent`**: The diligent worker scanning pixels and tables for the desired data.
7. **`SynthesizerAgent`**: The final editor crafting the submission text.

---

## ⚙️ Agent Tuning & Customization

The system is easily configurable without deep structural rewrites:

### 1. Adjusting Behavior (Prompts)
- Agent consciousness and instructions live entirely inside `core/prompts/`.
- If an agent starts hallucinating or misses data, tweak their corresponding `SYSTEM_PROMPT` in Python.

### 2. Data Model Extensions (Schemas)
- The agents strictly output data based on `core/schemas/agent_outputs.py`.
- Need the Extractor to return a new attribute (e.g., `confidence_score_color`)? Simply add it to the Pydantic class.

### 3. Model Configuration
- AI models can be seamlessly swapped (e.g. Gemini 3.1 Pro -> GPT-4o) using `core/config/settings.py` or your `.env` variables.

---

## 🧪 Installation & Testing

### 1. Requirements Setup
```bash
# Recommended: Use 'uv' for fast sync
uv sync
source .venv/bin/activate

# Setup your Environment
cp .env.example .env
# Edit .env to add OPENAI_API_KEY
```

### 2. Running E2E Tests
We have built-in E2E tests validating the Iterative Locator Loop and Keyword Organization flows:
```bash
# Run all system tests
uv run pytest tests/ -v -s

# Test the QA flow dynamically
uv run pytest tests/test_flow_qa.py -s
```

### 3. Start The Automation Engine
To automatically listen and consume real tasks from the remote server:
```bash
uv run python main.py
```
*(By default, this runs `pipeline.process_single_task()`. Switch to `pipeline.run_continuous()` inside `main.py` for headless loops).*

---
*Note: Ensure your `OPENAI_API_KEY` supports Multimodal Vision limits, as the system relies heavily on parsing image arrays efficiently.*
