from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Any, List, Tuple, Dict
from http.client import HTTPResponse
from utils import generate_question, get_all_properties, get_answer
import json
import pickle
import argparse
import logging
import config

logging.basicConfig(format='%(message)s')
log = logging.getLogger("logger")

sparql = SPARQLWrapper('http://dbpedia.org/sparql', returnFormat=JSON)

filename = 'elements'

types = [
    ['string', ['string']],
    ['boolean', ['boolean']],
    ['integer', ['integer', 'long']],
    ['decimal', ['float', 'double']],
    ['datetime', ['datetime', 'date', 'time', 'gYear']],
]

keywords = {
    'string': [],
    'boolean': [],
    'integer': [],
    'decimal': [],
    'datetime': []
}

question_prefixes = ['who', 'what', 'where', 'when', 'why', 'how']
yes_no_prefixes = [
    'do', 'don\'t',
    'does', 'doesn\'t',
    'did', 'didn\'t',
    'should', 'shouldn\'t',
    'can', 'can\'t',
    'could', 'couldn\'t',
    'has', 'hasn\'t',
    'have', 'haven\'t',
    'are', 'aren\'t',
    'was', 'wasn\'t',
    'will', 'won\'t',
    'would', 'wouldn\'t',
    'is', 'isn\'t'
]

superlatives = ['first', 'last', 'most', 'least', 'largest', 'smallest', 'tallest', 'shortest', 'earliest',
                'latest', 'deepest', 'shallowest', 'fastest', 'slowest', 'fattest', 'thinnest', 'greatest', 'best', 'worst', 'nearest', 'furthest', 'farthest']


def save_to_file(
    obj: Any,
    as_json=True,
    as_pickle=False,
    filename=None
) -> None:
    if filename == None:
        log.error('Need to provide a filename')
        return

    if as_pickle:
        with open(f"{filename}.pkl", "wb") as f:
            pickle.dump(obj, f)

    if as_json:
        with open(f"{filename}.json", "w", encoding="utf8") as f:
            json.dump(obj, f, ensure_ascii=False)

    log.info('Saved to file')


def process_results(results, key) -> List[Tuple[str, str]]:
    return [(x["label"]['value'], x[key]['value']) for x in results]


def generate_questions(elements) -> List[Tuple[str, str]]:
    questions = []

    for subtype, predicates in elements['predicates'].items():
        if config.DEBUG and subtype != 'string':
            log.debug(f'{subtype}: skipping in debug')
            continue
        for (predicate, uri) in predicates:
            questions.append(
                (f"who ??v?? ??s?? {predicate}", "select * where { ?s ?p ?o } limit 1"))

    return questions


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


def update() -> None:
    """
    Updates the templates by querying the store and saving them to file
    """

    predicates = get_all_properties()
    save_to_file(predicates, filename='properties')
    # generate_questions_from_predicates()


def has_cache():
    """
    Checks if a local copy of the templates exist
    """
    log.debug('TODO')
    return True


def main():
    parser = init_parser()
    args = parser.parse_args()
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    config.DEBUG = args.debug
    config.UPDATE = args.update
    config.BENCHMARK = args.benchmark

    log.debug(f'Started in DEBUG mode')

    if args.update or not has_cache():
        log.info('Updating templates')
        update()
    else:
        log.debug('Loading templates from cache')

    # elements = init_elements(update=args.update)
    # print(generate_questions(elements))

    if args.benchmark and (args.question or args.prompt):
        log.error('Cannot ask question and run benchmarks at the same time')
        exit(-1)

    elif args.benchmark:
        log.info('Running benchmarks...')
        log.info('TODO')

    elif args.question:
        answer = get_answer(args.question)
        log.info(answer)

    elif args.prompt:
        while True:
            question = input("What's your question?\n")
            answer = get_answer(question)
            log.info(answer)
            log.info('\n')

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
