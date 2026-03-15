from typing import Any

from pydantic import BaseModel


class PromptResponse(BaseModel):
    name: str
    version: str
    description: str
    system_prompt: str
    user_prompt: str
    output_schema: dict[str, Any] | None = None


class PromptUpdateRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    version: str | None = None
    description: str | None = None
