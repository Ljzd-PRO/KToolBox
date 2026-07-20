from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ktoolbox.api.generated import Post


class BlockerScope(BaseModel):
    """Select whether a blocker applies globally or to named creators."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["global", "creators"] = "global"
    creators: list[str] = Field(default_factory=list)

    @field_validator("creators")
    @classmethod
    def validate_creator_keys(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            service, separator, creator_id = value.strip().partition(":")
            if not separator or not service or not creator_id:
                raise ValueError("blocker creator scope entries must use service:creator_id")
            key = f"{service}:{creator_id}"
            if key.casefold() not in seen:
                normalized.append(key)
                seen.add(key.casefold())
        return normalized

    @model_validator(mode="after")
    def validate_mode(self) -> BlockerScope:
        if self.mode == "global" and self.creators:
            raise ValueError("global blocker scope cannot list creators")
        if self.mode == "creators" and not self.creators:
            raise ValueError("creator blocker scope requires at least one creator")
        return self

    def includes(self, service: str, creator_id: str) -> bool:
        if self.mode == "global":
            return True
        key = f"{service}:{creator_id}".casefold()
        return any(item.casefold() == key for item in self.creators)


class BlockerSpec(BaseModel):
    """Serializable definition used by the blocker registry."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
    type: Annotated[str, Field(min_length=1)] = "field-match"
    enabled: bool = True
    scope: BlockerScope = Field(default_factory=BlockerScope)
    options: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BlockerContext:
    service: str
    creator_id: str

    @property
    def creator_key(self) -> str:
        return f"{self.service}:{self.creator_id}"


@dataclass(frozen=True, slots=True)
class BlockDecision:
    blocker_id: str
    reason: str


class PostBlocker(Protocol):
    id: str

    async def evaluate(self, post: Post, context: BlockerContext) -> BlockDecision | None: ...


class FieldCondition(BaseModel):
    """One safe field comparison in a field-match rule tree."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    kind: Literal["field"] = "field"
    field: Annotated[str, Field(min_length=1)]
    operator: Literal["contains", "equals", "regex", "exists"]
    values: list[str] = Field(default_factory=list)
    expected: bool = True
    case_sensitive: bool = False
    negate: bool = False

    @field_validator("field")
    @classmethod
    def validate_field_path(cls, value: str) -> str:
        for component in value.split("."):
            name = component.removesuffix("[*]")
            if not name.isidentifier() or ("[" in component and not component.endswith("[*]")):
                raise ValueError("field paths use dotted names with optional [*] list selectors")
        return value

    @model_validator(mode="after")
    def validate_operator_values(self) -> FieldCondition:
        if self.operator == "exists" and self.values:
            raise ValueError("exists conditions do not accept values")
        if self.operator != "exists" and not self.values:
            raise ValueError(f"{self.operator} conditions require at least one value")
        return self


class ConditionGroup(BaseModel):
    """A recursive any/all group of field conditions."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["group"] = "group"
    mode: Literal["any", "all"] = "any"
    conditions: list[ConditionNode]
    negate: bool = False

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, values: list[ConditionNode]) -> list[ConditionNode]:
        if not values:
            raise ValueError("condition groups cannot be empty")
        return values


ConditionNode = Annotated[FieldCondition | ConditionGroup, Field(discriminator="kind")]
ConditionGroup.model_rebuild()
