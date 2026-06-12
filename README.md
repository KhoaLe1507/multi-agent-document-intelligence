# 🌟 OCR Multi-Agents System

This project is a fully automated **Multi-Agent system** designed for complex document handling, data extraction, question answering (QA), and automated file organization. It leverages the latest AI architectures (such as OpenAI's Vision capabilities and Gemini) combined with structured data flows (Pydantic) to process PDFs, scan images, and spreadsheets effectively.

---

## 🏗 System Architecture & Key Features

The system operates continuously as an autonomous AI engine rather than a static script. It boasts robust enterprise-grade features:

- **Parallel Processing Engine**: Deeply integrates `ThreadPoolExecutor` to shatter network latency bottlenecks. Agents fractionate documents and extract intelligence in parallel multiple threads.
- **Global Memory (CacheManager)**: A centralized RAM cache repository. When a file is recognized again (as frequently happens across tasks), all the processed chunks, translations, and keywords are retrieved instantly (`[Cache HIT]`). This slashes redundant API token costs to **zero** and provides a practically 0ms latency boost.
- **Self-Correction & Quality Assurance**: Outputs are strictly audited by the independent **ReviewerAgent**. If the agent catches contradictions, logical fallacies, or hallucinated facts, it halts the submission. The workflow then enters an iterative feedback loop, forcing the specific generator agents to correct their answers before finalizing.
- **Universal Format Intake**: Flawlessly reads offline PDFs, converts Excel `.xlsx` sheets natively to Markdown Tables (processed without heavy Vision calls), and uses Visual Intelligence (Image API) dynamically for pure-image scans where text arrays fail.

---

## 🌊 Detailed Workflow Sequences

### 1. Data Organization Workflow
*Goal: Analyze document bulk, extract core keyword identities, and map files precisely to a strict directory taxonomy.*

- **Step 1: Parse & Cache Engine:** The system fetches attached data (`file_router`). Excel files become Markdown Tables, while PDFs form a matrix of `DocumentChunk`. The `CacheManager` jumps in—identifying if the files have already been dissected previously.
- **Step 2: 360-Degree Keyword Scouting (Text & Vision):** The `ThreadPoolExecutor` dispatches multiple `KeywordExtractorAgent` instances simultaneously. Crucially, these instances can inject `image_base64` feeds dynamically; this allows pure-scan image files to still yield high-quality keywords in a matter of seconds. Keywords are instantly globally cached.
- **Step 3: Smart Algorithmic Mapping:** The `FileOrganizerAgent` takes the entire summarized bundle (File Names + Keywords) alongside the strict user rulebook, structuring its neural choices down into a concrete JSON mapping schema.
- **Step 4: The Sentinel Loop (Self-Correction):** The strict `ReviewerAgent` sweeps the outputs. If the rationale behind placing "design_blueprint.pdf" inside the "Invoices" folder lacks logic, it throws an error list (`issues`). The workflow traps this failure in a `while` loop, forcefully feeding `[LƯU Ý TỪ REVIEWER LẦN TRƯỚC]` back to the `FileOrganizerAgent` up to 2 times to correct the mistake.
- **Step 5: Final Persistence:** Successfully formulated mapping decisions and Thought Logs are written to the local submissions JSONL file.

### 2. Question Answering (QA) Workflow
*Goal: Autonomously scout through dozens of files, zero in on targeted data, and synthesize a cohesive contextual answer.*

- **Step 1: Preparation:** As always, robust formatting and global cache verification occur to spare tokens.
- **Step 2: Iterative Vision Scouting (The Scout Loop):** 
  - Submitting hundreds of pages to locate an answer is inefficient. The `FileLocatorAgent` is fed a batch view solely of the *first pages* of every file at once via Vision APIs.
  - If the initial sample lacks evidence (e.g. encountering blank covers), the agent triggers a `requires_more_info = True` flag. The environment inherently advances a page in the suspected files and loops the prompt. Once a file proves definitively relevant (or irrelevant), the selection scope is locked.
- **Step 3: Tactical Breakdown (Strategic Planning):** The `PlannerAgent` intercepts the raw user query and reformulates it. It translates generic questions into rigorous *extraction guidelines* alongside strict *target keywords* for the extraction troops.
- **Step 4: Parallel Extraction (The Snipe):** The `ThreadPoolExecutor` shines here—spawning up to 5 concurrent instances of the `ExtractorAgent`. Each agent dives into a chunk of the targeted document, sweeping pixels and text lines simultaneously based on the `PlannerAgent`'s rules, scoring their confidence for the extracted variables.
- **Step 5: Synthesis & Gatekeeping:** 
  - The `SynthesizerAgent` takes all disparate shards of data and weaves a final, coherent report.
  - Instantly, the `ReviewerAgent` judges the report. If the Synthesizer hallucinates numbers or ignores a core query detail, the report is trashed. The Reviewer appends critical corrections and commands a total revision.
- **Step 6: Submit Data:** Secure, structured dispatch of the QA answers.

---

## 🤖 Anatomy of the AI Agents

Every agent acts as a subclass of the indomitable `BaseAgent`. This core base handles critical fallback loops (`llm_retry` handling connection timeouts) and rigorously enforces standard `pydantic` JSON schemas upon outputs.

1. **`TaskRouterAgent`**: The Traffic Controller. Determines exclusively if an incoming task is a QA challenge or an Organizational taxonomy problem.
2. **`KeywordExtractorAgent`**: The Speed-Reader. It natively digests Vision arrays `image_base64` and Markdown tables to swiftly deduce document typologies and crucial subjects.
3. **`FileLocatorAgent`**: The multimodal Scout. Visually surveys document bundles to reject trash files and spotlight critical sources.
4. **`FileOrganizerAgent`**: The Logistics expert. Matches file realities with taxonomy expectations.
5. **`PlannerAgent`**: The Tactician. Reformats plain text prompts into explicit, hard-coding search paradigms.
6. **`ExtractorAgent`**: The diligent Sniper. It operates strictly on chunks matching them visually and textually against the Planner's targets, returning precise data and `confidence_score` arrays.
7. **`SynthesizerAgent`**: The Master of Ceremonies. Collects the Sniper shards, curating the final response presentation.
8. **`ReviewerAgent`**: The strict Judge (`temperature: 0.1`). Operates autonomously to catch hallucinations. Reads Prompts + Draft Answers + Thought Logs independently to flag and force corrections upon weak responses.

---

## ⚙️ Configuration & Customization Hacks

Because logic is decoupled from architecture, modifying the systems requires merely adjusting strings rather than refactoring functions:
- **Agent Personality Adjustments**: Located in `core/prompts/`. Manipulate these base strings to dictate exactly how an agent behaves.
- **Data Shape Injection**: Want your Extractor to flag a requirement like `contract_id`? Simply add the typed variable into the specific schema in `core/schemas/agent_outputs.py`. The LLM automatically obeys.
- **Model Agnostic Switch**: Flip the `settings.py` or `.env` configuration to oscillate between leading models (GPT, Gemini Pro) without crashing internal systems.

---

## 🧪 Installation & Running Automated Tests

We constructed an iron-clad integration test suite that tests local image Vision capabilities, Excel handlers, and E2E offline interactions without costing API credits.

### 1. Environment Config
```bash
# Recommended: Use 'uv' for efficient environment management
uv sync

# Duplicate the .env
cp .env.example .env
# Populate your local dataset paths and OpenAI model key.
```

### 2. The Built-in Test Suite
All test configurations are located securely in `tests/`. Breakdown of test files:
- **`test_agents.py`**: Ensures the discrete logic components of individual agents (e.g. Router, Locator) act rationally.
- **`test_data_pipeline.py`**: A local dataset suite that checks parsing, resource filename mapping, local copying, and JSONL submission persistence.
- **`test_image_excel_handling.py`**: Formats handler validation. Explicitly confirms that the Vision API can decode Image/Scans, and Tables accurately unpack Excel `.xlsx` spreadsheets. 
- **`test_workflows_offline.py`**: Integration testing at its best. Mimics the complete E2E interaction where the `ReviewerAgent` and `CacheManager` act synchronously without risking real external API Tokens.
- **`test_flow_qa.py` & `test_flow_organization.py`**: Specialized mock-logic checking the primary thought processes of both major workflows.

### 3. Executing the Tests

**Method A: Complete System Validation (Recommended)**
```bash
# Safely run all offline architecture tests, Vision checks, and Table extraction
uv run pytest tests/ -v -s
```

**Method B: Isolate a Single Module**
```bash
# Example: Just validating if the system reads Excel files properly
uv run pytest tests/test_image_excel_handling.py -v -s
```

### 4. Deploy The Engine
Run the workflow against the local dump and local resource files:
```bash
uv run python main.py
```
*(By default, this is loaded as an independent task via `pipeline.process_single_task()`. Un-comment `pipeline.run_continuous()` inside `main.py` if you seek endless processing capability).*
