# main.py
from dotenv import load_dotenv

from core.config.settings import settings
from core.pipeline import SystemPipeline
from core.utils.logger import agent_logger
from dataProvider import ProviderService


def main():
    load_dotenv()

    agent_logger.info("OCR Multi-Agents system started in local dataset mode.")

    try:
        provider = ProviderService(
            dump_path=settings.DATA_DUMP_PATH,
            data_dir=settings.DATA_DIR,
            submissions_path=settings.LOCAL_SUBMISSIONS_PATH,
            skip_missing_tasks=settings.LOCAL_SKIP_MISSING_TASKS,
        )
        provider.create_session()

        pipeline = SystemPipeline(provider)
        pipeline.process_single_task()
        # pipeline.run_continuous()

    except Exception as e:
        agent_logger.critical(f"System stopped because of a top-level error: {e}")


if __name__ == "__main__":
    main()
