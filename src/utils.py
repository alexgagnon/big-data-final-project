import spacy
import logging
import config
from http.client import HTTPResponse
from typing import List, Tuple
from SPARQLWrapper import SPARQLWrapper, JSON

log = logging.getLogger("logger")

sparql = SPARQLWrapper(config.ENDPOINT, returnFormat=JSON)

sp = spacy.load('en_core_web_sm')


used_predicates = f"""
select distinct ?predicate ?label where {{
  ?subject ?predicate ?object .
  ?predicate rdfs:label ?label
}}
order by ?predicate
"""

declared_predicates = f"""
select ?p ?label {{
  {{
    select ?p {{
      ?p a rdf:Property
  }}
  union
  {{
    select ?p {{
      VALUES ?t {{
        owl:ObjectProperty owl:DatatypeProperty owl:AnnotationProperty
      }}
      ?p a ?t
    }} .
  ?p rdfs:label ?label .
  filter langMatches( lang(?label), "EN" )
}}
"""

prefixes = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wds: <http://www.wikidata.org/entity/statement/>
PREFIX wdv: <http://www.wikidata.org/value/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>
"""

question_templates = {
    "date": ['(when (did|will)|in what (year|month) did|on what day did) {o} (occur|happen)']
}


def generate_question(
    question: str = '{q}',
    helper_verb: str = '{h}',
    subject: str = '{s}',
    verb: str = '{v}',
    obj: str = '{o}'
) -> str:
    return f'{question} {helper_verb} {subject} {verb} {obj}'


def check_query(response: HTTPResponse) -> bool:
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


def process_results(results: SPARQLWrapper.query, key) -> List[Tuple[str, str]]:
    return [(x["label"]["value"], x[key]["value"]) for x in results]


types = {
    'string': ['string'],
    'boolean': ['boolean'],
    'integer': ['integer', 'long'],
    'decimal': ['float', 'double'],
    'datetime': ['datetime', 'date', 'time', 'gYear', 'gMonth', 'gDay'],
    'object': None,
    'annotation': None
}


def get_all_properties():
    key = "property"
    properties = {}

    for property_type, sub_types in types.items():
        log.debug('Querying for %s', property_type)
        if property_type not in properties:
            properties[property_type] = []

        # datatypes
        if property_type not in ['object', 'annotation']:
            for sub_type in sub_types:
                query = f"""select distinct ?{key} ?label where {{
                                ?{key} a owl:DatatypeProperty ;
                                rdfs:range xsd:{sub_type} ;
                                rdfs:label ?label
                                filter langMatches( lang(?label), "EN" )
                        }}"""
                sparql.setQuery(query)
                results = sparql.query()
                bindings = results.convert()['results']['bindings']
                check_invalid_query(results.response)
                properties[property_type].extend(
                    process_results(bindings, key))

        #  objects and annotations
        else:
            query = f"""select distinct ?{key} ?label where {{
                            ?{key} a owl:{property_type.capitalize()}Property ;
                            rdfs:label ?label
                            filter langMatches( lang(?label), "EN" )
                    }}"""
            sparql.setQuery(query)
            results = sparql.query()
            bindings = results.convert()['results']['bindings']
            check_query(results.response)
            properties[property_type] = process_results(bindings, key)

    return properties


def find_all_indexes(iterable, character):
    return [i for i, letter in enumerate(iterable) if letter == character]


def generate_questions_from_template(template: str) -> List[str]:
    questions = []
    fork_points = find_all_indexes(template, '(')


def get_option(string: str):
    return [x for x in str.split('|')]
    return str.split(')')[0]


def convert_question_to_template(question: str) -> str:
    sentence = sp(question)
    log.debug([(word.text, word.pos_) for word in sentence])
    log.debug([entity for entity in sentence.ents])


def query(query_string: str, endpoint: str = config.ENDPOINT) -> SPARQLWrapper.query:
    """
    Performs the query
    """
    query_string = f"""
    {prefixes}
    {query_string}
    """
    if sparql.endpoint != endpoint:
        sparql.endpoint = endpoint
    log.debug("Executing query: \n%s", query_string)
    sparql.setQuery(query_string)
    return sparql.query()


def get_answer(question: str) -> List[str]:
    # elements = [('hello there', f"""SELECT DISTINCT ?uri ?string
    #              WHERE {{?uri rdf:type dbo:Film .
    #                     ?uri dbo:starring dbr:Julia_Roberts .
    #                     ?uri dbo:starring dbr:Richard_Gere .
    #                     OPTIONAL {{?uri rdfs:label ?string . FILTER(lang(?string)='en')}}
    #                     }}""")]

    # example = [("where was {entity} born", 12)]

    # print(example[0][0].format(entity='J.K. Rowling'))
    # example_questions = generate_question(question='when',)

    # # template = convert_question_to_template(question)

    # result = query(
    #     elements[0][1], endpoint="http://query.wikidata.org/").convert()
    # answers = [x["string"]["value"] for x in result["results"]["bindings"]]
    answers = ['Working on it!']
    return answers
