import argparse
import config


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
    parser.add_argument(
        "-t",
        "--templates",
        help='update only the templates',
        action='store_true',
        default=False
    )
    parser.add_argument(
        "-q",
        "--question",
        help="provide a question you want answered",
        action="store",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        help="ask questions from the terminal",
        action="store_true",
        default=True
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        help="runs benchmark tests",
        action="store_true",
        default=config.BENCHMARK
    )
    return parser
