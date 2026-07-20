import sys

from cyclopts.exceptions import CycloptsError
from loguru import logger

from ktoolbox.cli_app import app
from ktoolbox.utils import logger_init, uvloop_init

_LEGACY_COMMANDS = {
    "config-editor": "config edit",
    "download-post": "download",
    "example-env": "config example",
    "get-post": "post show",
    "search-creator": "creator search",
    "search-creator-post": "post search",
    "sync-creator": "sync",
}


def main(argv: list[str] | None = None) -> int:
    tokens = sys.argv[1:] if argv is None else argv
    try:
        is_help_or_version = not tokens or any(token in {"-h", "--help", "--version"} for token in tokens)
        if not is_help_or_version:
            logger_init(cli_use=True)
            uvloop_init()
            if replacement := _LEGACY_COMMANDS.get(tokens[0]):
                logger.warning(f"`{tokens[0]}` is deprecated; use `{replacement}` instead.")
        return int(app(tokens, result_action="return_int_as_exit_code_else_zero"))
    except CycloptsError as error:
        app.error_console.print(error)
        return 2
    except KeyboardInterrupt:
        logger.error("KToolBox was interrupted by the user")
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
