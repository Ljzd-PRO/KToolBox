from __future__ import annotations

import inspect
import io
import os
import re
from pathlib import Path
from typing import Any, Literal

from docutils import nodes  # type: ignore[import-untyped]
from docutils.core import publish_doctree  # type: ignore[import-untyped]
from dotenv import dotenv_values
from pydantic import BaseModel, SecretStr, TypeAdapter

import ktoolbox._configuration_zh as configuration_zh
from ktoolbox.configuration import (
    APIConfiguration,
    Configuration,
    DownloaderConfiguration,
    JobConfiguration,
    LoggerConfiguration,
    PostStructureConfiguration,
    WebUIConfiguration,
)
from ktoolbox.webui.config_locale_catalogs import CONFIG_LOCALE_CATALOGS
from ktoolbox.webui.models import ConfigFieldResponse, ConfigSchemaResponse, PathSelectorResponse

Locale = Literal["zh-CN", "zh-Hant", "en", "ja", "ko", "fr", "ru"]

_MODEL_TRANSLATIONS: dict[type[BaseModel], type[BaseModel]] = {
    Configuration: configuration_zh.Configuration,
    APIConfiguration: configuration_zh.APIConfiguration,
    DownloaderConfiguration: configuration_zh.DownloaderConfiguration,
    JobConfiguration: configuration_zh.JobConfiguration,
    PostStructureConfiguration: configuration_zh.PostStructureConfiguration,
    LoggerConfiguration: configuration_zh.LoggerConfiguration,
    WebUIConfiguration: configuration_zh.WebUIConfiguration,
}

_LABELS: dict[str, tuple[str, str]] = {
    "api.scheme": ("API protocol", "API 协议"),
    "api.netloc": ("API host", "API 主机"),
    "api.statics_netloc": ("Static asset host", "静态资源主机"),
    "api.path": ("API root path", "API 根路径"),
    "api.timeout": ("API timeout", "API 超时时间"),
    "api.retry_times": ("API retry attempts", "API 重试次数"),
    "api.retry_interval": ("API retry interval", "API 重试间隔"),
    "downloader.scheme": ("File protocol", "文件下载协议"),
    "downloader.files_netloc": ("File host", "文件主机"),
    "downloader.file_path_prefix": ("File path prefix", "文件路径前缀"),
    "downloader.session_key": ("File session key", "文件会话密钥"),
    "downloader.timeout": ("Download timeout", "下载超时时间"),
    "downloader.encoding": ("Text encoding", "文本编码"),
    "downloader.buffer_size": ("File buffer size", "文件缓冲区大小"),
    "downloader.chunk_size": ("Download chunk size", "下载分块大小"),
    "downloader.temp_suffix": ("Temporary suffix", "临时文件后缀"),
    "downloader.retry_times": ("Download retry attempts", "下载重试次数"),
    "downloader.retry_stop_never": ("Retry without limit", "无限重试"),
    "downloader.retry_interval": ("Download retry interval", "下载重试间隔"),
    "downloader.tps_limit": ("Connections per second", "每秒连接数"),
    "downloader.use_bucket": ("Storage bucket mode", "存储桶模式"),
    "downloader.bucket_path": ("Storage bucket path", "存储桶路径"),
    "downloader.reverse_proxy": ("Download reverse proxy", "下载反向代理"),
    "downloader.keep_metadata": ("Preserve file metadata", "保留文件元数据"),
    "job.count": ("Concurrent downloads", "并发下载数"),
    "job.creator_concurrency": ("Concurrent creators", "并发作者数"),
    "job.include_revisions": ("Include revisions", "包含修订版本"),
    "job.post_dirname_format": ("Post directory format", "作品目录格式"),
    "job.post_structure.attachments": ("Attachment directory", "附件目录"),
    "job.post_structure.content": ("Content file", "正文文件"),
    "job.post_structure.external_links": ("External links file", "外部链接文件"),
    "job.post_structure.file": ("Primary file format", "主文件名格式"),
    "job.post_structure.revisions": ("Revision directory", "修订目录"),
    "job.mix_posts": ("Mix post files", "混合作品文件"),
    "job.sequential_filename": ("Sequential filenames", "顺序文件名"),
    "job.sequential_filename_excludes": ("Sequential naming exclusions", "顺序命名排除项"),
    "job.filename_format": ("Attachment filename format", "附件文件名格式"),
    "job.allow_list": ("Allowed file patterns", "允许的文件模式"),
    "job.block_list": ("Blocked file patterns", "屏蔽的文件模式"),
    "job.extract_content": ("Save post content", "保存作品正文"),
    "job.extract_content_images": ("Download content images", "下载正文图片"),
    "job.extract_external_links": ("Save external links", "保存外部链接"),
    "job.external_link_patterns": ("External link patterns", "外部链接模式"),
    "job.group_by_year": ("Group by year", "按年份分组"),
    "job.group_by_month": ("Group by month", "按月份分组"),
    "job.year_dirname_format": ("Year directory format", "年份目录格式"),
    "job.month_dirname_format": ("Month directory format", "月份目录格式"),
    "job.keywords": ("Required title keywords", "标题包含关键词"),
    "job.keywords_exclude": ("Legacy excluded keywords", "旧版排除关键词"),
    "job.download_file": ("Download primary file", "下载主文件"),
    "job.download_attachments": ("Download attachments", "下载附件"),
    "job.min_file_size": ("Minimum file size", "最小文件大小"),
    "job.max_file_size": ("Maximum file size", "最大文件大小"),
    "logger.path": ("Log directory", "日志目录"),
    "logger.level": ("Log level", "日志级别"),
    "logger.rotation": ("Log rotation", "日志轮换"),
    "webui.host": ("WebUI listen address", "WebUI 监听地址"),
    "webui.port": ("WebUI port", "WebUI 端口"),
    "webui.open_browser": ("Open browser on startup", "启动时打开浏览器"),
    "webui.username": ("WebUI username", "WebUI 用户名"),
    "webui.password_hash": ("WebUI password hash", "WebUI 密码哈希"),
    "webui.password": ("WebUI plaintext password", "WebUI 明文密码"),
    "webui.max_active_tasks": ("Active task limit", "活动任务上限"),
    "webui.session_idle_hours": ("Session idle lifetime", "会话空闲期限"),
    "webui.session_absolute_hours": ("Maximum session lifetime", "会话最长期限"),
    "ssl_verify": ("Verify TLS certificates", "验证 TLS 证书"),
    "json_dump_indent": ("JSON indentation", "JSON 缩进"),
    "use_uvloop": ("Use optimized event loop", "使用优化事件循环"),
}

