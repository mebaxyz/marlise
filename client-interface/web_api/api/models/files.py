from typing import List
from pydantic import BaseModel


class UserFile(BaseModel):
    fullname: str
    basename: str
    filetype: str


class FileListResponse(BaseModel):
    ok: bool
    files: List[UserFile]
