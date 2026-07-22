from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from typing import Literal

from ktoolbox.webui.models import (
    FilesystemBreadcrumbResponse,
    FilesystemBrowseResponse,
    FilesystemEntryResponse,
    FilesystemLocationResponse,
)

FilesystemScope = Literal["project", "host"]
FilesystemMode = Literal["directory", "file"]


class FilesystemBrowserError(Exception):
    """A sanitized filesystem browser failure."""


class FilesystemForbiddenError(FilesystemBrowserError):
    pass


class FilesystemNotFoundError(FilesystemBrowserError):
    pass


class FilesystemConflictError(FilesystemBrowserError):
    pass


class FilesystemInvalidError(FilesystemBrowserError):
    pass


@dataclass(frozen=True, slots=True)
class _ResolvedRequest:
    directory: Path
    suggested_name: str | None


class FilesystemBrowser:
    def __init__(
        self,
        project_root: Path,
        *,
        home: Path | None = None,
        host_roots: tuple[Path, ...] | None = None,
        restrict_host_to_roots: bool = False,
    ) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.home = (home or Path.home()).expanduser().resolve()
        self.host_roots = tuple(root.expanduser().resolve() for root in (host_roots or _system_roots()))
        self.restrict_host_to_roots = restrict_host_to_roots

    async def browse(
        self,
        *,
        scope: FilesystemScope,
        mode: FilesystemMode,
        path: str | None,
        search: str,
        include_hidden: bool,
        offset: int,
        limit: int,
    ) -> FilesystemBrowseResponse:
        return await asyncio.to_thread(
            self._browse,
            scope=scope,
            mode=mode,
            path=path,
            search=search,
            include_hidden=include_hidden,
            offset=offset,
            limit=limit,
        )

    async def create_directory(
        self,
        *,
        scope: FilesystemScope,
        parent: str,
        name: str,
    ) -> FilesystemEntryResponse:
        return await asyncio.to_thread(self._create_directory, scope=scope, parent=parent, name=name)

    def _browse(
        self,
        *,
        scope: FilesystemScope,
        mode: FilesystemMode,
        path: str | None,
        search: str,
        include_hidden: bool,
        offset: int,
        limit: int,
    ) -> FilesystemBrowseResponse:
        requested = self._requested_path(path)
        self._ensure_allowed(requested, scope)
        resolved = self._resolve_request(requested, mode)
        self._ensure_allowed(resolved.directory, scope)
        entries = self._entries(resolved.directory, scope, search, include_hidden)
        page = entries[offset : offset + limit]
        current = str(resolved.directory)
        return FilesystemBrowseResponse(
            scope=scope,
            mode=mode,
            path=current,
            project_relative_path=self._project_relative(resolved.directory) if scope == "project" else None,
            parent=self._parent(resolved.directory, scope),
            separator=os.sep,
            breadcrumbs=[
                FilesystemBreadcrumbResponse(label=label, path=crumb_path)
                for label, crumb_path in path_breadcrumbs(
                    current,
                    separator=os.sep,
                    project_root=str(self.project_root) if scope == "project" else None,
                )
            ],
            locations=self._locations(scope),
            entries=page,
            suggested_name=resolved.suggested_name,
            offset=offset,
            limit=limit,
            has_more=offset + limit < len(entries),
        )

    def _create_directory(
        self,
        *,
        scope: FilesystemScope,
        parent: str,
        name: str,
    ) -> FilesystemEntryResponse:
        if not _valid_child_name(name):
            raise FilesystemInvalidError("Directory name is invalid")
        parent_path = self._requested_path(parent)
        self._ensure_allowed(parent_path, scope)
        try:
            if not parent_path.exists():
                raise FilesystemNotFoundError("Parent directory was not found")
            if not parent_path.is_dir():
                raise FilesystemInvalidError("Parent path is not a directory")
            target = parent_path / name
            self._ensure_allowed(target, scope)
            target.mkdir()
        except FileExistsError as error:
            raise FilesystemConflictError("A file or directory with that name already exists") from error
        except PermissionError as error:
            raise FilesystemForbiddenError("Permission denied") from error
        except OSError as error:
            raise FilesystemInvalidError("Directory could not be created") from error
        return self._entry(target, scope)

    def _requested_path(self, value: str | None) -> Path:
        if value is None or not value.strip():
            return self.project_root
        expanded = Path(value).expanduser()
        if not expanded.is_absolute():
            expanded = self.project_root / expanded
        try:
            return expanded.resolve(strict=False)
        except (OSError, RuntimeError) as error:
            raise FilesystemInvalidError("Path is invalid") from error

    def _resolve_request(self, requested: Path, mode: FilesystemMode) -> _ResolvedRequest:
        try:
            if requested.exists():
                if requested.is_dir():
                    return _ResolvedRequest(requested, None)
                if mode == "file" and requested.is_file():
                    return _ResolvedRequest(requested.parent, requested.name)
                raise FilesystemInvalidError("Path is not a directory")
            parent = requested.parent
            if not parent.exists():
                raise FilesystemNotFoundError("Parent directory was not found")
            if not parent.is_dir():
                raise FilesystemInvalidError("Parent path is not a directory")
            return _ResolvedRequest(parent, requested.name or None)
        except PermissionError as error:
            raise FilesystemForbiddenError("Permission denied") from error
        except OSError as error:
            raise FilesystemInvalidError("Path could not be inspected") from error

    def _entries(
        self,
        directory: Path,
        scope: FilesystemScope,
        search: str,
        include_hidden: bool,
    ) -> list[FilesystemEntryResponse]:
        try:
            children = list(directory.iterdir())
        except FileNotFoundError as error:
            raise FilesystemNotFoundError("Directory was not found") from error
        except PermissionError as error:
            raise FilesystemForbiddenError("Permission denied") from error
        except OSError as error:
            raise FilesystemInvalidError("Directory could not be read") from error
        query = search.casefold().strip()
        entries = [
            self._entry(child, scope)
            for child in children
            if (include_hidden or not _is_hidden(child)) and (not query or query in child.name.casefold())
        ]
        return sorted(entries, key=lambda entry: (entry.kind != "directory", entry.name.casefold(), entry.name))

    def _entry(self, path: Path, scope: FilesystemScope) -> FilesystemEntryResponse:
        try:
            is_symlink = path.is_symlink()
            if path.is_dir():
                kind: Literal["directory", "file", "other"] = "directory"
            elif path.is_file():
                kind = "file"
            else:
                kind = "other"
            navigable = kind == "directory" and self._is_allowed(path, scope)
        except (OSError, RuntimeError):
            is_symlink = False
            kind = "other"
            navigable = False
        return FilesystemEntryResponse(
            name=path.name,
            path=str(path),
            project_relative_path=self._project_relative(path) if scope == "project" else None,
            kind=kind,
            is_symlink=is_symlink,
            navigable=navigable,
        )

    def _locations(self, scope: FilesystemScope) -> list[FilesystemLocationResponse]:
        candidates: list[tuple[str, str, Path]] = [("project", "Project", self.project_root)]
        if scope == "host":
            candidates.append(("home", "Home", self.home))
            candidates.extend((f"root-{index}", _root_label(root), root) for index, root in enumerate(self.host_roots))
        locations: list[FilesystemLocationResponse] = []
        seen: set[Path] = set()
        for location_id, label, path in candidates:
            if path in seen or not path.is_dir() or not self._is_allowed(path, scope):
                continue
            seen.add(path)
            locations.append(FilesystemLocationResponse(id=location_id, label=label, path=str(path)))
        return locations

    def _parent(self, path: Path, scope: FilesystemScope) -> str | None:
        if scope == "project" and path == self.project_root:
            return None
        if self.restrict_host_to_roots and scope == "host" and path in self.host_roots:
            return None
        parent = path.parent
        if parent == path or not self._is_allowed(parent, scope):
            return None
        return str(parent)

    def _project_relative(self, path: Path) -> str | None:
        try:
            relative = path.resolve(strict=False).relative_to(self.project_root)
        except (OSError, RuntimeError, ValueError):
            return None
        return str(relative) if relative.parts else "."

    def _is_allowed(self, path: Path, scope: FilesystemScope) -> bool:
        try:
            resolved = path.resolve(strict=False)
        except (OSError, RuntimeError):
            return False
        if scope == "project":
            return resolved == self.project_root or self.project_root in resolved.parents
        if not self.restrict_host_to_roots:
            return True
        return any(resolved == root or root in resolved.parents for root in self.host_roots)

    def _ensure_allowed(self, path: Path, scope: FilesystemScope) -> None:
        if not self._is_allowed(path, scope):
            raise FilesystemForbiddenError("Path is outside the allowed scope")


