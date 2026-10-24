from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    route: str
    message: str
