from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from core.config.settings import settings

from .agent_evaluators import AGENT_EVALUATORS
from .dataset_loader import create_or_update_phoenix_dataset, load_local_eval_samples
from .e2e_evaluators import E2E_EVALUATORS
from .phoenix_config import configure_phoenix_tracing, create_phoenix_client
from .run_agent_task import run_agent_task


EXPERIMENT_NAME = "Overall Multi-Agent Evaluation"
EXPERIMENT_DESCRIPTION = (
    "Evaluate Multi-Agent AI system using binary LLM-as-a-Judge evaluators without ground truth."
)


def main() -> None:
    args = _parse_args()
    configure_phoenix_tracing(
        project_name=args.project_name,
        endpoint=args.phoenix_collector_endpoint,
    )

    samples = load_local_eval_samples(
        dump_path=args.dump,
        data_dir=args.data_dir,
        limit=args.limit,
    )
    client = create_phoenix_client(args.phoenix_base_url)
    dataset = create_or_update_phoenix_dataset(
        client,
        samples,
        dataset_name=args.dataset_name,
        dataset_description="Local OCR multi-agent tasks without ground truth.",
    )

    evaluators = _phoenix_evaluators(AGENT_EVALUATORS + E2E_EVALUATORS)
    experiment_name = args.experiment_name or (
        f"{EXPERIMENT_NAME} - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    experiment = client.experiments.run_experiment(
        dataset=dataset,
        task=run_agent_task,
        evaluators=evaluators,
        experiment_name=experiment_name,
        experiment_description=EXPERIMENT_DESCRIPTION,
        experiment_metadata={
            "ground_truth": False,
            "score_type": "binary",
            "judge_tracing": "disabled",
            "source": "evaluation.run_experiment",
        },
        dry_run=args.dry_run,
        print_summary=True,
        timeout=args.timeout,
    )

    base_url = args.phoenix_base_url or os.getenv("PHOENIX_BASE_URL") or "http://localhost:6006"
    print(f"Phoenix UI: {base_url}")
    print(f"Experiment: {experiment}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phoenix evaluation for OCR multi-agents.")
    parser.add_argument("--dump", default=settings.DATA_DUMP_PATH)
    parser.add_argument("--data-dir", default=settings.DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dataset-name", default="ocr-multi-agent-local-eval")
    parser.add_argument("--experiment-name", default=None)
    parser.add_argument("--phoenix-base-url", default=os.getenv("PHOENIX_BASE_URL"))
    parser.add_argument(
        "--phoenix-collector-endpoint",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT"),
    )
    parser.add_argument("--project-name", default="ocr-multi-agent-evaluation")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--dry-run",
        nargs="?",
        const=True,
        default=False,
        type=_dry_run_value,
        help="Run a Phoenix dry-run. Use --dry-run or --dry-run 3.",
    )
    return parser.parse_args()


def _dry_run_value(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    lowered = str(value).lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    return int(value)


def _phoenix_evaluators(evaluators):
    try:
        from phoenix.evals import create_evaluator
    except Exception:
        return evaluators

    wrapped = []
    for evaluator in evaluators:
        wrapped.append(
            create_evaluator(
                name=evaluator.__name__,
                kind="llm",
                direction="maximize",
            )(evaluator)
        )
    return wrapped


if __name__ == "__main__":
    main()
