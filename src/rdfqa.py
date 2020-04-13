from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Any, List, Literal, Tuple, Dict, Union
from http.client import HTTPResponse
from utils import get_all_properties, get_answer
from templates import generate_templates_from_properties
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
    filename=None
) -> None:
    if filename == None:
        log.error('Must provide filename! (NOTE: this is a dev error!')
        sys.exit(-1)

    if not (as_json and as_pickle):
        return

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


def load_templates_from_cache(ext: Union[Literal['json'], Literal['pkl']] = 'json', filename=config.TEMPLATES_FILENAME) -> Dict:
    templates = {}
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
    config.UPDATE = args.update
    config.BENCHMARK = args.benchmark

    log.debug(f'Started in DEBUG mode')

    properties = None
    templates = {}

    if args.update or (args.templates and not has_properties_cache()):
        log.info('Updating properties')
        properties = update()

    if args.templates or not has_templates_cache():
        log.info('Regenerating templates from cached properties')
        if properties == None:
            properties = load_properties_from_cache()
        templates = generate_templates_from_properties(properties)
        save_to_file(templates, filename=config.TEMPLATES_FILENAME)
    else:
        log.debug('Loading templates from cache')
        templates = load_templates_from_cache()

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
