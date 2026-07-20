from __future__ import annotations

from datetime import datetime
from pathlib import Path

import aiofiles  # type: ignore[import-untyped]
from loguru import logger
from pathvalidate import sanitize_filename
from pydantic import BaseModel, ValidationError
from settings_doc import OutputFormat, render  # type: ignore[import-untyped]

from ktoolbox import __version__
from ktoolbox._enum import TextEnum
from ktoolbox.action import (
    FetchInterruptError,
    create_job_from_creator,
    create_job_from_post,
    generate_post_path_name,
)
from ktoolbox.action import search_creator as search_creator_action
from ktoolbox.action import search_creator_post as search_creator_post_action
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveError, PawchiveNotFoundError
from ktoolbox.api.generated import Post, Revision
from ktoolbox.api.utils import create_pawchive_client
from ktoolbox.configuration import config
from ktoolbox.job import JobRunner
from ktoolbox.utils import check_for_updates, dump_search, generate_msg, parse_webpage_url

__all__ = ["KToolBoxCli"]


async def _requested_post(
    client: PawchiveClient,
    service: str,
    creator_id: str,
    post_id: str,
    revision_id: str | None,
) -> Post | Revision:
    if revision_id is None:
        return await client.get_post(service, creator_id, post_id)

    revisions = await client.list_post_revisions(service, creator_id, post_id)
    revision = next((item for item in revisions if str(item.revision_id) == str(revision_id)), None)
    if revision is None:
        raise LookupError(f"Revision {revision_id} was not found")
    return revision


async def _dump_model(model: BaseModel, path: Path) -> None:
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(model.model_dump_json(indent=config.json_dump_indent))


def _error_message(error: Exception) -> str:
    message = str(error)
    logger.error(message)
    return message


