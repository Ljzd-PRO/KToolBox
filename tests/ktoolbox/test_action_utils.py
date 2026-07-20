from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from ktoolbox.action.utils import (
    extract_content_images,
    filter_posts_by_date,
    filter_posts_by_indices,
    filter_posts_by_keywords,
    filter_posts_by_keywords_exclude,
    generate_filename,
    generate_grouped_post_path,
    generate_month_dirname,
    generate_post_path_name,
    generate_year_dirname,
    match_post_keywords,
)
from ktoolbox.api.generated import Post
from ktoolbox.configuration import config
from ktoolbox.job import CreatorIndices


def post(post_id: str, title: str | None = None, date: datetime | None = None, edited: datetime | None = None) -> Post:
    return Post(
        id=post_id,
        user="creator",
        service="fanbox",
        title=title,
        published=date,
        edited=edited,
    )


def test_path_and_filename_generation() -> None:
    dated = post("42", "A/B", datetime(2025, 3, 2))
    assert generate_post_path_name(post("42")) == "42"
    assert generate_post_path_name(dated) == "AB"
    assert generate_filename(dated, "cover.jpg", "{id}_{published}_{}") == "42_2025-03-02_cover.jpg"
    assert generate_year_dirname(dated) == "2025"
    assert generate_month_dirname(dated) == "2025-03"
    assert generate_year_dirname(post("missing")) == "unknown"
    assert generate_month_dirname(post("missing")) == "unknown"

    config.job.group_by_year = False
    assert generate_grouped_post_path(dated, Path("root")) == Path("root")
    config.job.group_by_year = True
    assert generate_grouped_post_path(dated, Path("root")) == Path("root/2025")
    config.job.group_by_month = True
    assert generate_grouped_post_path(dated, Path("root")) == Path("root/2025/2025-03")


@pytest.mark.parametrize(
    ("attribute", "value", "call"),
    [
        ("post_dirname_format", "{invalid}", lambda item: generate_post_path_name(item)),
        ("year_dirname_format", "{invalid}", lambda item: generate_year_dirname(item)),
        ("month_dirname_format", "{invalid}", lambda item: generate_month_dirname(item)),
        ("filename_format", "{invalid}", lambda item: generate_filename(item, "file.jpg", config.job.filename_format)),
    ],
)
def test_invalid_path_formats_exit(attribute: str, value: str, call) -> None:
    setattr(config.job, attribute, value)
    with pytest.raises(SystemExit):
        call(post("42", "Title", datetime(2025, 1, 1)))


def test_date_keyword_and_index_filters() -> None:
    early = post("early", "Alpha", datetime(2024, 1, 1), datetime(2024, 1, 2))
    late = post("late", "Beta Release", datetime(2025, 1, 1), datetime(2025, 1, 2))
    undated = post("undated", None)
    posts = [early, late, undated]

    assert list(filter_posts_by_date(posts, datetime(2024, 6, 1), None)) == [late, undated]
    assert list(filter_posts_by_date(posts, None, datetime(2024, 6, 1))) == [early, undated]
    assert match_post_keywords(late, {"release"})
    assert not match_post_keywords(undated, {"release"})
    assert match_post_keywords(undated, set())
    assert list(filter_posts_by_keywords(posts, None)) == posts
    assert list(filter_posts_by_keywords(posts, {"alpha"})) == [early]
    assert list(filter_posts_by_keywords_exclude(posts, None)) == posts
    assert list(filter_posts_by_keywords_exclude(posts, {"release"})) == [early, undated]

    old_late = late.model_copy(update={"edited": datetime(2024, 12, 1)})
    indices = CreatorIndices(
        creator_id="creator",
        service="fanbox",
        posts={"early": early, "late": old_late},
    )
    filtered, updated = filter_posts_by_indices(posts[:2], indices)
    assert filtered == [late]
    assert updated is not indices
    assert updated.posts["late"] == late
    assert indices.posts["late"] == old_late


def test_content_image_extraction_and_parse_failure() -> None:
    content = '<IMG SRC="/one.jpg"><img alt="x"><img src="https://example.test/two.png"><img src="">'
    assert extract_content_images(content) == ["/one.jpg", "https://example.test/two.png"]
    assert extract_content_images("") == []
    with patch("ktoolbox.action.utils._ContentImageParser.feed", side_effect=ValueError("bad html")):
        assert extract_content_images("<img>") == []
