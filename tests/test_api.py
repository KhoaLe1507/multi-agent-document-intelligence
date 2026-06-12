from dotenv import load_dotenv

from core.config.settings import settings
from dataProvider import ProviderService


def main():
    load_dotenv()

    provider = ProviderService(
        dump_path=settings.DATA_DUMP_PATH,
        data_dir=settings.DATA_DIR,
        submissions_path=settings.LOCAL_SUBMISSIONS_PATH,
        skip_missing_tasks=settings.LOCAL_SKIP_MISSING_TASKS,
    )
    session = provider.create_session()
    task = provider.get_next_task()

    print("Local provider OK")
    print(f"Session ID: {session.session_id}")
    print(f"Task ID: {task.task_id}")
    print(f"Prompt: {task.prompt_template[:120]}")
    print(f"Resources: {len(task.resources)}")

    if task.resources:
        res = task.resources[0]
        local_name = provider.to_local_resource_name(res.file_path)
        print(f"First resource local filename: {local_name}")


if __name__ == "__main__":
    main()
