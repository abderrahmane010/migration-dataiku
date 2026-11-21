"""Phase 1: substitution of Dataiku variables."""

from __future__ import annotations

from dku2dbx.reader.variables import effective_variables, find_variables, resolve


def test_resolve_known_variables() -> None:
    assert resolve("${projectKey}_orders", {"projectKey": "P"}) == ("P_orders", [])


def test_unresolved_variables_are_kept_and_listed() -> None:
    text, missing = resolve("${NODE_DC}_${projectKey}_${NODE_DC}", {"projectKey": "P"})
    assert text == "${NODE_DC}_P_${NODE_DC}"
    assert missing == ["NODE_DC"]


def test_scalar_values_only() -> None:
    variables = {"n": 3, "f": 1.5, "b": True, "obj": {"a": 1}, "lst": [1]}
    text, missing = resolve("${n}-${f}-${b}-${obj}-${lst}", variables)
    assert text == "3-1.5-true-${obj}-${lst}"
    assert missing == ["obj", "lst"]


def test_text_without_variables() -> None:
    assert resolve("plain_table", {}) == ("plain_table", [])
    assert resolve("$notavar {x}", {}) == ("$notavar {x}", [])


def test_find_variables_in_order() -> None:
    assert find_variables("${b}${a}${b}${dotted.name}") == ["b", "a", "dotted.name"]


def test_variable_priority() -> None:
    merged = effective_variables(
        "PK",
        {"standard": {"x": "std", "y": "std", "projectKey": "ignored"}, "local": {"y": "loc"}},
        instance_variables={"x": "inst", "z": "inst"},
    )
    assert merged == {"x": "std", "y": "loc", "z": "inst", "projectKey": "PK"}


def test_no_project_variables() -> None:
    assert effective_variables("PK", None) == {"projectKey": "PK"}
