from pydantic import BaseModel


class FileTypesResponse(BaseModel):
    types: list[str]
