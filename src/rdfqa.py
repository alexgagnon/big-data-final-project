from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Any, List, Tuple, Dict
from http.client import HTTPResponse
from utils import generate_question, get_answer
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


def check_invalid_query(response: HTTPResponse) -> bool:
    return is_incomplete_query(response) or is_partial_query(response)


def is_incomplete_query(response: HTTPResponse) -> bool:
    incomplete = response.getheader('X-SPARQL-MaxRows') != None
    if incomplete:
        log.warn('Query response too large!')
    return response.getheader('X-SPARQL-MaxRows') != None


def is_partial_query(response: HTTPResponse) -> bool:
    partial = response.getheader('X-SQL-State') != None
    if partial:
        log.warn('Partial response!')
    return partial


def save_to_file(
    obj: Any,
    as_json=True,
    as_pickle=False,
    filename=filename
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


def load_predicates_and_types():
    elements = {
        'predicates': get_all_predicates(),
        'types': {}
    }

    save_to_file(elements)

    return elements


def get_all_predicates():
    key = "predicate"
    predicates = {}
    for name, subtypes in types:
        if name not in predicates:
            predicates[name] = []

        for subtype in subtypes:
            query = f"""select distinct ?{key} ?label where {{
                            ?{key} a owl:DatatypeProperty ;
                              rdfs:range xsd:{subtype} ;
                              rdfs:label ?label
                            filter langMatches( lang(?label), "EN" )
                      }}"""
            sparql.setQuery(query)
            results = sparql.query()
            bindings = results.convert()['results']['bindings']
            check_invalid_query(results.response)
            predicates[name].extend(process_results(bindings, key))

        # Sets can't be output as JSON
        predicates[name] = list(predicates[name])

    return predicates


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
        "-b",
        "--benchmark",
        help="runs benchmark tests",
        action="store_true",
        default=config.BENCHMARK
    )
    return parser


def init_elements(update: bool) -> Dict:
    elements = {}
    source = 'Loading from: '

    if (update):
        log.info('Updating from DB')
        elements = load_predicates_and_types()

    else:
        try:
            with open(f'{filename}.json') as f:
                elements = json.load(f)
                source += f.name
        except:
            try:
                with open(f'{filename}.pkl') as f:
                    elements = pickle.load(f)
                    source += f.name

            except:
                elements = load_predicates_and_types()
                source = 'No local copy, pulling from DB'

        log.info(source)

    return elements


def main():
    parser = init_parser()
    args = parser.parse_args()
    log.setLevel(logging.DEBUG if args.debug else logging.WARN)
    config.DEBUG = args.debug
    config.UPDATE = args.update
    config.BENCHMARK = args.benchmark

    log.debug(f'Running in DEBUG mode')

    # elements = init_elements(update=args.update)
    # print(generate_questions(elements))

    while True:
        question = input("What's your question?\n")
        answer = get_answer(question)
        print(answer)
        print()


if __name__ == "__main__":
    main()
