from typing import Any

from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    title: str = ""
    input_variables: dict[str, Any] = Field(default_factory=dict)
    file_assets: list[dict[str, Any]] = Field(default_factory=list)


class ContinueInterruptRequest(BaseModel):
    interrupt_type: str
    interrupt_command: dict[str, Any] = Field(default_factory=dict)
