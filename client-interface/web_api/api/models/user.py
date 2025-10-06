from pydantic import BaseModel


class UserIdSaveRequest(BaseModel):
    name: str
    email: str
