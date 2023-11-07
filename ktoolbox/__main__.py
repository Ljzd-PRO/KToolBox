import fire

from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import logger_init

if __name__ == "__main__":
    logger_init()
    fire.Fire(KToolBoxCli)
