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
        "-p",
        "--properties",
        help="updates the cache of properties in a knowledge base",
        action="store_true",
        default=config.UPDATE
    )
    parser.add_argument(
        "-t",
        "--templates",
        help='update the templates',
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
        "-b",
        "--benchmark",
        help="runs benchmark tests",
        action="store_true",
        default=config.BENCHMARK
    )
    parser.add_argument(
        '-m',
        '--metric',
        help='define the similarity metric used',
        choices=['nlp', 'ld'],
        action='store',
        default=config.SIMILARITY_METRIC
    )
    parser.add_argument(
        '-s',
        '--similarity',
        help='set the similarity threshold',
        action='store',
        type=float,
        default=config.THRESHOLD
    )
    parser.add_argument(
        '-w',
        '--word',
        help='define size of word embeddings vector (NOTE: must have installed the matching spacy file',
        choices=['md', 'lg'],
        action='store',
        default=config.WORD_EMBEDDINGS_SIZE
    )
    parser.add_argument(
        '-f',
        '--figures',
        help='generate figures',
        action='store_true',
        default=config.FIGURES
    )
    parser.add_argument(
        '-l',
        '--log',
        help='output logs to file',
        action='store',
        default=config.LOG
    )
    parser.add_argument(
        '-a',
        '--ask',
        help='ask a question through the CLI',
        action='store',
        default=config.PROMPT_AS_DEFAULT
    )
    return parser
