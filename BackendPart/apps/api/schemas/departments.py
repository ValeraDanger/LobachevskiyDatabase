from pydantic import BaseModel


class DepartmentResponse(BaseModel):
    id: int
    code: str
    name: str
