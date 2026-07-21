from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated

from cyclopts import App, Group, Parameter
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ktoolbox import __version__
from ktoolbox._enum import TextEnum
from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.generated import CreatorSummary, Post, Revision
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
from ktoolbox.reporting import ProgressReporter, create_progress_reporter
from ktoolbox.sync import SyncCoordinator, SyncOptions, SyncSummary, resolve_sync_targets

stdout = Console()
stderr = Console(stderr=True)


@dataclass(frozen=True, slots=True)
class CliRuntimeOptions:
    config_path: Path | None = None
    verbose: bool = False
    quiet: bool = False
    plain: bool = False
    no_color: bool = False


_DEFAULT_RUNTIME_OPTIONS = CliRuntimeOptions()
_runtime_options = ContextVar("ktoolbox_cli_runtime_options", default=_DEFAULT_RUNTIME_OPTIONS)

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
webui_app = App(name="webui", help="Run the local HeroUI management panel.")
app.command(creator_app)
app.command(post_app)
app.command(config_app)
app.command(webui_app)
app.register_install_completion_command()
app.meta.group_parameters = Group("Global options", sort_key=0)


def _print_json(value: object) -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    elif isinstance(value, list):
        value = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in value]
    stdout.print(json.dumps(value, ensure_ascii=False, indent=2), markup=False, highlight=False, soft_wrap=True)


def _command_error(label: str, message: str, *, code: int = 1) -> int:
    stderr.print(f"[red]{label}:[/red] {message}")
    return code


def _project_store(path: Path | None) -> ProjectConfigStore:
    return ProjectConfigStore(path or _runtime_options.get().config_path)


def _progress_reporter() -> ProgressReporter:
    options = _runtime_options.get()
    return create_progress_reporter(stderr, plain=options.plain, quiet=options.quiet)


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
    if post is None and not all((service, creator_id, post_id)):
        return _command_error(
            "Usage error",
            "provide a post URL or use --service, --creator-id, and --post-id together",
            code=2,
        )
    result = await KToolBoxCli.download_post(
        url=post,
        service=service,
        creator_id=creator_id,
        post_id=post_id,
        revision_id=revision_id,
        path=output,
        dump_post_data=dump_post_data,
        reporter=_progress_reporter(),
    )
    return _command_error("Download failed", result) if result else 0


@app.command
async def sync(
    *creators: str,
    service: str | None = None,
    creator_id: str | None = None,
    output: Annotated[Path, Parameter(name=("--output", "-o", "--path"))] = Path("."),
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

    store = _project_store(None)
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
                reporter=_progress_reporter(),
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
    json_output: Annotated[bool, Parameter(name="--json")] = False,
) -> int:
    """Search Pawchive creators."""
    result = await KToolBoxCli.search_creator(name=name, id=creator_id, service=service, dump=dump)
    if isinstance(result, str):
        if result == TextEnum.SearchResultEmpty.value:
            result = []
        else:
            return _command_error("Creator search failed", result)
    creators: list[CreatorSummary] = result
    if json_output:
        _print_json(creators)
        return 0
    if not creators:
        stdout.print("No creators found.")
        return 0
    table = Table(title="Creator search results")
    table.add_column("Service")
    table.add_column("Creator ID")
    table.add_column("Name")
    table.add_column("Updated")
    for creator in creators:
        table.add_row(
            str(creator.service),
            str(creator.id),
            str(creator.name),
            str(creator.updated),
        )
    stdout.print(table)
    return 0


@creator_app.command(name="list")
def creator_list(
    *,
    json_output: Annotated[bool, Parameter(name="--json")] = False,
) -> int:
    """List creators saved in the project roster."""
    store = _project_store(None)
    try:
        configuration = store.load()
    except ProjectConfigError as error:
        return _project_error(error)
    if json_output:
        _print_json(configuration.creators)
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
) -> int:
    """Add a Pawchive creator URL or service:id to the project roster."""
    store = _project_store(None)
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
) -> int:
    """Remove a creator from the project roster."""
    store = _project_store(None)
    try:
        creator = store.remove_creator(target)
    except ProjectConfigError as error:
        return _project_error(error)
    stdout.print(f"Removed [bold]{creator.key}[/bold] from {store.path}.")
    return 0


def _set_creator_enabled(target: str, enabled: bool) -> int:
    store = _project_store(None)
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
) -> int:
    """Enable a saved creator."""
    return _set_creator_enabled(target, True)


@creator_app.command(name="disable")
def creator_disable(
    target: str,
) -> int:
    """Disable a saved creator."""
    return _set_creator_enabled(target, False)


@post_app.command(name="search")
async def post_search(
    creator_id: Annotated[str | None, Parameter(name=("--creator-id", "--id"))] = None,
    name: str | None = None,
    service: str | None = None,
    query: Annotated[str | None, Parameter(name=("--query", "-q"))] = None,
    offset: Annotated[int | None, Parameter(name=("--offset", "-o"))] = None,
    *,
    dump: Path | None = None,
    json_output: Annotated[bool, Parameter(name="--json")] = False,
) -> int:
    """Search posts for matching creators."""
    result = await KToolBoxCli.search_creator_post(
        id=creator_id,
        name=name,
        service=service,
        q=query,
        o=offset,
        dump=dump,
    )
    if isinstance(result, str):
        if result == TextEnum.SearchResultEmpty.value:
            result = []
        else:
            return _command_error("Post search failed", result, code=2 if not any((creator_id, name, service)) else 1)
    posts: list[Post] = result
    if json_output:
        _print_json(posts)
        return 0
    if not posts:
        stdout.print("No posts found.")
        return 0
    table = Table(title="Post search results")
    table.add_column("Service")
    table.add_column("Creator ID")
    table.add_column("Post ID")
    table.add_column("Title", overflow="ellipsis")
    table.add_column("Published")
    for post in posts:
        table.add_row(
            str(post.service),
            str(post.user),
            str(post.id),
            str(post.title or ""),
            str(post.published or ""),
        )
    stdout.print(table)
    return 0