_SECTION_LABELS: dict[str, tuple[str, str]] = {
    "api": ("Pawchive API", "Pawchive API"),
    "downloader": ("File downloads", "文件下载"),
    "job": ("Download jobs", "下载任务"),
    "logger": ("Logging", "日志"),
    "webui": ("WebUI", "WebUI"),
    "general": ("General", "常规"),
}

_SECRET_PATHS = {"downloader.session_key", "webui.password", "webui.password_hash"}
_PATH_SELECTORS: dict[str, PathSelectorResponse] = {
    "downloader.bucket_path": PathSelectorResponse(kind="directory", scope="host", value_mode="absolute"),
    "logger.path": PathSelectorResponse(kind="directory", scope="host", value_mode="absolute"),
    "job.post_structure.attachments": PathSelectorResponse(
        kind="directory", scope="project", value_mode="project_relative"
    ),
    "job.post_structure.revisions": PathSelectorResponse(
        kind="directory", scope="project", value_mode="project_relative"
    ),
    "job.post_structure.content": PathSelectorResponse(kind="file", scope="project", value_mode="project_relative"),
    "job.post_structure.external_links": PathSelectorResponse(
        kind="file", scope="project", value_mode="project_relative"
    ),
}
_RESTART_PATHS = {
    "webui.host",
    "webui.port",
    "webui.open_browser",
    "webui.username",
    "webui.password",
    "webui.password_hash",
    "webui.session_idle_hours",
    "webui.session_absolute_hours",
    "use_uvloop",
}
_IVAR_PATTERN = re.compile(r"^:ivar\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def build_config_schema(configuration: Configuration, project_root: Path, locale: Locale) -> ConfigSchemaResponse:
    dotenv_sources = _dotenv_sources(project_root)
    fields: list[ConfigFieldResponse] = []
    _walk_model(
        Configuration,
        configuration,
        locale,
        dotenv_sources,
        fields,
    )
    sections = _localized_sections(locale)
    return ConfigSchemaResponse(locale=locale, sections=sections, fields=fields)


def missing_config_metadata() -> dict[str, list[str]]:
    descriptions_en: dict[str, str] = {}
    descriptions_zh: dict[str, str] = {}
    _collect_descriptions(Configuration, "", "en", descriptions_en)
    _collect_descriptions(Configuration, "", "zh-CN", descriptions_zh)
    paths = set(_field_paths(Configuration))
    missing = {
        "labels": sorted(paths - _LABELS.keys()),
        "english_descriptions": sorted(paths - descriptions_en.keys()),
        "chinese_descriptions": sorted(paths - descriptions_zh.keys()),
    }
    for locale, catalog in CONFIG_LOCALE_CATALOGS.items():
        missing[f"{locale}_labels"] = sorted(paths - catalog["labels"].keys())
        missing[f"{locale}_descriptions"] = sorted(paths - catalog["descriptions"].keys())
    return missing


def _walk_model(
    model: type[BaseModel],
    instance: BaseModel,
    locale: Locale,
    dotenv_sources: dict[str, str],
    result: list[ConfigFieldResponse],
    prefix: str = "",
) -> None:
    descriptions: dict[str, str] = {}
    _collect_descriptions(model, prefix, locale, descriptions)
    property_schemas = model.model_json_schema(mode="validation").get("properties", {})
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}" if prefix else name
        value = getattr(instance, name)
        nested_model = _model_type(field.annotation)
        if nested_model is not None:
            _walk_model(nested_model, value, locale, dotenv_sources, result, path)
            continue
        env_name = f"KTOOLBOX_{path.replace('.', '__').upper()}"
        secret = path in _SECRET_PATHS
        serialized = None if secret else _serialize_value(field.annotation, value)
        result.append(
            ConfigFieldResponse(
                path=path,
                env_name=env_name,
                section=path.split(".", 1)[0] if "." in path else "general",
                label=_localized_label(path, locale),
                description=descriptions[path],
                json_schema=dict(property_schemas[name]),
                default=None
                if secret
                else _serialize_value(field.annotation, field.get_default(call_default_factory=True)),
                value=serialized,
                is_set=bool(value.get_secret_value()) if isinstance(value, SecretStr) else value is not None,
                secret=secret,
                source=_value_source(env_name, dotenv_sources),
                apply_mode="restart" if path in _RESTART_PATHS else "next_task",
                path_selector=_PATH_SELECTORS.get(path),
            )
        )


