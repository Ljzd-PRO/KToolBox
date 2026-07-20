from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic import BaseModel

from ktoolbox.api.generated import FileReference, Post
from ktoolbox.blocker import (
    BlockDecision,
    BlockerContext,
    BlockerEngine,
    BlockerRegistry,
    BlockerScope,
    BlockerSpec,
)
from ktoolbox.blocker.engine import _build_field_match, legacy_keyword_blocker
from ktoolbox.blocker.field_match import FieldMatchOptions, _flatten, _select_values
from ktoolbox.project_config import ProjectConfigError, ProjectConfigStore


def post() -> Post:
    return Post(
        id="post-1",
        user="creator-1",
        service="fanbox",
        title="Weekly progress update",
        content="Sketch practice and daily notes",
        tags=["WIP", "drawing"],
        attachments=[FileReference(name="preview.PNG", path="/data/preview.png")],
    )


def spec(rule: dict, *, scope: BlockerScope | None = None) -> BlockerSpec:
    return BlockerSpec(id="rule", scope=scope or BlockerScope(), options={"rule": rule})


def field(field: str, operator: str, values: list[str] | None = None, **options: object) -> dict:
    return {
        "kind": "field",
        "field": field,
        "operator": operator,
        "values": values or [],
        **options,
    }


def group(*conditions: dict, mode: str = "any", negate: bool = False) -> dict:
    return {"kind": "group", "mode": mode, "conditions": list(conditions), "negate": negate}


@pytest.mark.parametrize(
    "condition",
    [
        field("title", "contains", ["PROGRESS"]),
        field("content", "equals", ["sketch practice and daily notes"]),
        field("tags[*]", "regex", [r"^w.p$"]),
        field("attachments[*].name", "contains", ["preview"]),
        field("file.name", "exists", expected=False),
    ],
)
async def test_field_match_operators_cover_list_post_fields(condition: dict) -> None:
    engine = BlockerEngine.from_specs([spec(group(condition))])
    decision = await engine.evaluate(post(), BlockerContext("fanbox", "creator-1"))
    assert decision == BlockDecision("rule", "matched field rule in rule")


async def test_nested_groups_negation_and_case_sensitivity() -> None:
    rule = group(
        group(
            field("title", "contains", ["progress"]),
            field("tags[*]", "equals", ["WIP"], case_sensitive=True),
            mode="all",
        ),
        field("content", "contains", ["finished"], negate=True),
        mode="all",
    )
    engine = BlockerEngine.from_specs([spec(rule)])
    assert await engine.evaluate(post(), BlockerContext("fanbox", "creator-1")) is not None


async def test_creator_scope_and_disabled_specs() -> None:
    creator_scope = BlockerScope(mode="creators", creators=["fanbox:creator-1"])
    scoped = spec(group(field("title", "contains", ["progress"])), scope=creator_scope)
    disabled = scoped.model_copy(update={"id": "disabled", "enabled": False})
    engine = BlockerEngine.from_specs([disabled, scoped])
    assert await engine.evaluate(post(), BlockerContext("fanbox", "other")) is None
    assert await engine.evaluate(post(), BlockerContext("fanbox", "creator-1")) is not None


async def test_field_match_returns_none_when_in_scope_rule_does_not_match() -> None:
    engine = BlockerEngine.from_specs([spec(group(field("title", "equals", ["finished work"])))])
    assert await engine.evaluate(post(), BlockerContext("fanbox", "creator-1")) is None


def test_rule_validation_rejects_unsafe_paths_and_invalid_regex() -> None:
    with pytest.raises(ValueError, match="field paths"):
        BlockerEngine.from_specs([spec(group(field("__class__[0]", "exists")))])
    with pytest.raises(ValueError, match="invalid regular expression"):
        BlockerEngine.from_specs([spec(group(field("title", "regex", ["["])))])
    with pytest.raises(ValueError, match="cannot be empty"):
        BlockerEngine.from_specs([spec(group())])


