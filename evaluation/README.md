# Phoenix Evaluation

Run the local multi-agent dataset through Phoenix experiments with binary LLM-as-a-Judge evaluators.

```bash
uv run python -m evaluation.run_experiment --limit 3
```

Useful options:

```bash
uv run python -m evaluation.run_experiment --dry-run 1
uv run python -m evaluation.run_experiment --phoenix-base-url http://localhost:6006 --limit 5
```

Requirements:

- Phoenix server must be reachable through `PHOENIX_BASE_URL` or `--phoenix-base-url`.
- Phoenix trace collector can be configured with `PHOENIX_COLLECTOR_ENDPOINT`.
- `GEMINI_API_KEY` must be set for both the production agents and LLM judge calls.
- Judge calls use `evaluation.judge_client` directly and do not go through `BaseAgent`, so they are not added to the agent trace.

