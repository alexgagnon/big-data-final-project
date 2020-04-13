import os
import sys
import cli
import config
import logging
import argparse
import pickle
import json
from templates import generate_templates_from_properties
from utils import get_all_properties, get_answer
from http.client import HTTPResponse
from typing import Any, List, Literal, Tuple, Dict, Union
from SPARQLWrapper import SPARQLWrapper, JSON


logging.basicConfig(format='%(message)s')
log = logging.getLogger("logger")
log.info('Loaded imports...')

sparql = SPARQLWrapper('http://dbpedia.org/sparql', returnFormat=JSON)

types = [
    ['string', ['string']],
    ['boolean', ['boolean']],
    ['integer', ['integer', 'long']],
    ['decimal', ['float', 'double']],
    ['datetime', ['datetime', 'date', 'time', 'gYear']],
]

question_prefixes = ['who', 'what', 'where', 'when']


def save_to_file(
    obj: Any,
    as_json=True,
    as_pickle=False,
    filename=None
) -> None:
    if filename == None:
        log.error('Must provide filename! (NOTE: this is a developer error!')
        sys.exit(-1)

    if not (as_json or as_pickle):
        log.error('Must provide a file type (json or pickle)')
        sys.exit(-1)

    if as_pickle:
        with open(f"{filename}.pkl", "wb") as f:
            pickle.dump(obj, f)

    if as_json:
        with open(f"{filename}.json", "w", encoding="utf8") as f:
            json.dump(obj, f, ensure_ascii=False)

    log.info(f'Saved to file "{filename}.(json|pkl)"')


def load_properties_from_cache(ext: Union[Literal['json'], Literal['pkl']] = 'json', filename=config.PROPERTIES_FILENAME) -> Dict:
    properties = {}
    try:
        with open(f'{filename}.{ext}') as f:
            if ext == 'json':
                properties = json.load(f)
            else:
                properties = pickle.load(f)
    except:
        log.error(f'Could not load templates from {filename}.(json|pkl)')
        sys.exit(-1)

    return properties


def load_templates_from_cache(ext: Union[Literal['json'], Literal['pkl']] = 'json', filename=config.TEMPLATES_FILENAME) -> List:
    templates = []
    try:
        with open(f'{filename}.{ext}') as f:
            if ext == 'json':
                templates = json.load(f)
            else:
                templates = pickle.load(f)
    except:
        log.error(f'Could not load templates from {filename}.(json|pkl)')
        sys.exit(-1)

    return templates


def process_results(results, key) -> List[Tuple[str, str]]:
    return [(x["label"]['value'], x[key]['value']) for x in results]


def update() -> None:
    """
    Updates the templates by querying the store and saving them to file
    """

    # TODO: split this into redownload vs regenerate templates
    properties = get_all_properties()
    save_to_file(properties, filename=config.PROPERTIES_FILENAME)

    return properties


def has_properties_cache(filename=config.PROPERTIES_FILENAME):
    """
    Checks if a local copy of the templates exist
    """
    return os.path.exists(f'{filename}.json') or os.path.exists(f'{filename}.pkl')


def has_templates_cache(filename=config.TEMPLATES_FILENAME):
    """
    Checks if a local copy of the templates exist
    """
    return os.path.exists(f'{filename}.json') or os.path.exists(f'{filename}.pkl')


def main():
    parser = cli.init_parser()
    args = parser.parse_args()
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    config.DEBUG = args.debug
    config.UPDATE = args.properties or args.update
    config.BENCHMARK = args.benchmark
    config.SIMILARITY_METRIC = args.similarity
    config.THRESHOLD = args.threshold

    log.debug(f'Started in DEBUG mode')

    properties = None
    templates = []

    if args.properties or (args.update and not has_properties_cache()):
        log.info('Updating properties')
        properties = update()

    if args.update or not has_templates_cache():
        log.info('Regenerating templates from cached properties')
        if properties == None:
            properties = load_properties_from_cache()
        templates = generate_templates_from_properties(properties)
        save_to_file(templates, filename=config.TEMPLATES_FILENAME)
    else:
        log.debug('Loading templates from cache')
        templates = load_templates_from_cache()

    if args.benchmark and args.question:
        log.error('Cannot ask question and run benchmarks at the same time')
        sys.exit(-1)

    elif args.benchmark:
        log.info('Running benchmarks...')
        log.info('TODO')

    elif args.question:
        answer = get_answer(args.question, templates)
        log.info(answer)

    else:
        while True:
            try:
                question = input("Ask a question:\n")
                answer = get_answer(question, templates)
                log.info(answer)
            except KeyboardInterrupt:
                log.info('\nExiting')
                sys.exit()


if __name__ == "__main__":
    main()
