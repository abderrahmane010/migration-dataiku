"""Substitution of Dataiku variables (``${name}``) in object fields."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# ASSUMPTION (H-18): DSS variable syntax is ``${name}`` with name made of
# letters, digits, ``_`` and ``.``. To be confirmed on real exports.
VARIABLE_PATTERN = re.compile(r"\$\{([A-Za-z0-9_.]+)\}")


def find_variables(text: str) -> list[str]:
    """Variable names referenced in ``text``, in order of first appearance."""
    return list(dict.fromkeys(VARIABLE_PATTERN.findall(text)))


def _as_text(value: Any) -> str | None:
    if isinstance(value, bool):
        # ASSUMPTION (H-19): booleans render in lower case, as in JSON.
        return "true" if value else "false"
    if isinstance(value, str | int | float):
        return str(value)
    return None  # objects and lists are never substituted: reported as unresolved


def resolve(text: str, variables: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Substitute known scalar variables.

    Returns the resolved text and the names that remain unresolved. Unresolved
    references are left untouched (``${name}``) in the output.
    """
    unresolved: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in variables:
            text_value = _as_text(variables[name])
            if text_value is not None:
                return text_value
        if name not in unresolved:
            unresolved.append(name)
        return match.group(0)

    return VARIABLE_PATTERN.sub(substitute, text), unresolved


def effective_variables(
    project_key: str,
    variables_json: Mapping[str, Any] | None,
    instance_variables: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge the variable sources, lowest to highest priority.

    instance variables (given by the caller) < project ``standard`` < project
    ``local`` < built-ins (``projectKey``).
    """
    merged: dict[str, Any] = dict(instance_variables or {})
    if variables_json:
        # ASSUMPTION (H-13, H-24): project variables are {"standard": {...}, "local": {...}},
        # and local overrides standard.
        merged.update(variables_json.get("standard") or {})
        merged.update(variables_json.get("local") or {})
    merged["projectKey"] = project_key
    return merged
