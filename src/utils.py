import spacy
import logging
import config
from http.client import HTTPResponse
from typing import List, Tuple
from SPARQLWrapper import SPARQLWrapper, JSON
from spacy import displacy
from tabulate import tabulate

log = logging.getLogger("logger")

sparql = SPARQLWrapper(config.ENDPOINT, returnFormat=JSON)

nlp = spacy.load('en_core_web_lg')


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

sparql_statements = {
    'age': """select ?age {
        dbr:Michael_Jackson dbo:birthDate ?birthdate .
    dbr:Michael_Jackson dbo:deathDate ?deathdate .
    bind(year(?deathdate) - year(?birthdate) - if(month(?deathdate) < month(?birthdate) || (month(?deathdate)=month(?birthdate) && day(?deathdate < day(?birthdate)), 1, 0) as ?age)}""",
    'time': """f""",
    'entity': """
        ?s a rdf:Resource ;
          rdfs:label ?label .
        filter (
            regex(str(?label), %s, 'i') &&
            langMatches( lang(?label), "EN" )
        )
    """
}

question_templates = [
    ('how old is {s}', sparql_statements['age']),
    ('what age is {s}', sparql_statements['age']),
    ('when did {o} occur', ""),
    ('when did {o} happen', ""),
    ('when will {o} occur', ""),
    ('when will {o} happen', ""),
    ('in what year did {o} happen', ""),
    ('in what year did {o} occur', ""),
    ('in what month did {o} happen', ""),
    ('in what month did {o} occur', ""),
    ('in what year will {o} happen', ""),
    ('in what year will {o} occur', ""),
    ('in what month will {o} happen', ""),
    ('in what month will {o} occur', ""),
    ('on what day did {o} happen', ""),
    ('on what day did {o} occur', ""),
    ('on what day will {o} happen', ""),
    ('on what day will {o} occur'""),
    ('when did {o} happen', ""),
    ('when did {o} occur', ""),
]


def query(query_string: str, endpoint: str = config.ENDPOINT) -> SPARQLWrapper.query:
    """
    Performs a query
    """
    query_string = f"""
    {prefixes}
    {query_string}
    """
    if sparql.endpoint != endpoint:
        sparql.endpoint = endpoint
    sparql.setQuery(query_string)
    return sparql.query()


def generate_question(
    question: str = '{q}',
    helper_verb: str = '{a}',
    subject: str = '{s}',
    verb: str = '{v}',
    obj: str = '{o}'
) -> str:
    return f'{question} {helper_verb} {subject} {verb} {obj}'


def is_similar(similarity: float, threshold: float = 0.8):
    return similarity >= threshold


def get_similarity(question: str, template: str) -> float:
    q = nlp(question)
    t = nlp(template)
    return q.similarity(t)


def get_similar_templates(question: str, templates, threshold=0.8) -> List[Tuple[str, str, str]]:
    valid_templates = []
    for template, query in templates:
        similarity = get_similarity(question, template)
        if is_similar(similarity):
            valid_templates.append((similarity, template, query))

    return valid_templates


def check_query(response: HTTPResponse) -> bool:
    return is_incomplete_query(response) or is_partial_query(response)


def is_incomplete_query(response: HTTPResponse) -> bool:
    incomplete = response.getheader('X-SPARQL-MaxRows') != None
    if incomplete:
        log.warn('Query response too large!')
    return incomplete


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
    'date': ['date', 'gYear', 'gMonth', 'gDay'],
    'time': ['datetime', 'time'],
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
                check_query(results.response)
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


def convert_question_to_template(question: str) -> str:
    sentence = nlp(question)

    if config.DEBUG:
        token_table = [[
            token.text,
            token.prob,
            token.lemma_,
            (token.pos, token.pos_),
            token.tag_,
            token.dep_,
            token.shape_,
            token.is_stop
        ] for token in sentence]

        log.debug(
            tabulate(
                token_table,
                headers=[
                    'text', 'probability', 'lemma', 'part-of-speech', 'tag', 'dependency', 'shape', 'is stop'
                ]
            )
        )

        log.debug('\n')

        log.debug(
            tabulate(
                [[ent.text, ent.label_, ent.kb_id_] for ent in sentence.ents],
                headers=['text', 'label', 'KB ID']
            )
        )

        displacy.render(sentence, style='dep')
        displacy.render(sentence, style='ent')

    def replace_token(token) -> str:
        new_token = token.text
        if token.pos_ == 'VERB':
            new_token = '{v}'
        elif token.pos == 'AUX':
            new_token = '{a}'

        return new_token

    template_tokens = []
    template_tags = []

    # i = 0
    # while i < len(sentence):
    #     for ent in sentence.ents:
    #         if i == ent.start_char:
    #             i += len(ent)
    #             template_tokens.append('{e}')
    #         else:
    #             template_tokens.append(replace_token(sentence[i]))
    #             i += 1

    last_end = 0
    for ent in sentence.ents:
        template_tokens.extend([replace_token(token)
                                for token in sentence[last_end:ent.start]])
        template_tags.extend(
            [token.pos_ for token in sentence[last_end:ent.start]])

        template_tokens.append('{e}')
        template_tags.append(ent.label_)

        last_end = ent.end

    template_tokens.extend([replace_token(token)
                            for token in sentence[last_end:]])
    template_tags.extend(
        [token.tag_ for token in sentence[last_end:]])

    tag_string = ' '.join(template_tags)
    template_string = ' '.join(template_tokens)

    log.debug(tag_string)
    log.debug(template_string)

    return template_string


def get_answer(question: str, templates) -> List[str]:
    question_template = convert_question_to_template(question)
    templates = get_similar_templates(question_template, templates)

    if len(templates) == 0:
        log.info('Could not find any similar templates!')
        return []

    answers = []

    for similarity, template, query_string in templates:
        results = query(query_string)
        bindings = results.convert()['results']['bindings']
        check_query(results.response)

        if len(bindings) == 0:
            log.info('Could not find any results!')
            return []

        answers.extend([x["result"]["value"] for x in bindings])

    return answers
