"""Prompt template management endpoints — view and edit YAML prompt files."""

from typing import Any

import yaml
from fastapi import APIRouter, status
from jinja2 import TemplateSyntaxError

from backend.app.agent.prompt_loader import PROMPTS_DIR, _jinja_env
from backend.app.api.exceptions import OathKeeperError
from backend.app.api.schemas.prompts import PromptResponse, PromptUpdateRequest

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

ALLOWED_NAMES = frozenset(
    {
        "system",
        "deal_structuring",
        "scoring",
        "resource_estimation",
        "risk_analysis",
        "similar_project",
        "final_verdict",
    },
)


def _validate_name(name: str) -> None:
    if name not in ALLOWED_NAMES:
        raise OathKeeperError(f"Prompt '{name}' not found", status_code=404)


def _load_yaml(name: str) -> dict[str, Any]:
    path = PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise OathKeeperError(f"Prompt file '{name}' not found", status_code=404)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _to_response(name: str, data: dict[str, Any]) -> PromptResponse:
    return PromptResponse(
        name=name,
        version=data.get("version", "1.0"),
        description=data.get("description", ""),
        system_prompt=data.get("system_prompt", ""),
        user_prompt=data.get("user_prompt", ""),
        output_schema=data.get("output_schema"),
    )


def _literal_str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def _get_yaml_dumper() -> type[yaml.Dumper]:
    dumper = yaml.Dumper
    dumper.add_representer(str, _literal_str_representer)
    return dumper


@router.get("", response_model=list[PromptResponse])
async def list_prompts() -> list[PromptResponse]:
    results = []
    for name in sorted(ALLOWED_NAMES):
        try:
            data = _load_yaml(name)
            results.append(_to_response(name, data))
        except OathKeeperError:
            continue
    return results


@router.get("/{name}", response_model=PromptResponse)
async def get_prompt(name: str) -> PromptResponse:
    _validate_name(name)
    data = _load_yaml(name)
    return _to_response(name, data)


@router.put("/{name}", response_model=PromptResponse)
async def update_prompt(name: str, body: PromptUpdateRequest) -> PromptResponse:
    _validate_name(name)
    data = _load_yaml(name)

    # Validate Jinja2 syntax
    for field, value in [("system_prompt", body.system_prompt), ("user_prompt", body.user_prompt)]:
        try:
            _jinja_env.parse(value)
        except TemplateSyntaxError as e:
            raise OathKeeperError(
                f"Jinja2 syntax error in {field}: {e.message}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from e

    data["system_prompt"] = body.system_prompt
    data["user_prompt"] = body.user_prompt

    if body.version is not None:
        data["version"] = body.version
    if body.description is not None:
        data["description"] = body.description

    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            Dumper=_get_yaml_dumper(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return _to_response(name, data)
