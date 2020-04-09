from SPARQLWrapper import SPARQLWrapper2
from typing import Any, List, Tuple
import json
import pickle

UPDATE = True

# Use SPARQLWrapper2 so we can do operations directly on the response
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

    print('Saved to file')


def process_results(results: SPARQLWrapper2.query, key) -> List[Tuple[str, str]]:
    return [(x["label"].value, x[key].value) for x in results.bindings]


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
            predicates[name].append(process_results(results, key))

        # Sets can't be output as JSON
        predicates[name] = list(predicates[name])

    return predicates


def generate_questions(elements) -> List[Tuple[str, str]]:
    questions = []

    for subtype, predicates in elements['predicates'].items():
        for predicate in predicates:
            if subtype == 'boolean':
                questions.append(
                    (predicate, "select * where { ?s ?p ?o } limit 1"))

    return questions


def main():
    elements = {}
    source = 'Loading from: '
    if (UPDATE):
        elements = load_predicates_and_types()
        source = 'Updating from DB'

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

    print(source)
    print(list(generate_questions(elements)))


if __name__ == "__main__":
    main()
