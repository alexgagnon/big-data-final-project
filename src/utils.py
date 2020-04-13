import spacy
import logging
import config
from pytictoc import TicToc
from urllib.error import HTTPError
from http.client import HTTPResponse
from typing import List, Tuple, Union
from SPARQLWrapper import SPARQLWrapper, JSON
from spacy import displacy
from tabulate import tabulate
from pathlib import Path

log = logging.getLogger("logger")

sparql = SPARQLWrapper(config.ENDPOINT, returnFormat=JSON)

nlp = spacy.load('en_core_web_lg')

timer = TicToc()


def nlp_similarity(question: str, template: str) -> float:
    q = nlp(question)
    t = nlp(template)
    return q.similarity(t)


def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(
                    1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def ld_similarity(question: str, template: str) -> float:
    return 1 / levenshtein_distance(question, template)


get_similarity = nlp_similarity
if config.SIMILARITY_METRIC == 'ld':
    get_similarity = ld_similarity


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


def query(query_string: str, endpoint: str = config.ENDPOINT) -> SPARQLWrapper.query:
    """
    Performs a query
    """
    start = timer.tic()
    query_string = f"""
    {prefixes}
    {query_string}
    """
    if sparql.endpoint != endpoint:
        sparql.endpoint = endpoint
    sparql.setQuery(query_string)
    try:
        response = sparql.query()
        timer.toc('Query took: ')
        return response
    except HTTPError as error:
        log.info('SPARQL query error')
        log.debug(error)


def is_similar(similarity: float, threshold: float = config.THRESHOLD):
    return similarity >= threshold


def get_similar_templates(question: str, templates, threshold=0.8) -> List[Tuple[str, str, str]]:
    valid_templates = []
    for template, query in templates:
        similarity = get_similarity(question, template)
        if is_similar(similarity):
            valid_templates.append((similarity, template, query))

    return sorted(valid_templates, key=lambda x: x[0], reverse=True)


def check_invalid_query(response: HTTPResponse) -> bool:
    if is_incomplete_query(response) or is_partial_query(response):
        raise Exception

    return False


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
    'date': ['datetime', 'date', 'gYear', 'gMonth', 'gDay'],
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
                try:
                    bindings = parse_query_response(results)
                    properties[property_type].extend(
                        process_results(bindings, key))
                except Exception:
                    continue

        #  objects and annotations
        else:
            query = f"""select distinct ?{key} ?label where {{
                            ?{key} a owl:{property_type.capitalize()}Property ;
                            rdfs:label ?label
                            filter langMatches( lang(?label), "EN" )
                    }}"""
            sparql.setQuery(query)
            results = sparql.query()
            bindings = parse_query_response(results)
            properties[property_type] = process_results(bindings, key)

    return properties


def parse_query_response(query_results: SPARQLWrapper.query) -> List[str]:
    bindings = query_results.convert()['results']['bindings']
    check_invalid_query(query_results.response)  # can throw Exception
    return bindings


def convert_question_to_template(question: str) -> Tuple[str, List[str]]:

    def replace_token(token) -> str:
        new_token = token.text
        if token.pos_ == 'VERB':
            new_token = '{v}'

        return new_token

    sentence = nlp(question)

    # strip out date entities... we want to be able to compare sentences
    entities = [entity for entity in sentence.ents if entity.label_ != 'DATE']
    template_tokens = []
    template_tags = []

    last_end = 0

    # build sentence template from tokens and entities, since entities can
    # span multiple tokens
    for ent in entities:
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

        log.debug('\n')

        svg = displacy.render(sentence, style="dep")
        output_path = Path("sentence-deps.svg")
        output_path.open("w", encoding="utf-8").write(svg)

        svg = displacy.render(sentence, style="ent")
        output_path = Path("sentence-ents.svg")
        output_path.open("w", encoding="utf-8").write(svg)

        log.debug(question)
        log.debug(tag_string)
        log.debug(template_string)

    return (template_string, entities)


def get_uri(label: str) -> Union[None, str]:
    log.debug(f'Getting uri for {label}')
    result = query(f"""SELECT DISTINCT * WHERE {{
        ?labelUri rdfs:label ?label .
        filter ( ?label = "{label}"@en )
        optional {{?labelUri dbo:wikiPageRedirects ?redirectUri}}
    }}""")

    bindings = parse_query_response(result)  # can throw Exception
    if len(bindings) == 0:
        log.info(f'No matching uri for {label}')

    # a label should have a URI associated with it (unless there is no match)
    # HOWEVER, a label might reference a URI that redirects to the real entity
    # i.e. J.K. Rowling is a valid label, but returns J.K._Rowling, which
    # redirects to the real entity, J. K. Rowling (J._K._Rowling)
    # SO, return the URI UNLESS a redirect URI is present
    uri = get_result_value(bindings[0], key='labelUri')
    for binding in bindings:
        if 'redirectUri' not in binding:
            continue
        redirectUri = get_result_value(binding, key='redirectUri')
        if redirectUri:
            uri = redirectUri
            break

    return uri


def get_result_value(result, key="result") -> str:
    return result[key]["value"]


def replace_uris_in_query(template, uris) -> str:
    log.debug(f'{template}\n{uris}\n\n')
    return template.format(*uris)


def get_answer(question: str, templates) -> List[str]:
    log.info('Converting question to template')
    timer.tic()
    question_template, entities = convert_question_to_template(question)
    timer.toc(f'Got template "{question_template}" in: ')
    log.info(
        f'Searching through {len(templates)} templates using {config.SIMILARITY_METRIC} similarity metric')
    timer.tic()
    templates = get_similar_templates(question_template, templates)
    timer.toc(
        f'Found {len(templates)} with a similarity above threshold of {config.THRESHOLD} in:'
    )

    timer.tic()
    uris = [get_uri(entity) for entity in entities]
    timer.toc(f'Found URIs for entities {entities} in:')

    if len(templates) == 0:
        log.info('Could not find any similar templates!')
        return []

    log.debug(uris)
    log.debug('Top 5 templates:')
    for x in templates[:min(len(templates) - 1, 5)]:
        log.debug(x)

    answers = []

    for index, template in enumerate(templates):
        if index >= config.MAX_TEMPLATE_SEARCHES:
            log.info('Maximum iterations of templates exceeded, no results :(')
            return []

        log.debug(template)
        query_string = replace_uris_in_query(template[2], uris)
        log.debug(query_string)
        results = query(query_string)

        try:
            bindings = parse_query_response(results)
            if len(bindings) == 0:
                log.debug(f'No matches for {query_string}')
                continue

            return [get_result_value(x) for x in bindings]
        except:
            log.info('Could not find matching entity URI')

    return answers
