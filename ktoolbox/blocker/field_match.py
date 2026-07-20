from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from ktoolbox.api.generated import Post
from ktoolbox.blocker.model import (
    BlockDecision,
    BlockerContext,
    BlockerSpec,
    ConditionGroup,
    ConditionNode,
    FieldCondition,
)

_MISSING = object()


class FieldMatchOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: ConditionGroup

    @field_validator("rule")
    @classmethod
    def compile_regular_expressions(cls, rule: ConditionGroup) -> ConditionGroup:
        for condition in _field_conditions(rule):
            if condition.operator == "regex":
                flags = 0 if condition.case_sensitive else re.IGNORECASE
                for pattern in condition.values:
                    try:
                        re.compile(pattern, flags)
                    except re.error as error:
                        raise ValueError(f"invalid regular expression {pattern!r}: {error}") from error
        return rule


class FieldMatchBlocker:
    def __init__(self, spec: BlockerSpec, options: FieldMatchOptions) -> None:
        self.id = spec.id
        self.scope = spec.scope
        self.options = options

    async def evaluate(self, post: Post, context: BlockerContext) -> BlockDecision | None:
        if not self.scope.includes(context.service, context.creator_id):
            return None
        if _evaluate_node(self.options.rule, post.model_dump(mode="python")):
            return BlockDecision(blocker_id=self.id, reason=f"matched field rule in {self.id}")
        return None


def _field_conditions(group: ConditionGroup) -> list[FieldCondition]:
    result: list[FieldCondition] = []
    for condition in group.conditions:
        if isinstance(condition, FieldCondition):
            result.append(condition)
        else:
            result.extend(_field_conditions(condition))
    return result


def _evaluate_node(node: ConditionNode, data: Mapping[str, Any]) -> bool:
    if isinstance(node, FieldCondition):
        result = _evaluate_condition(node, data)
    else:
        values = (_evaluate_node(child, data) for child in node.conditions)
        result = any(values) if node.mode == "any" else all(values)
    return not result if node.negate else result


def _evaluate_condition(condition: FieldCondition, data: Mapping[str, Any]) -> bool:
    selected = _select_values(data, condition.field)
    if condition.operator == "exists":
        result = any(value is not _MISSING and value is not None for value in selected)
        return result is condition.expected

    values = [value for selected_value in selected for value in _flatten(selected_value)]
    if condition.operator == "contains":
        result = any(
            _contains(value, expected, condition.case_sensitive) for value in values for expected in condition.values
        )
    elif condition.operator == "equals":
        result = any(
            _equals(value, expected, condition.case_sensitive) for value in values for expected in condition.values
        )
    else:
        flags = 0 if condition.case_sensitive else re.IGNORECASE
        result = any(
            re.search(pattern, str(value), flags) is not None for value in values for pattern in condition.values
        )
    return result


def _select_values(data: Mapping[str, Any], path: str) -> list[Any]:
    current: list[Any] = [data]
    for raw_component in path.split("."):
        wildcard = raw_component.endswith("[*]")
        component = raw_component.removesuffix("[*]")
        selected: list[Any] = []
        for value in current:
            if isinstance(value, BaseModel):
                value = value.model_dump(mode="python")
            child = value.get(component, _MISSING) if isinstance(value, Mapping) else _MISSING
            if wildcard and isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                selected.extend(child)
            else:
                selected.append(child)
        current = selected
    return current


def _flatten(value: Any) -> list[Any]:
    if value is _MISSING or value is None:
        return []
    if isinstance(value, Mapping):
        return [item for child in value.values() for item in _flatten(child)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for child in value for item in _flatten(child)]
    return [value]


def _contains(value: Any, expected: str, case_sensitive: bool) -> bool:
    actual = str(value)
    return expected in actual if case_sensitive else expected.casefold() in actual.casefold()


def _equals(value: Any, expected: str, case_sensitive: bool) -> bool:
    actual = str(value)
    return actual == expected if case_sensitive else actual.casefold() == expected.casefold()
