# dataProvider/services/provider_service.py
from ..utils.http_client import HTTPClient
from ..models.session import Session
from ..models.task import Task, Resource

class ProviderService:
    def __init__(self, base_url, api_key):
        self.client = HTTPClient(base_url, api_key)
        self.session = None

    def create_session(self) -> Session:
        data = self.client.post("/sessions")
        self.session = Session(
            session_id=data['session_id'],
            access_token=data['access_token'],
            expires_in=data['expires_in']
        )
        # Cập nhật token cho các request sau
        self.client.set_bearer_token(self.session.access_token)
        return self.session

    def get_next_task(self) -> Task:
        data = self.client.get("/tasks/next").json()
        resources = [Resource(**res) for res in data.get('resources', [])]
        return Task(task_id=data['task_id'], prompt_template=data['prompt_template'], resources=resources)

    def download_file(self, download_token, save_path):
        """Tải file dạng stream để tiết kiệm RAM"""
        params = {"token": download_token}
        response = self.client.get("/download", params=params, stream=True)
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

    def submit_task(self, task_id, answers, thought_log, used_tools=[]):
        payload = {
            "session_id": self.session.session_id,
            "task_id": task_id,
            "answers": answers,
            "thought_log": thought_log,
            "used_tools": used_tools
        }
        return self.client.post("/submissions", data=payload)