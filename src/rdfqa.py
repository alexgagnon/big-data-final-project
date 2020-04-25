import os
import sys
import cli
import config
import logging
import pickle
import json
from pytictoc import TicToc
from templates import generate_templates_from_properties
from properties import get_all_properties, get_filtered_properties
from benchmark import run_benchmark
from utils import get_answer
from typing import Any, List, Literal, Tuple, Dict, Union
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

logging.basicConfig(format='%(message)s')
log = logging.getLogger("logger")
log.info('Loaded imports...')

timer = TicToc()

sparql = SPARQLWrapper('http://dbpedia.org/sparql', returnFormat=JSON)


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
    config.UPDATE = args.properties or args.templates
    config.BENCHMARK = args.benchmark
    config.SIMILARITY_METRIC = args.metric
    config.THRESHOLD = args.similarity
    config.FIGURES = args.figures

    log.debug(f'Started in DEBUG mode')
    log.info('Hit CTRL+D to exit')

    properties = None
    filtered_properties = None
    templates = []

    # update properties if asked or if we're trying to update templates without a properties.json file
    if args.properties or (args.templates and not has_properties_cache()):
        log.info('Updating properties')
        timer.tic()
        properties = update()
        log.info(f'Cached properties in: {timer.tocvalue()}')

    if args.templates or not has_templates_cache():
        log.info('Regenerating templates from cached properties')
        timer.tic()
        if properties == None:
            properties = load_properties_from_cache()

        total_properties = 0
        for property_type in properties:
            total_properties += len(properties[property_type])
        log.info(
            f'{len(properties.keys())} property types with {total_properties} total properties found')

        filtered_properties = get_filtered_properties(properties)

        templates = generate_templates_from_properties(filtered_properties)
        log.info(f'Generated {len(templates)} question templates')
        save_to_file(templates, filename=config.TEMPLATES_FILENAME)
        log.info(f'Templates created in: {timer.tocvalue()}')
    else:
        log.debug('Loading templates from cache')
        templates = load_templates_from_cache()

    if args.benchmark and args.question:
        log.error('Cannot ask question and run benchmarks at the same time')
        sys.exit(-1)

    if args.log or args.benchmark:
        now = datetime.now()
        current_time = now.strftime("%Y:%m:%d-%H:%M:%S")
        log_file = logging.FileHandler(
            f'results/{current_time}-benchmarks.log')
        log.addHandler(log_file)

    log.info(f'Loaded {len(templates)} templates')
    log.info(
        f"Using '{config.SIMILARITY_METRIC}' as similarity metric, with threshold of {config.THRESHOLD}")

    if args.benchmark:
        log.info('Running benchmarks...')

        run_benchmark(templates)

    elif args.question:
        answer = get_answer(args.question, templates)
        log.info(answer)

    else:
        while True:
            try:
                question = input("Ask a question:\n")
                if question == '':
                    continue
                answer = get_answer(question, templates)
                log.info(answer)
                log.info('')
            except KeyboardInterrupt as interrupt:
                log.info('')
                continue
            except EOFError:
                log.info('\nExiting\n')
                sys.exit(0)


if __name__ == "__main__":
    main()
