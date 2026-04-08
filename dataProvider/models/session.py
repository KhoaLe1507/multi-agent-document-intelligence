# dataProvider/models/session.py
from dataclasses import dataclass

@dataclass
class Session:
    session_id: str
    access_token: str
    expires_in: int

