from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
LOCALES = ("en", "zh", "zh-Hant", "ru", "ja", "ko", "fr")
README_BY_LOCALE = {
    "en": "README.md",
    "zh": "README_zh-CN.md",
    "zh-Hant": "README_zh-Hant.md",
    "ru": "README_ru.md",
    "ja": "README_ja.md",
    "ko": "README_ko.md",
    "fr": "README_fr.md",
}
README_LANGUAGE_NAV = (
    "[English](README.md) | [简体中文](README_zh-CN.md) | "
    "[繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | "
    "[日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)"
)
DOCS_URL_PREFIX = {
    "en": "https://ktoolbox.readthedocs.io/latest/",
    "zh": "https://ktoolbox.readthedocs.io/latest/zh/",
    "zh-Hant": "https://ktoolbox.readthedocs.io/latest/zh-Hant/",
    "ru": "https://ktoolbox.readthedocs.io/latest/ru/",
    "ja": "https://ktoolbox.readthedocs.io/latest/ja/",
    "ko": "https://ktoolbox.readthedocs.io/latest/ko/",
    "fr": "https://ktoolbox.readthedocs.io/latest/fr/",
}
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6}) ", re.MULTILINE)
TABLE_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$", re.MULTILINE)
FENCED_CODE_RE = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")


def _manifest(locale: str) -> set[Path]:
    return {path.relative_to(DOCS_ROOT / locale) for path in (DOCS_ROOT / locale).rglob("*.md")}


def _relative_targets(markdown: str) -> list[str]:
    targets = []
    for target in MARKDOWN_LINK_RE.findall(markdown):
        target = target.split("#", 1)[0].split("?", 1)[0]
        if target and "://" not in target and not target.startswith("mailto:"):
            targets.append(target)
    return targets


def _relative_links(markdown: str) -> list[str]:
    return [
        target
        for target in MARKDOWN_LINK_RE.findall(markdown)
        if "://" not in target and not target.startswith("mailto:")
    ]


def _code_contract(markdown: str) -> tuple[list[str], Counter[str]]:
    fenced = FENCED_CODE_RE.findall(markdown)
    executable = [
        "\n".join(line for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#"))
        for block in fenced
    ]
    without_fenced = FENCED_CODE_RE.sub("", markdown)
    return executable, Counter(INLINE_CODE_RE.findall(without_fenced))


def test_mkdocs_config_builds_every_locale_without_fallback() -> None:
    config = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "fallback_to_default: false" in config
    positions = [config.index(f"- locale: {locale}") for locale in LOCALES]
    assert positions == sorted(positions)


def test_readmes_have_complete_language_navigation_and_localized_docs_links() -> None:
    assert {path.name for path in PROJECT_ROOT.glob("README*.md")} == set(README_BY_LOCALE.values())

    for locale, filename in README_BY_LOCALE.items():
        readme = (PROJECT_ROOT / filename).read_text(encoding="utf-8")
        opening = readme.split("</div>", 1)[0]
        assert README_LANGUAGE_NAV in opening
        assert readme.count(README_LANGUAGE_NAV) == 1

        docs_links = [
            target
            for target in MARKDOWN_LINK_RE.findall(readme)
            if target.startswith("https://ktoolbox.readthedocs.io/latest/")
        ]
        assert docs_links
        assert all(target.startswith(DOCS_URL_PREFIX[locale]) for target in docs_links)


def test_localized_page_trees_and_markdown_structure_match_english() -> None:
    english_manifest = _manifest("en")
    assert len(english_manifest) == 11

    for locale in LOCALES[1:]:
        assert _manifest(locale) == english_manifest
        for relative_path in english_manifest:
            english = (DOCS_ROOT / "en" / relative_path).read_text(encoding="utf-8")
            localized = (DOCS_ROOT / locale / relative_path).read_text(encoding="utf-8")

            assert localized != english
            assert HEADING_RE.findall(localized) == HEADING_RE.findall(english)
            assert _code_contract(localized) == _code_contract(english)
            assert len(TABLE_SEPARATOR_RE.findall(localized)) == len(TABLE_SEPARATOR_RE.findall(english))
            assert _relative_targets(localized) == _relative_targets(english)


def test_all_relative_markdown_links_resolve() -> None:
    markdown_files = [PROJECT_ROOT / filename for filename in README_BY_LOCALE.values()]
    markdown_files.extend(DOCS_ROOT.glob("*/**/*.md"))

    for markdown_file in markdown_files:
        markdown = markdown_file.read_text(encoding="utf-8")
        for target in _relative_links(markdown):
            path, _, fragment = target.partition("#")
            path = path.split("?", 1)[0]
            resolved = (markdown_file.parent / path).resolve()
            assert resolved.exists(), f"{markdown_file.relative_to(PROJECT_ROOT)} -> {target}"
            if fragment:
                destination = resolved.read_text(encoding="utf-8")
                assert f"{{#{fragment}}}" in destination, f"{markdown_file.relative_to(PROJECT_ROOT)} -> {target}"
