import fire

from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import logger_init


def main():
    logger_init(cli_use=True)
    fire.Fire(KToolBoxCli)


if __name__ == "__main__":
    main()
