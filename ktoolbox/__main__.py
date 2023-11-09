import logging

import fire

from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import logger_init

if __name__ == "__main__":
    logger_init(std_level=logging.WARNING)
    fire.Fire(KToolBoxCli)