def test_scope_and_registry_validation() -> None:
    with pytest.raises(ValueError, match="requires at least one creator"):
        BlockerScope(mode="creators")
    with pytest.raises(ValueError, match="cannot list creators"):
        BlockerScope(mode="global", creators=["fanbox:1"])
    with pytest.raises(ValueError, match="service:creator_id"):
        BlockerScope(mode="creators", creators=["invalid"])
    with pytest.raises(ValueError, match="unknown blocker type"):
        BlockerRegistry().validate(BlockerSpec(id="custom", type="custom"))

    scope = BlockerScope(mode="creators", creators=["fanbox:1", "FANBOX:1"])
    assert scope.creators == ["fanbox:1"]
    context = BlockerContext("fanbox", "1")
    assert context.creator_key == "fanbox:1"


def test_condition_value_validation_and_nested_value_helpers() -> None:
    with pytest.raises(ValueError, match="do not accept values"):
        BlockerEngine.from_specs([spec(group(field("title", "exists", ["unexpected"])))])
    with pytest.raises(ValueError, match="require at least one value"):
        BlockerEngine.from_specs([spec(group(field("title", "contains")))])

    class Nested(BaseModel):
        name: str

    assert _select_values({"nested": Nested(name="value")}, "nested.name") == ["value"]
    assert _flatten(_select_values({}, "missing")[0]) == []
    assert _flatten(None) == []
    assert _flatten({"items": ["one", None]}) == ["one"]
    assert _flatten(["one", ["two"]]) == ["one", "two"]


def test_field_match_builder_rejects_the_wrong_options_model() -> None:
    class OtherOptions(BaseModel):
        pass

    configured = spec(group(field("title", "contains", ["progress"])))
    with pytest.raises(TypeError, match="requires FieldMatchOptions"):
        _build_field_match(configured, OtherOptions())
    assert _build_field_match(configured, FieldMatchOptions.model_validate(configured.options)).id == "rule"


async def test_engine_short_circuits_after_first_decision() -> None:
    calls: list[str] = []

    @dataclass
    class StubBlocker:
        id: str
        blocked: bool

        async def evaluate(self, target: Post, context: BlockerContext) -> BlockDecision | None:
            calls.append(self.id)
            return BlockDecision(self.id, "blocked") if self.blocked else None

    engine = BlockerEngine([StubBlocker("first", True), StubBlocker("second", True)])
    assert await engine.evaluate(post(), BlockerContext("fanbox", "creator-1")) == BlockDecision("first", "blocked")
    assert calls == ["first"]


def test_registry_supports_future_blocker_types() -> None:
    class Options(BaseModel):
        answer: int

    @dataclass
    class CustomBlocker:
        id: str

        async def evaluate(self, target: Post, context: BlockerContext) -> BlockDecision | None:
            return None

    registry = BlockerRegistry()
    registry.register("custom", Options, lambda configured, options: CustomBlocker(configured.id))
    blocker = registry.build(BlockerSpec(id="future", type="custom", options={"answer": 42}))
    assert blocker.id == "future"
    with pytest.raises(ValueError, match="already registered"):
        registry.register("custom", Options, lambda configured, options: CustomBlocker(configured.id))


def test_legacy_keyword_blocker_is_global_and_normalized() -> None:
    assert legacy_keyword_blocker([]) is None
    blocker = legacy_keyword_blocker([" daily ", "daily", "WIP"])
    assert blocker is not None
    assert blocker.id == "legacy-keywords-exclude"
    assert blocker.scope.mode == "global"
    assert blocker.options["rule"]["conditions"][0]["values"] == ["WIP", "daily"]


def test_project_store_round_trips_and_validates_blockers(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    path.write_text(
        """
schema_version = 1

[[blockers]]
id = "daily-life"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:creator-1"] }
options = { rule = { kind = "group", mode = "any", conditions = [
  { kind = "field", field = "title", operator = "contains", values = ["daily"] }
] } }
""".strip(),
        encoding="utf-8",
    )
    store = ProjectConfigStore(path)
    configuration = store.load()
    assert configuration.blockers[0].id == "daily-life"
    store.save(configuration)
    assert ProjectConfigStore(path).load() == configuration

    path.write_text(
        'schema_version = 1\n[[blockers]]\nid = "bad"\ntype = "missing"\n',
        encoding="utf-8",
    )
    with pytest.raises(ProjectConfigError, match="unknown blocker type"):
        ProjectConfigStore(path).load()
