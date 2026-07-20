from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ktoolbox import __version__
from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.utils import create_pawchive_client
from ktoolbox.blocker import BlockerEngine
from ktoolbox.cli import KToolBoxCli
from ktoolbox.configuration import config as runtime_config
from ktoolbox.project_config import (
    CreatorReference,
    ProjectConfigError,
    ProjectConfigStore,
    parse_creator_reference,
)
from ktoolbox.sync import SyncCoordinator, SyncOptions, SyncSummary, resolve_sync_targets

stdout = Console()
stderr = Console(stderr=True)

app = App(
    name="ktoolbox",
    help="Download and synchronize public Pawchive posts.",
    version=__version__,
    help_format="rich",
    help_on_error=True,
    exit_on_error=False,
    result_action="return_int_as_exit_code_else_zero",
    console=stdout,
    error_console=stderr,
)
creator_app = App(name="creator", help="Manage and search creators.")
post_app = App(name="post", help="Inspect and search posts.")
config_app = App(name="config", help="Inspect and edit KToolBox configuration.")
app.command(creator_app)
app.command(post_app)
app.command(config_app)
app.register_install_completion_command()


def _print_result(result: object) -> int:
    if result is not None:
        stdout.print(result)
    return 0


def _project_store(path: Path | None) -> ProjectConfigStore:
    return ProjectConfigStore(path)


def _project_error(error: ProjectConfigError) -> int:
    stderr.print(f"[red]Configuration error:[/red] {error}")
    return 2


def _print_sync_summary(summary: SyncSummary) -> None:
    table = Table(title="Synchronization summary")
    table.add_column("Creator")
    table.add_column("Posts", justify="right")
    table.add_column("Excluded", justify="right")
    table.add_column("Jobs", justify="right")
    table.add_column("Status")
    for result in summary.creators:
        generation = result.generation
        table.add_row(
            Text(result.creator.key),
            str(generation.accepted_posts if generation else 0),
            str(sum(generation.blocked_by.values()) if generation else 0),
            str(generation.generated_jobs if generation else 0),
            Text(
                "completed" if result.successful else result.error or "failed",
                style="green" if result.successful else "red",
            ),
        )
    table.caption = (
        f"Files: {summary.downloads.completed} downloaded, {summary.downloads.existed} existing, "
        f"{summary.downloads.failed} failed"
    )
    stdout.print(table)


@app.command
async def download(
    post: str | None = None,
    *,
    service: str | None = None,
    creator_id: str | None = None,
    post_id: str | None = None,
    revision_id: str | None = None,
    output: Annotated[Path, Parameter(name=("--output", "-o", "--path"))] = Path("."),
    dump_post_data: bool = True,
) -> int:
    """Download one post or revision."""
    return _print_result(
        await KToolBoxCli.download_post(
            url=post,
            service=service,
            creator_id=creator_id,
            post_id=post_id,
            revision_id=revision_id,
            path=output,
            dump_post_data=dump_post_data,
        )
    )


@app.command
async def sync(
    *creators: str,
    service: str | None = None,
    creator_id: str | None = None,
    output: Annotated[Path, Parameter(name=("--output", "-o", "--path"))] = Path("."),
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
    save_creator_indices: bool = False,
    mix_posts: bool | None = None,
    start_time: Annotated[str | None, Parameter(name=("--start-time", "--start"))] = None,
    end_time: Annotated[str | None, Parameter(name=("--end-time", "--end"))] = None,
    offset: int = 0,
    length: int | None = None,
    keywords: tuple[str, ...] | None = None,
    keywords_exclude: tuple[str, ...] | None = None,
) -> int:
    """Synchronize one or more creators, or every enabled roster creator."""
    targets = list(creators)
    if service or creator_id:
        if not service or not creator_id:
            return _project_error(ProjectConfigError("--service and --creator-id must be used together"))
        targets.append(f"{service}:{creator_id}")

    store = _project_store(config_path)
    try:
        project = store.load()
        selected_creators = resolve_sync_targets(targets, project)
        options = SyncOptions(
            output=output,
            save_creator_indices=save_creator_indices,
            mix_posts=mix_posts,
            start_time=datetime.strptime(start_time, "%Y-%m-%d") if start_time else None,
            end_time=datetime.strptime(end_time, "%Y-%m-%d") if end_time else None,
            offset=offset,
            length=length,
            keywords=set(keywords) if keywords else set(runtime_config.job.keywords),
            keywords_exclude=(set(keywords_exclude) if keywords_exclude else set(runtime_config.job.keywords_exclude)),
        )
        engine = BlockerEngine.from_specs(project.blockers)
    except (ProjectConfigError, ValueError) as error:
        return _project_error(ProjectConfigError(str(error)))

    try:
        async with create_pawchive_client() as client:
            summary = await SyncCoordinator(
                client,
                blocker_engine=engine,
                creator_concurrency=runtime_config.job.creator_concurrency,
            ).run(selected_creators, options)
    except PawchiveError as error:
        stderr.print(f"[red]Pawchive error:[/red] {error}")
        return 1
    _print_sync_summary(summary)
    return 0 if summary.successful else 1