class KToolBoxCli:
    _update_checked = False

    @classmethod
    async def _ensure_update_check(cls) -> None:
        """Perform the optional release check at most once per process."""
        if cls._update_checked:
            return
        try:
            await check_for_updates()
        except Exception:
            pass
        finally:
            cls._update_checked = True

    @staticmethod
    async def version() -> str:
        """Show KToolBox version."""
        await check_for_updates()
        return __version__

    @staticmethod
    async def site_version() -> str:
        """Show the current Pawchive application version."""
        try:
            async with create_pawchive_client() as client:
                return await client.get_app_version()
        except PawchiveError as error:
            return _error_message(error)

    @staticmethod
    async def config_editor() -> None:
        """Launch the graphical KToolBox configuration editor."""
        try:
            from ktoolbox.editor import run_config_editor

            run_config_editor()  # type: ignore[no-untyped-call]
        except ModuleNotFoundError:
            logger.error(
                "You need to install extra dependencies to use the editor, "
                "run `pip install ktoolbox[urwid]` "
                "or `pipx install ktoolbox[urwid] --force` if you are using pipx"
            )

    @staticmethod
    async def example_env() -> None:
        """Generate an example configuration ``.env`` file."""
        print(render(OutputFormat.DOTENV, class_path=("ktoolbox.configuration.Configuration",)))

    @staticmethod
    async def search_creator(
        name: str | None = None,
        id: str | None = None,
        service: str | None = None,
        *,
        dump: Path | None = None,
    ) -> object:
        """Search creators using one or more local filter values."""
        async with create_pawchive_client() as client:
            result = await search_creator_action(id=id, name=name, service=service, client=client)
        if not result:
            return result.message
        creators = list(result.data or ())
        if dump:
            await dump_search(creators, dump)
        return creators or TextEnum.SearchResultEmpty.value

    @staticmethod
    async def search_creator_post(
        id: str | None = None,
        name: str | None = None,
        service: str | None = None,
        q: str | None = None,
        o: int | None = None,
        *,
        dump: Path | None = None,
    ) -> object:
        """Search posts for creators selected by ID, name, or service."""
        async with create_pawchive_client() as client:
            result = await search_creator_post_action(
                id=id,
                name=name,
                service=service,
                q=q,
                o=o,
                client=client,
            )
        if not result:
            return result.message
        posts = result.data or []
        if dump:
            await dump_search(posts, dump)
        return posts or TextEnum.SearchResultEmpty.value

    @staticmethod
    async def get_post(
        service: str,
        creator_id: str,
        post_id: str,
        revision_id: str | None = None,
        *,
        dump: Path | None = None,
    ) -> object:
        """Get one post or select one revision from its revision list."""
        try:
            async with create_pawchive_client() as client:
                post = await _requested_post(client, service, creator_id, post_id, revision_id)
        except (PawchiveError, ValidationError, LookupError) as error:
            return _error_message(error)
        if dump:
            await _dump_model(post, dump)
        return post

    @staticmethod
    async def download_post(
        url: str | None = None,
        service: str | None = None,
        creator_id: str | None = None,
        post_id: str | None = None,
        revision_id: str | None = None,
        path: Path | str = Path("."),
        *,
        dump_post_data: bool = True,
    ) -> str | None:
        """Download one post, one selected revision, or a post with all revisions."""
        await KToolBoxCli._ensure_update_check()
        if url:
            service, creator_id, post_id, parsed_revision = parse_webpage_url(url)
            revision_id = parsed_revision or revision_id
        if not all((service, creator_id, post_id)):
            return str(
                generate_msg(
                    TextEnum.MissingParams.value,
                    use_at_lease_one=[["url"], ["service", "creator_id", "post_id"]],
                )
            )

        assert service is not None and creator_id is not None and post_id is not None
        output_path = path if isinstance(path, Path) else Path(path)

        try:
            async with create_pawchive_client() as client:
                post = await _requested_post(client, service, creator_id, post_id, revision_id)
                post_path = output_path / generate_post_path_name(post)
                if revision_id:
                    post_path = post_path / config.job.post_structure.revisions / str(revision_id)

                jobs = await create_job_from_post(
                    post,
                    post_path,
                    dump_post_data=dump_post_data,
                    client=client,
                )

                if config.job.include_revisions and revision_id is None:
                    try:
                        revisions = await client.list_post_revisions(service, creator_id, post_id)
                    except PawchiveNotFoundError:
                        revisions = []
                    for revision in revisions:
                        revision_path = (
                            post_path / config.job.post_structure.revisions / generate_post_path_name(revision)
                        )
                        jobs.extend(
                            await create_job_from_post(
                                revision,
                                revision_path,
                                dump_post_data=dump_post_data,
                                client=client,
                            )
                        )
        except (FetchInterruptError, PawchiveError, ValidationError, LookupError) as error:
            cause = error.error if isinstance(error, FetchInterruptError) else error
            return _error_message(cause)

        await JobRunner(job_list=jobs).start()
        return None

    @staticmethod
    async def sync_creator(
        url: str | None = None,
        service: str | None = None,
        creator_id: str | None = None,
        path: Path | str = Path("."),
        *,
        save_creator_indices: bool = False,
        mix_posts: bool | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        offset: int = 0,
        length: int | None = None,
        keywords: tuple[str, ...] | str | None = None,
        keywords_exclude: tuple[str, ...] | str | None = None,
    ) -> str | None:
        """Synchronize a bounded range or every available post for one creator."""
        await KToolBoxCli._ensure_update_check()
        if url:
            service, creator_id, _, _ = parse_webpage_url(url)
        if not all((service, creator_id)):
            return str(
                generate_msg(
                    TextEnum.MissingParams.value,
                    use_at_lease_one=[["url"], ["service", "creator_id"]],
                )
            )

        assert service is not None and creator_id is not None
        output_path = path if isinstance(path, Path) else Path(path)
        keyword_values = (keywords,) if isinstance(keywords, str) else keywords
        excluded_keyword_values = (keywords_exclude,) if isinstance(keywords_exclude, str) else keywords_exclude
        keyword_set = set(keyword_values) if keyword_values else config.job.keywords
        excluded_keyword_set = set(excluded_keyword_values) if excluded_keyword_values else config.job.keywords_exclude

        try:
            async with create_pawchive_client() as client:
                profile = await client.get_creator_profile(service, creator_id)
                creator_path = output_path / sanitize_filename(profile.name or creator_id)
                creator_path.mkdir(parents=True, exist_ok=True)

                result = await create_job_from_creator(
                    service,
                    creator_id,
                    creator_path,
                    all_pages=length is None,
                    offset=offset,
                    length=length,
                    save_creator_indices=save_creator_indices,
                    mix_posts=mix_posts,
                    start_time=datetime.strptime(start_time, "%Y-%m-%d") if start_time else None,
                    end_time=datetime.strptime(end_time, "%Y-%m-%d") if end_time else None,
                    keywords=keyword_set,
                    keywords_exclude=excluded_keyword_set,
                    client=client,
                )
        except (PawchiveError, ValidationError, ValueError) as error:
            return _error_message(error)

        if not result:
            return result.message
        await JobRunner(job_list=result.data or []).start()
        return None
