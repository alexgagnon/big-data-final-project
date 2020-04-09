from templates import updateTemplates
import argparse
import logging
import config

logging.basicConfig()
log = logging.getLogger("logger")


def init_parser() -> argparse.ArgumentParser:
    """
    Returns a parser for the cli arguments
    """

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]...",
        description="Answer a question from a knowledge graph",
        allow_abbrev=False
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{parser.prog} version 1.0.0"
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="runs in debug mode",
        action="store_true",
        default=config.DEBUG
    )
    parser.add_argument(
        "-u",
        "--update",
        help="updates the cache of prebuilt templates",
        action="store_true",
        default=config.UPDATE
    )
    return parser


def main() -> None:
    parser = init_parser()
    args = parser.parse_args()
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    config.DEBUG = args.debug

    if args.update:
        updateTemplates()


if __name__ == "__main__":
    main()
