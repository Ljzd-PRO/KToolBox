from __future__ import annotations

import asyncio
import io
import warnings
from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

from ktoolbox.action.utils import extract_content_images
from ktoolbox.api.generated import CreatorSummary, Post, Revision
from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.models import (
    CreatorSearchItemResponse,
    MediaAssetResponse,
    PawchivePostDetailResponse,
    PawchivePostSummaryResponse,
    PawchiveRevisionDetailResponse,
    PawchiveRevisionSummaryResponse,
)

MediaVariant = Literal["thumbnail", "preview", "original"]
CreatorMediaKind = Literal["avatar", "banner"]
AssetKind = Literal["avatar", "banner", "cover", "attachment", "content"]

MAX_MEDIA_BYTES = 32 * 1024 * 1024
MAX_MEDIA_PIXELS = 50_000_000
THUMBNAIL_MAX_EDGE = 480
PREVIEW_MAX_EDGE = 1280
ALLOWED_IMAGE_FORMATS = {"GIF", "JPEG", "PNG", "WEBP"}


class MediaProxyError(Exception):
    code = "media_unavailable"
    status_code = 502


class MediaNotFoundError(MediaProxyError):
    code = "media_not_found"
    status_code = 404


class MediaTooLargeError(MediaProxyError):
    code = "media_too_large"
    status_code = 413


class MediaUnsupportedError(MediaProxyError):
    code = "media_unsupported"
    status_code = 415


@dataclass(frozen=True, slots=True)
class MediaPayload:
    content: bytes
    media_type: str