@creator_app.command(name="search")
async def creator_search(
    name: str | None = None,
    creator_id: Annotated[str | None, Parameter(name=("--creator-id", "--id"))] = None,
    service: str | None = None,
    *,
    dump: Path | None = None,
) -> int:
    """Search Pawchive creators."""
    return _print_result(await KToolBoxCli.search_creator(name=name, id=creator_id, service=service, dump=dump))


@creator_app.command(name="list")
def creator_list(
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
    json_output: Annotated[bool, Parameter(name="--json")] = False,
) -> int:
    """List creators saved in the project roster."""
    store = _project_store(config_path)
    try:
        configuration = store.load()
    except ProjectConfigError as error:
        return _project_error(error)
    if json_output:
        stdout.print(json.dumps([item.model_dump() for item in configuration.creators], ensure_ascii=False))
        return 0
    if not configuration.creators:
        stdout.print(f"No creators are configured in {store.path}.")
        return 0
    table = Table(title=f"Creator roster: {store.path}")
    table.add_column("Creator")
    table.add_column("Alias")
    table.add_column("Status")
    for creator in configuration.creators:
        table.add_row(
            Text(creator.key),
            Text(creator.alias or ""),
            Text("enabled" if creator.enabled else "disabled", style="green" if creator.enabled else "dim"),
        )
    stdout.print(table)
    return 0


@creator_app.command(name="add")
def creator_add(
    target: str,
    *,
    alias: str | None = None,
    disabled: bool = False,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Add a Pawchive creator URL or service:id to the project roster."""
    store = _project_store(config_path)
    try:
        parsed = parse_creator_reference(target)
        creator = CreatorReference(
            service=parsed.service,
            creator_id=parsed.creator_id,
            alias=alias,
            enabled=not disabled,
        )
        store.add_creator(creator)
    except (ProjectConfigError, ValueError) as error:
        return _project_error(ProjectConfigError(str(error)))
    stdout.print(f"Added [bold]{creator.key}[/bold] to {store.path}.")
    return 0


@creator_app.command(name="remove")
def creator_remove(
    target: str,
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Remove a creator from the project roster."""
    store = _project_store(config_path)
    try:
        creator = store.remove_creator(target)
    except ProjectConfigError as error:
        return _project_error(error)
    stdout.print(f"Removed [bold]{creator.key}[/bold] from {store.path}.")
    return 0


def _set_creator_enabled(target: str, config_path: Path | None, enabled: bool) -> int:
    store = _project_store(config_path)
    try:
        creator = store.set_creator_enabled(target, enabled)
    except ProjectConfigError as error:
        return _project_error(error)
    state = "Enabled" if enabled else "Disabled"
    stdout.print(f"{state} [bold]{creator.key}[/bold].")
    return 0


@creator_app.command(name="enable")
def creator_enable(
    target: str,
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Enable a saved creator."""
    return _set_creator_enabled(target, config_path, True)


@creator_app.command(name="disable")
def creator_disable(
    target: str,
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Disable a saved creator."""
    return _set_creator_enabled(target, config_path, False)


@post_app.command(name="search")
async def post_search(
    creator_id: Annotated[str | None, Parameter(name=("--creator-id", "--id"))] = None,
    name: str | None = None,
    service: str | None = None,
    query: Annotated[str | None, Parameter(name=("--query", "-q"))] = None,
    offset: Annotated[int | None, Parameter(name=("--offset", "-o"))] = None,
    *,
    dump: Path | None = None,
) -> int:
    """Search posts for matching creators."""
    return _print_result(
        await KToolBoxCli.search_creator_post(
            id=creator_id,
            name=name,
            service=service,
            q=query,
            o=offset,
            dump=dump,
        )
    )


@post_app.command(name="show")
async def post_show(
    service: str,
    creator_id: str,
    post_id: str,
    revision_id: str | None = None,
    *,
    dump: Path | None = None,
) -> int:
    """Show one post or revision."""
    return _print_result(await KToolBoxCli.get_post(service, creator_id, post_id, revision_id=revision_id, dump=dump))


@config_app.command(name="edit")
async def config_edit(
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Open the optional terminal configuration editor."""
    await KToolBoxCli.config_editor(config_path)
    return 0


@config_app.command(name="example")
async def config_example() -> int:
    """Print an example dotenv configuration."""
    await KToolBoxCli.example_env()
    return 0


@config_app.command(name="validate")
def config_validate(
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Validate the project configuration file."""
    store = _project_store(config_path)
    try:
        configuration = store.load()
    except ProjectConfigError as error:
        return _project_error(error)
    stdout.print(f"[green]Valid configuration:[/green] {store.path} ({len(configuration.creators)} creators)")
    return 0


@config_app.command(name="path")
def config_path(
    *,
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
) -> int:
    """Print the resolved project configuration path."""
    stdout.print(_project_store(config_path).path)
    return 0


@app.command(name="site-version")
async def site_version() -> int:
    """Show the Pawchive application version."""
    return _print_result(await KToolBoxCli.site_version())


app.command(download, name="download-post", show=False)
app.command(sync, name="sync-creator", show=False)
app.command(creator_search, name="search-creator", show=False)
app.command(post_search, name="search-creator-post", show=False)
app.command(post_show, name="get-post", show=False)
app.command(config_edit, name="config-editor", show=False)
app.command(config_example, name="example-env", show=False)
