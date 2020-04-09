from SPARQLWrapper import SPARQLWrapper2
from typing import Any, List, Literal, Set, Union
import json
import pickle

sparql = SPARQLWrapper2("http://dbpedia.org/sparql")

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

verbs = {
    'to_do': ['do', 'does', 'did', 'will do'],
    'to_be': ['am', 'is', 'was', 'will be'],
    'to_have': ['have', 'has', 'had', 'will have']
}

superlatives = ['first', 'last', 'most', 'least', 'largest', 'smallest', 'tallest', 'shortest', 'earliest',
                'latest', 'deepest', 'shallowest', 'fastest', 'slowest', 'fattest', 'thinnest', 'greatest', 'best', 'worst', 'nearest', 'furthest', 'farthest']


def save_to_file(obj: Any, as_json=True, as_pickle=False, filename=filename) -> None:
    if as_pickle:
        with open(f"{filename}.pkl", "wb") as f:
            pickle.dump(obj, f)

    if as_json:
        with open(f"{filename}.json", "w", encoding="utf8") as f:
            json.dump(obj, f, ensure_ascii=False)


def process_results(results: SPARQLWrapper2.query, key) -> List:
    return [x["label"].value
            for x in results.bindings]


elements = {
    'predicates': {},
    'types': {}
}


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
            predicates[name] = set()

        for subtype in subtypes:
            query = f"""select ?{key} ?label where {{
                            ?{key} a owl:DatatypeProperty ;
                              rdfs:range xsd:{subtype} ;
                              rdfs:label ?label
                            filter langMatches( lang(?label), "EN" )
                      }}"""
            sparql.setQuery(query)
            results = sparql.query()
            predicates[name].update(process_results(results, key))

        # Sets can't be output as JSON
        predicates[name] = list(predicates[name])

    return predicates


def generate_questions(elements) -> Set[str]:
    questions = set()

    for subtype in elements['predicates'].items():
        for boolean_predicates in subtype['boolean']:
            print(boolean_predicates)
        # questions.add(f"has {boolean_predicate} happened")
        # questions.add(f"will {boolean_predicate} happen")
        # questions.add(f"is {boolean_predicate} happening")
        # questions.add(f"did {boolean_predicate} happen")

    return questions


elements = {}
source = 'Loading from: '
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
        source += 'new copy'

print(source)
print(list(generate_questions(elements)))
