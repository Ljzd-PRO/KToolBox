import sys

from cyclopts.exceptions import CycloptsError
from loguru import logger
from pydantic import ValidationError
from pydantic_settings import SettingsError

from ktoolbox.cli_app import run_cli, stderr
from ktoolbox.exceptions import KToolBoxUserError
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


def _validation_error_message(error: ValidationError) -> str:
    details = []
    for item in error.errors(include_url=False, include_context=False, include_input=False)[:3]:
        path = ".".join(str(part) for part in item.get("loc", ())) or "configuration"
        details.append(f"{path}: {item.get('msg', 'invalid value')}")
    remaining = error.error_count() - len(details)
    suffix = f"; {remaining} more error(s)" if remaining > 0 else ""
    return "; ".join(details) + suffix


def main(argv: list[str] | None = None) -> int:
    tokens = sys.argv[1:] if argv is None else argv
    try:
        if not tokens:
            tokens = ["--help"]
        is_help_or_version = not tokens or any(token in {"-h", "--help", "--version"} for token in tokens)
        if not is_help_or_version:
            logger_init(
                cli_use=True,
                console=stderr,
                verbose="--verbose" in tokens,
                quiet="--quiet" in tokens,
            )
            uvloop_init()
            command = next((token for token in tokens if token in _LEGACY_COMMANDS), "")
            if replacement := _LEGACY_COMMANDS.get(command):
                logger.warning(f"`{command}` is deprecated; use `{replacement}` instead.")
        return run_cli(tokens)
    except CycloptsError:
        return 2
    except KToolBoxUserError as error:
        logger.error(f"{error.label}: {error}")
        return error.exit_code
    except ValidationError as error:
        logger.error(f"Configuration error: {_validation_error_message(error)}")
        return 2
    except SettingsError as error:
        logger.error(f"Configuration error: {error}")
        return 2
    except OSError as error:
        logger.error(f"System error: {error}")
        return 1
    except KeyboardInterrupt:
        logger.error("KToolBox was forcefully stopped by the user")
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
