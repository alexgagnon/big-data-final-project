from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Any, List, Tuple, Dict
from http.client import HTTPResponse
from utils import generate_question, get_all_properties, get_answer
import json
import pickle
import argparse
import logging
import config
import cli
import sys
import os

logging.basicConfig(format='%(message)s')
log = logging.getLogger("logger")

sparql = SPARQLWrapper('http://dbpedia.org/sparql', returnFormat=JSON)

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


def save_to_file(
    obj: Any,
    as_json=True,
    as_pickle=False,
    filename=config.FILENAME
) -> None:
    if as_pickle:
        with open(f"{filename}.pkl", "wb") as f:
            pickle.dump(obj, f)

    if as_json:
        with open(f"{filename}.json", "w", encoding="utf8") as f:
            json.dump(obj, f, ensure_ascii=False)

    log.info('Saved to file')


def process_results(results, key) -> List[Tuple[str, str]]:
    return [(x["label"]['value'], x[key]['value']) for x in results]


def generate_templates_from_properties(properties) -> List[Tuple[str, str]]:
    questions = []

    # for subtype, predicates in elements['predicates'].items():
    #     if config.DEBUG and subtype != 'string':
    #         log.debug(f'{subtype}: skipping in debug')
    #         continue
    #     for (predicate, uri) in predicates:
    #         questions.append(
    #             (f"who ??v?? ??s?? {predicate}", "select * where { ?s ?p ?o } limit 1"))

    return questions


def update() -> None:
    """
    Updates the templates by querying the store and saving them to file
    """

    properties = get_all_properties()
    save_to_file(properties)
    generate_templates_from_properties(properties)


def has_cache(filename=config.FILENAME):
    """
    Checks if a local copy of the templates exist
    """
    return os.path.exists(f'{filename}.json') or os.path.exists(f'{filename}.pkl')


def main():
    parser = cli.init_parser()
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

    templates = [(
        'What year was {s} born in', 'select ?result {<http://dbpedia.org/resource/J._K._Rowling> dbo:birthDate ?result}')]

    if args.benchmark and (args.question or args.prompt):
        log.error('Cannot ask question and run benchmarks at the same time')
        sys.exit(-1)

    elif args.benchmark:
        log.info('Running benchmarks...')
        log.info('TODO')

    elif args.question:
        answer = get_answer(args.question, templates)
        log.info(answer)

    elif args.prompt:
        while True:
            try:
                log.info('\n')
                question = input("Ask a question:\n")
                answer = get_answer(question, templates)
                log.info(answer)
            except KeyboardInterrupt:
                log.info('\nExiting')
                sys.exit()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