@post_app.command(name="show")
async def post_show(
    service: str,
    creator_id: str,
    post_id: str,
    revision_id: str | None = None,
    *,
    dump: Path | None = None,
    json_output: Annotated[bool, Parameter(name="--json")] = False,
) -> int:
    """Show one post or revision."""
    result = await KToolBoxCli.get_post(service, creator_id, post_id, revision_id=revision_id, dump=dump)
    if isinstance(result, str):
        return _command_error("Post lookup failed", str(result))
    post: Post | Revision = result
    if json_output:
        _print_json(post)
        return 0
    table = Table(title="Post details", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value", overflow="fold")
    table.add_row("Service", str(post.service))
    table.add_row("Creator ID", str(post.user))
    table.add_row("Post ID", str(post.id))
    table.add_row("Title", str(post.title or ""))
    table.add_row("Published", str(post.published or ""))
    table.add_row("Attachments", str(len(post.attachments or ())))
    stdout.print(table)
    return 0


@config_app.command(name="edit")
async def config_edit() -> int:
    """Open the optional terminal configuration editor."""
    await KToolBoxCli.config_editor(_project_store(None).path)
    return 0


@config_app.command(name="example")
async def config_example() -> int:
    """Print an example dotenv configuration."""
    await KToolBoxCli.example_env()
    return 0


@config_app.command(name="validate")
def config_validate() -> int:
    """Validate the project configuration file."""
    store = _project_store(None)
    try:
        configuration = store.load()
    except ProjectConfigError as error:
        return _project_error(error)
    stdout.print(f"[green]Valid configuration:[/green] {store.path} ({len(configuration.creators)} creators)")
    return 0


@config_app.command(name="path")
def config_path() -> int:
    """Print the resolved project configuration path."""
    stdout.print(str(_project_store(None).path), markup=False, highlight=False, soft_wrap=True)
    return 0


@app.command(name="site-version")
async def site_version() -> int:
    """Show the Pawchive application version."""
    try:
        async with create_pawchive_client() as client:
            version = await client.get_app_version()
    except PawchiveError as error:
        return _command_error("Pawchive error", str(error))
    stdout.print(version)
    return 0


@webui_app.default
async def webui_run(
    project_dir: Path = Path("."),
    *,
    host: str | None = None,
    port: int | None = None,
    no_open: bool = False,
) -> int:
    """Run the WebUI for one directory containing ktoolbox.toml."""
    try:
        from ktoolbox.webui.server import run_webui

        await run_webui(
            project_dir,
            host=host,
            port=port,
            open_browser=False if no_open else None,
        )
    except (RuntimeError, ValueError) as error:
        return _command_error("WebUI error", str(error), code=2)
    return 0


@webui_app.command(name="hash-password")
def webui_hash_password() -> int:
    """Generate an Argon2id password hash using hidden terminal input."""
    try:
        from ktoolbox.webui.server import generate_password_hash

        password_hash = generate_password_hash()
    except (RuntimeError, ValueError) as error:
        return _command_error("Password error", str(error), code=2)
    stdout.print(password_hash, markup=False, highlight=False)
    return 0


app.command(download, name="download-post", show=False)
app.command(sync, name="sync-creator", show=False)
app.command(creator_search, name="search-creator", show=False)
app.command(post_search, name="search-creator-post", show=False)
app.command(post_show, name="get-post", show=False)
app.command(config_edit, name="config-editor", show=False)
app.command(config_example, name="example-env", show=False)


@app.meta.default
async def launch(
    *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    config_path: Annotated[Path | None, Parameter(name="--config")] = None,
    verbose: Annotated[bool, Parameter(negative=())] = False,
    quiet: Annotated[bool, Parameter(negative=())] = False,
    plain: Annotated[bool, Parameter(negative=())] = False,
    no_color: Annotated[bool, Parameter(negative=())] = False,
) -> int:
    """Run KToolBox with global runtime options."""
    if verbose and quiet:
        return _command_error("Usage error", "--verbose and --quiet cannot be used together", code=2)

    runtime = CliRuntimeOptions(
        config_path=config_path,
        verbose=verbose,
        quiet=quiet,
        plain=plain,
        no_color=no_color,
    )
    context_token = _runtime_options.set(runtime)
    stdout_no_color = stdout.no_color
    stderr_no_color = stderr.no_color
    if no_color:
        stdout.no_color = True
        stderr.no_color = True
    try:
        if not tokens:
            tokens = ("--help",)
        return int(await app.run_async(tokens, result_action="return_int_as_exit_code_else_zero"))
    finally:
        stdout.no_color = stdout_no_color
        stderr.no_color = stderr_no_color
        _runtime_options.reset(context_token)


def run_cli(tokens: list[str]) -> int:
    return int(app.meta(tokens, result_action="return_int_as_exit_code_else_zero"))