def path_breadcrumbs(
    path: str,
    *,
    separator: str,
    project_root: str | None = None,
) -> list[tuple[str, str]]:
    pure_class = PureWindowsPath if separator == "\\" else PurePosixPath
    pure_path: PurePath = pure_class(path)
    pure_root: PurePath | None = pure_class(project_root) if project_root else None
    if pure_root is not None:
        try:
            relative = pure_path.relative_to(pure_root)
        except ValueError:
            return []
        crumbs = [("Project", str(pure_root))]
        current = pure_root
        for part in relative.parts:
            current = current / part
            crumbs.append((part, str(current)))
        return crumbs
    parts = pure_path.parts
    if not parts:
        return []
    current = type(pure_path)(parts[0])
    label = parts[0].rstrip("/\\") or parts[0]
    crumbs = [(label, str(current))]
    for part in parts[1:]:
        current = current / part
        crumbs.append((part, str(current)))
    return crumbs


def _valid_child_name(name: str) -> bool:
    return (
        bool(name.strip())
        and name == name.strip()
        and name not in {".", ".."}
        and not any(separator in name for separator in {"/", "\\", "\0"})
    )


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    try:
        return bool(path.stat(follow_symlinks=False).st_file_attributes & 2)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False


def _root_label(path: Path) -> str:
    anchor = path.anchor.rstrip("/\\")
    return anchor or str(path)


def _system_roots() -> tuple[Path, ...]:
    list_drives = getattr(os, "listdrives", None)
    if list_drives is not None:
        return tuple(Path(drive) for drive in list_drives())
    return (Path(os.sep),)