def _collect_descriptions(
    model: type[BaseModel],
    prefix: str,
    locale: Locale,
    result: dict[str, str],
) -> None:
    if locale not in ("en", "zh-CN"):
        catalog = CONFIG_LOCALE_CATALOGS[locale]["descriptions"]
        for path in _field_paths(model, prefix):
            result[path] = catalog[path]
        return
    source_model = model if locale == "en" else _MODEL_TRANSLATIONS[model]
    descriptions = _parse_ivar_descriptions(inspect.getdoc(source_model) or "")
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}" if prefix else name
        nested_model = _model_type(field.annotation)
        if nested_model is not None:
            _collect_descriptions(nested_model, path, locale, result)
        else:
            description = descriptions.get(name)
            if description:
                result[path] = description


def _localized_label(path: str, locale: Locale) -> str:
    if locale in ("en", "zh-CN"):
        return _LABELS[path][0 if locale == "en" else 1]
    return CONFIG_LOCALE_CATALOGS[locale]["labels"][path]


def _localized_sections(locale: Locale) -> dict[str, str]:
    if locale in ("en", "zh-CN"):
        index = 0 if locale == "en" else 1
        return {key: labels[index] for key, labels in _SECTION_LABELS.items()}
    return dict(CONFIG_LOCALE_CATALOGS[locale]["sections"])


def _parse_ivar_descriptions(docstring: str) -> dict[str, str]:
    extracted: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in docstring.splitlines():
        match = _IVAR_PATTERN.match(line.strip())
        if match:
            current = (match.group(1), [match.group(2)])
            extracted.append(current)
        elif current is not None and line.strip():
            current[1].append(line.strip())
    normalized = "\n".join(f":ivar {name}: {' '.join(parts)}" for name, parts in extracted)
    if not normalized:
        return {}
    document = publish_doctree(
        normalized,
        settings_overrides={"report_level": 5, "halt_level": 6, "warning_stream": io.StringIO()},
    )
    parsed: dict[str, str] = {}
    for field in document.findall(nodes.field):
        field_name = field[0].astext()
        if field_name.startswith("ivar "):
            parsed[field_name.removeprefix("ivar ")] = field[1].astext().strip()
    return parsed


def _model_type(annotation: Any) -> type[BaseModel] | None:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _serialize_value(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    return TypeAdapter(annotation).dump_python(value, mode="json")


def _field_paths(model: type[BaseModel], prefix: str = "") -> list[str]:
    result: list[str] = []
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}" if prefix else name
        nested_model = _model_type(field.annotation)
        if nested_model is None:
            result.append(path)
        else:
            result.extend(_field_paths(nested_model, path))
    return result


def _dotenv_sources(project_root: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for filename in (".env", "prod.env"):
        path = project_root / filename
        if path.exists():
            for key in dotenv_values(path):
                sources[key.upper()] = filename
    return sources


def _value_source(env_name: str, dotenv_sources: dict[str, str]) -> str:
    if env_name in os.environ:
        return "environment"
    return dotenv_sources.get(env_name, "default")
