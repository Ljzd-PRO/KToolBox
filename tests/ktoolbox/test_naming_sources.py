from __future__ import annotations

from pathlib import Path

import pytest

from ktoolbox.naming_sources import (
    MAX_NAMING_SOURCE_BYTES,
    NamingSourceParseError,
    parse_naming_source,
)
from ktoolbox.project_config import ProjectNamingConfiguration


def test_parse_env_supports_comments_quotes_booleans_and_json_arrays() -> None:
    parsed = parse_naming_source(
        "env",
        """
# Legacy naming only
KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{id} - {title}"
KTOOLBOX_JOB__MIX_POSTS=yes
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='["cover.jpg", "thumb.png"]'
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=files
UNRELATED_PASSWORD=do-not-return
""",
        target=ProjectNamingConfiguration(),
    )

    assert parsed.naming.post_dirname_format == "{id} - {title}"
    assert parsed.naming.mix_posts is True
    assert parsed.naming.sequential_filename_excludes == {"cover.jpg", "thumb.png"}
    assert parsed.naming.post_structure.attachments == Path("files")
    assert parsed.recognized_fields == (
        "mix_posts",
        "post_dirname_format",
        "post_structure.attachments",
        "sequential_filename_excludes",
    )
    assert parsed.warnings[0].code == "ignored_unknown_entries"
    assert parsed.warnings[0].count == 1
    assert "UNRELATED_PASSWORD" not in repr(parsed)
    assert "do-not-return" not in repr(parsed)


def test_parse_env_uses_legacy_defaults_instead_of_target_values() -> None:
    target = ProjectNamingConfiguration(
        post_dirname_format="{post_id}",
        mix_posts=True,
    )

    parsed = parse_naming_source(
        "env",
        "KTOOLBOX_JOB__FILENAME_FORMAT={id}_{}\n",
        target=target,
    )

    assert parsed.naming.post_dirname_format == "{title}"
    assert parsed.naming.mix_posts is False
    assert parsed.naming.filename_format == "{id}_{}"
    assert "post_dirname_format" in parsed.defaulted_fields


@pytest.mark.parametrize(
    "content",
    [
        """
schema_version = 5
[naming]
creator_dirname_format = "{creator_name} ({creator_id})"
post_dirname_format = "{post_id}"
[naming.post_structure]
attachments = "files"
""",
        """
[naming]
creator_dirname_format = "{creator_name} ({creator_id})"
post_dirname_format = "{post_id}"
[naming.post_structure]
attachments = "files"
""",
        """
creator_dirname_format = "{creator_name} ({creator_id})"
post_dirname_format = "{post_id}"
[post_structure]
attachments = "files"
""",
    ],
)
def test_parse_toml_supports_full_section_and_bare_fragments(content: str) -> None:
    parsed = parse_naming_source(
        "toml",
        content,
        target=ProjectNamingConfiguration(),
    )

    assert parsed.naming.creator_dirname_format == "{creator_name} ({creator_id})"
    assert parsed.naming.post_dirname_format == "{post_id}"
    assert parsed.naming.post_structure.attachments == Path("files")


def test_parse_toml_reports_unknown_and_invalid_fields_without_input_values() -> None:
    with pytest.raises(NamingSourceParseError) as captured:
        parse_naming_source(
            "toml",
            """
[naming]
post_dirname_format = "{unsupported_secret}"
unknown_password = "very-secret"
""",
            target=ProjectNamingConfiguration(),
        )

    issues = captured.value.issues
    assert {issue.path for issue in issues} == {
        "post_dirname_format",
        "unknown_password",
    }
    assert "very-secret" not in repr(issues)


@pytest.mark.parametrize(
    ("content", "code"),
    [
        ("NOT A DOTENV LINE\n", "dotenv_syntax"),
        ("UNRELATED=value\n", "no_legacy_naming_fields"),
        ("KTOOLBOX_JOB__MIX_POSTS=maybe\n", "invalid_value"),
    ],
)
def test_parse_env_reports_safe_errors(content: str, code: str) -> None:
    with pytest.raises(NamingSourceParseError) as captured:
        parse_naming_source(
            "env",
            content,
            target=ProjectNamingConfiguration(),
        )

    assert code in {issue.code for issue in captured.value.issues}
    assert content.strip() not in str(captured.value)


def test_parse_source_rejects_empty_nul_and_oversize_input() -> None:
    for content, code in (
        ("", "source_empty"),
        ("KTOOLBOX_JOB__MIX_POSTS=true\0", "invalid_character"),
        ("x" * (MAX_NAMING_SOURCE_BYTES + 1), "source_too_large"),
    ):
        with pytest.raises(NamingSourceParseError) as captured:
            parse_naming_source(
                "env",
                content,
                target=ProjectNamingConfiguration(),
            )
        assert captured.value.issues[0].code == code


def test_parse_digest_is_deterministic_and_reflects_normalized_source() -> None:
    first = parse_naming_source(
        "env",
        "KTOOLBOX_JOB__MIX_POSTS=true\n",
        target=ProjectNamingConfiguration(),
    )
    second = parse_naming_source(
        "toml",
        "[naming]\nmix_posts = true\n",
        target=ProjectNamingConfiguration(),
    )

    assert first.digest == second.digest
    assert first.naming == second.naming
