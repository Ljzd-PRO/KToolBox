import fire
from loguru import logger

from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import logger_init, uvloop_init


def main():
    try:
        logger_init(cli_use=True)
        uvloop_init()
        fire.Fire(KToolBoxCli)
    except KeyboardInterrupt:
        logger.error("KToolBox was interrupted by the user")


if __name__ == "__main__":
    main()
