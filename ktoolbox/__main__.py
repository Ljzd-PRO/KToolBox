import sys
import fire
from loguru import logger

from ktoolbox import __version__
from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import logger_init, uvloop_init


def main():
    try:
        # Handle -v flag before Fire takes over
        if len(sys.argv) > 1 and sys.argv[1] in ['-v', '--version']:
            print(__version__)
            return
            
        logger_init(cli_use=True)
        uvloop_init()
        fire.Fire(KToolBoxCli)
    except KeyboardInterrupt:
        logger.error("KToolBox was interrupted by the user")


if __name__ == "__main__":
    main()