class MediaProxyService:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        cache_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        self._client = client
        self._owns_client = client is None
        self._cache_limit = cache_bytes
        self._cache_size = 0
        self._cache: OrderedDict[str, MediaPayload] = OrderedDict()
        self._cache_lock = asyncio.Lock()

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                follow_redirects=False,
                limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
                headers={"Accept": "image/avif,image/webp,image/png,image/jpeg,image/gif"},
            )

    async def stop(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
        self._client = None
        async with self._cache_lock:
            self._cache.clear()
            self._cache_size = 0

    async def fetch_creator(
        self,
        context: RuntimeContext,
        platform: str,
        creator_id: str,
        kind: CreatorMediaKind,
        variant: MediaVariant,
    ) -> MediaPayload:
        configuration = context.configuration
        resource = "icons" if kind == "avatar" else "banners"
        path = f"/{resource}/{quote(platform, safe='')}/{quote(creator_id, safe='')}"
        url = urlunsplit((configuration.api.scheme, configuration.api.statics_netloc, path, "", ""))
        return await self._fetch(url, variant, timeout=configuration.api.timeout)

    async def fetch_file(
        self,
        context: RuntimeContext,
        source_path: str,
        variant: MediaVariant,
    ) -> MediaPayload:
        path = normalize_file_path(source_path)
        configuration = context.configuration
        prefix = f"/{configuration.downloader.file_path_prefix.strip('/')}"
        if path != prefix and not path.startswith(f"{prefix}/"):
            path = f"{prefix}{path}"
        url = urlunsplit((configuration.downloader.scheme, configuration.downloader.files_netloc, path, "", ""))
        headers: dict[str, str] = {}
        if configuration.downloader.session_key:
            headers["Cookie"] = f"session={configuration.downloader.session_key}"
        return await self._fetch(url, variant, headers=headers, timeout=configuration.api.timeout)

    async def _fetch(
        self,
        url: str,
        variant: MediaVariant,
        *,
        timeout: float,
        headers: dict[str, str] | None = None,
    ) -> MediaPayload:
        cache_key = f"{variant}:{url}"
        if variant != "original":
            cached = await self._cache_get(cache_key)
            if cached is not None:
                return cached

        client = self._client
        if client is None:
            raise RuntimeError("media proxy service is not running")
        try:
            async with client.stream("GET", url, headers=headers, timeout=timeout) as response:
                if response.status_code == 404:
                    raise MediaNotFoundError
                if response.status_code != 200:
                    raise MediaProxyError
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_MEDIA_BYTES:
                    raise MediaTooLargeError
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_MEDIA_BYTES:
                        raise MediaTooLargeError
                    chunks.append(chunk)
        except MediaProxyError:
            raise
        except (httpx.HTTPError, ValueError) as error:
            raise MediaProxyError from error

        payload = await asyncio.to_thread(process_media, b"".join(chunks), variant)
        if variant != "original":
            await self._cache_put(cache_key, payload)
        return payload

    async def _cache_get(self, key: str) -> MediaPayload | None:
        async with self._cache_lock:
            payload = self._cache.pop(key, None)
            if payload is not None:
                self._cache[key] = payload
            return payload

    async def _cache_put(self, key: str, payload: MediaPayload) -> None:
        if len(payload.content) > self._cache_limit:
            return
        async with self._cache_lock:
            previous = self._cache.pop(key, None)
            if previous is not None:
                self._cache_size -= len(previous.content)
            self._cache[key] = payload
            self._cache_size += len(payload.content)
            while self._cache_size > self._cache_limit and self._cache:
                _, removed = self._cache.popitem(last=False)
                self._cache_size -= len(removed.content)


def normalize_file_path(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise MediaUnsupportedError
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise MediaUnsupportedError
    parts = parsed.path.split("/")
    if not parsed.path.startswith("/") or any(part in {".", ".."} for part in parts):
        raise MediaUnsupportedError
    return "/" + "/".join(part for part in parts if part)


def process_media(content: bytes, variant: MediaVariant) -> MediaPayload:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as candidate:
                image_format = candidate.format or ""
                width, height = candidate.size
                if image_format not in ALLOWED_IMAGE_FORMATS:
                    raise MediaUnsupportedError
                if width * height > MAX_MEDIA_PIXELS:
                    raise MediaTooLargeError
                candidate.verify()
    except MediaProxyError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise MediaTooLargeError from None
    except (OSError, UnidentifiedImageError, ValueError):
        raise MediaUnsupportedError from None

    if variant == "original":
        media_type = Image.MIME.get(image_format)
        if not media_type:
            raise MediaUnsupportedError
        return MediaPayload(content, media_type)

    max_edge = THUMBNAIL_MAX_EDGE if variant == "thumbnail" else PREVIEW_MAX_EDGE
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.seek(0)
            image = ImageOps.exif_transpose(source)
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            converted = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            output = io.BytesIO()
            converted.save(output, format="WEBP", quality=82, method=6)
    except (OSError, ValueError):
        raise MediaUnsupportedError from None
    return MediaPayload(output.getvalue(), "image/webp")


def creator_asset(platform: str, creator_id: str, kind: CreatorMediaKind) -> MediaAssetResponse:
    base = f"/api/v1/media/creators/{quote(platform, safe='')}/{quote(creator_id, safe='')}/{kind}"
    return _asset(kind, base)


def file_asset(path: str, kind: Literal["cover", "attachment", "content"]) -> MediaAssetResponse:
    base = f"/api/v1/media/files?{urlencode({'path': path})}"
    return _asset(kind, base)


def creator_search_item(creator: CreatorSummary) -> CreatorSearchItemResponse:
    data = creator.model_dump()
    data["avatar"] = creator_asset(creator.service, creator.id, "avatar")
    data["banner"] = creator_asset(creator.service, creator.id, "banner")
    return CreatorSearchItemResponse.model_validate(data)


def post_summary(post: Post) -> PawchivePostSummaryResponse:
    data = post.model_dump()
    data["cover"] = file_asset(post.file.path, "cover") if post.file and post.file.path else None
    return PawchivePostSummaryResponse.model_validate(data)


def post_detail(post: Post) -> PawchivePostDetailResponse:
    data = post_summary(post).model_dump()
    data["media"] = post_media(post)
    return PawchivePostDetailResponse.model_validate(data)


def revision_summary(revision: Revision) -> PawchiveRevisionSummaryResponse:
    data = revision.model_dump()
    data["cover"] = file_asset(revision.file.path, "cover") if revision.file and revision.file.path else None
    return PawchiveRevisionSummaryResponse.model_validate(data)


def revision_detail(revision: Revision) -> PawchiveRevisionDetailResponse:
    data = revision_summary(revision).model_dump()
    data["media"] = post_media(revision)
    return PawchiveRevisionDetailResponse.model_validate(data)


def post_media(post: Post | Revision) -> list[MediaAssetResponse]:
    result: list[MediaAssetResponse] = []
    seen: set[str] = set()

    def add(path: str | None, kind: Literal["cover", "attachment", "content"]) -> None:
        if not path:
            return
        try:
            normalized = normalize_file_path(path)
        except MediaProxyError:
            return
        if normalized in seen:
            return
        seen.add(normalized)
        result.append(file_asset(normalized, kind))

    if post.file:
        add(post.file.path, "cover")
    for attachment in post.attachments or []:
        add(attachment.path, "attachment")
    for source in extract_content_images(post.content or ""):
        parsed = urlsplit(source)
        if source.startswith("/") or parsed.scheme in {"http", "https"}:
            add(parsed.path, "content")
    return result


def _asset(kind: AssetKind, base: str) -> MediaAssetResponse:
    separator = "&" if "?" in base else "?"
    return MediaAssetResponse(
        kind=kind,
        thumbnail_url=f"{base}{separator}variant=thumbnail",
        preview_url=f"{base}{separator}variant=preview",
        original_url=f"{base}{separator}variant=original",
    )
