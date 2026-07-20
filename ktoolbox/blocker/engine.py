from __future__ import annotations

from collections.abc import Callable, Iterable

from pydantic import BaseModel, ValidationError

from ktoolbox.api.generated import Post
from ktoolbox.blocker.field_match import FieldMatchBlocker, FieldMatchOptions
from ktoolbox.blocker.model import BlockDecision, BlockerContext, BlockerSpec, PostBlocker

BlockerBuilder = Callable[[BlockerSpec, BaseModel], PostBlocker]


class BlockerRegistry:
    """Validate and build blocker implementations by their configured type."""

    def __init__(self) -> None:
        self._types: dict[str, tuple[type[BaseModel], BlockerBuilder]] = {}

    def register(self, blocker_type: str, options_model: type[BaseModel], builder: BlockerBuilder) -> None:
        if blocker_type in self._types:
            raise ValueError(f"blocker type already registered: {blocker_type}")
        self._types[blocker_type] = (options_model, builder)

    def validate(self, spec: BlockerSpec) -> BaseModel:
        try:
            options_model, _ = self._types[spec.type]
        except KeyError as error:
            raise ValueError(f"unknown blocker type: {spec.type}") from error
        try:
            return options_model.model_validate(spec.options)
        except ValidationError as error:
            raise ValueError(f"invalid options for blocker {spec.id}: {error}") from error

    def build(self, spec: BlockerSpec) -> PostBlocker:
        options = self.validate(spec)
        _, builder = self._types[spec.type]
        return builder(spec, options)


class BlockerEngine:
    def __init__(self, blockers: Iterable[PostBlocker] = ()) -> None:
        self.blockers = tuple(blockers)

    @classmethod
    def from_specs(
        cls,
        specs: Iterable[BlockerSpec],
        *,
        registry: BlockerRegistry | None = None,
    ) -> BlockerEngine:
        selected_registry = blocker_registry if registry is None else registry
        return cls(selected_registry.build(spec) for spec in specs if spec.enabled)

    async def evaluate(self, post: Post, context: BlockerContext) -> BlockDecision | None:
        for blocker in self.blockers:
            if decision := await blocker.evaluate(post, context):
                return decision
        return None


def _build_field_match(spec: BlockerSpec, options: BaseModel) -> PostBlocker:
    if not isinstance(options, FieldMatchOptions):
        raise TypeError("field-match blocker requires FieldMatchOptions")
    return FieldMatchBlocker(spec, options)


blocker_registry = BlockerRegistry()
blocker_registry.register("field-match", FieldMatchOptions, _build_field_match)


def legacy_keyword_blocker(keywords: Iterable[str]) -> BlockerSpec | None:
    values = sorted({keyword.strip() for keyword in keywords if keyword.strip()})
    if not values:
        return None
    return BlockerSpec(
        id="legacy-keywords-exclude",
        options={
            "rule": {
                "kind": "group",
                "mode": "any",
                "conditions": [
                    {
                        "kind": "field",
                        "field": "title",
                        "operator": "contains",
                        "values": values,
                    }
                ],
            }
        },
    )
