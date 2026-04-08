# dataProvider/utils/http_client.py
import requests

class HTTPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["x-api-key"] = api_key

    def set_bearer_token(self, token):
        self.headers["Authorization"] = f"Bearer {token}"

    def post(self, endpoint, data=None):
        response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get(self, endpoint, params=None, stream=False):
        response = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self.headers, stream=stream)
        response.raise_for_status()
        return response