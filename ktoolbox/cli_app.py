from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from ktoolbox import __version__
from ktoolbox.cli import KToolBoxCli

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
    creator: str | None = None,
    *,
    service: str | None = None,
    creator_id: str | None = None,
    output: Annotated[Path, Parameter(name=("--output", "-o", "--path"))] = Path("."),
    save_creator_indices: bool = False,
    mix_posts: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    offset: int = 0,
    length: int | None = None,
    keywords: tuple[str, ...] | None = None,
    keywords_exclude: tuple[str, ...] | None = None,
) -> int:
    """Synchronize posts from one creator."""
    return _print_result(
        await KToolBoxCli.sync_creator(
            url=creator,
            service=service,
            creator_id=creator_id,
            path=output,
            save_creator_indices=save_creator_indices,
            mix_posts=mix_posts,
            start_time=start_time,
            end_time=end_time,
            offset=offset,
            length=length,
            keywords=keywords,
            keywords_exclude=keywords_exclude,
        )
    )


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
async def config_edit() -> int:
    """Open the optional terminal configuration editor."""
    await KToolBoxCli.config_editor()
    return 0


@config_app.command(name="example")
async def config_example() -> int:
    """Print an example dotenv configuration."""
    await KToolBoxCli.example_env()
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
