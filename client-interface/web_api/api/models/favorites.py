from pydantic import BaseModel


class FavoriteRequest(BaseModel):
    uri: str
