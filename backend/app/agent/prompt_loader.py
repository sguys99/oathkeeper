"""YAML prompt loader with Jinja2 template rendering."""

from typing import Any

import yaml
from jinja2 import BaseLoader, Environment, Undefined

from backend.app.utils.path import CONFIG_PATH

PROMPTS_DIR = CONFIG_PATH / "prompts"

_jinja_env = Environment(
    loader=BaseLoader(),
    autoescape=False,
    keep_trailing_newline=True,
    undefined=Undefined,
)
_jinja_env.policies["json.dumps_kwargs"] = {"ensure_ascii": False}


class PromptNotFoundError(Exception):
    """Raised when a prompt YAML file does not exist."""


class PromptTemplate:
    """A loaded prompt template with metadata and renderable fields."""

    def __init__(self, data: dict[str, Any], name: str, profile: str = "full") -> None:
        self._data = data
        self.name = name
        self.version: str = data.get("version", "1.0")

        if profile != "full":
            suffix = f"_{profile}"
            self._system_prompt: str = data.get(f"system_prompt{suffix}") or data.get(
                "system_prompt",
                "",
            )
            self._user_prompt: str = data.get(f"user_prompt{suffix}") or data.get("user_prompt", "")
        else:
            self._system_prompt: str = data.get("system_prompt", "")
            self._user_prompt: str = data.get("user_prompt", "")

        self.output_schema: dict[str, Any] | None = data.get("output_schema")

    def render_system(self, **variables: Any) -> str:
        """Render the system prompt with Jinja2 variables."""
        return _render(self._system_prompt, variables)

    def render_user(self, **variables: Any) -> str:
        """Render the user prompt with Jinja2 variables."""
        return _render(self._user_prompt, variables)

    def render(self, **variables: Any) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) rendered pair."""
        return self.render_system(**variables), self.render_user(**variables)


def _render(template_str: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template string with the given variables."""
    if not template_str:
        return ""
    template = _jinja_env.from_string(template_str)
    return template.render(**variables)


def load_prompt(name: str, profile: str | None = None) -> PromptTemplate:
    """Load a prompt YAML file from ``configs/prompts/{name}.yaml``.

    Parameters
    ----------
    name:
        Stem name of the YAML file (e.g. ``"scoring"``).
    profile:
        Prompt profile to use (``"full"`` or ``"compact"``).
        When *None*, reads from ``Settings.prompt_profile``.

    Returns
    -------
    PromptTemplate
        Parsed template object with ``render_system`` / ``render_user`` helpers.

    Raises
    ------
    PromptNotFoundError
        If the file does not exist.
    """
    if profile is None:
        from backend.app.utils.settings import get_settings

        profile = get_settings().prompt_profile

    path = PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise PromptNotFoundError(f"Prompt file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    return PromptTemplate(data=data, name=name, profile=profile)


def load_system_prompt(profile: str | None = None) -> PromptTemplate:
    """Shortcut to load the shared system prompt template."""
    return load_prompt("system", profile=profile)


def render_prompt(
    name: str,
    profile: str | None = None,
    **variables: Any,
) -> tuple[str, str]:
    """Load + render in one call. Returns ``(system_prompt, user_prompt)``."""
    tpl = load_prompt(name, profile=profile)
    return tpl.render(**variables)
