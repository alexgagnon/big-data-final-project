import spacy
import logging
import config
import re
from pytictoc import TicToc
from urllib.error import HTTPError
from http.client import HTTPResponse
from typing import List, Tuple, Union
from SPARQLWrapper import SPARQLWrapper, JSON
from spacy import displacy
from tabulate import tabulate
from pathlib import Path
from errors import SPARQLQueryError, SPARQLQueryTooLarge

log = logging.getLogger("logger")

sparql = SPARQLWrapper(config.ENDPOINT, returnFormat=JSON)

nlp = spacy.load('en_core_web_lg')

regex = re.compile('<.*>')


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


def paged_query(query_string: str) -> SPARQLWrapper.query:
    """
    Allows for running queries that return all of the items, not limited by the endpoints max limit
    """
    limit = 10000  # typical max for Virtuoso servers
    results = []
    iteration = 0
    while True:
        sparql.setQuery(
            f'{query_string} limit {limit} offset {iteration * limit}'
        )
        query_results = sparql.query()
        results.extend(query_results.convert()['results']['bindings'])
        try:
            is_incomplete_query(query_results.response)
            break
        except SPARQLQueryTooLarge:
            iteration += 1
            log.debug(
                f'Incomplete response, fetching next {limit} at offset: {limit * iteration}')

    return results


def query(query_string: str, endpoint: str = config.ENDPOINT) -> SPARQLWrapper.query:
    """
    Generic function to perform a query
    """
    query_string = f"""
    {prefixes}
    {query_string}
    """

    if sparql.endpoint != endpoint:
        sparql.endpoint = endpoint
    sparql.setQuery(query_string)
    try:
        response = sparql.query()
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
    return not is_incomplete_query(response) or is_partial_query(response)


def is_incomplete_query(response: HTTPResponse) -> bool:
    incomplete = response.getheader('X-SPARQL-MaxRows') != None
    if incomplete:
        raise SPARQLQueryTooLarge
    return incomplete


def is_partial_query(response: HTTPResponse) -> bool:
    partial = response.getheader('X-SQL-State') != None
    if partial:
        log.warn('Partial response!')
    return partial


def process_results(results: SPARQLWrapper.query, key) -> List[Tuple[str, str]]:
    return [(x["label"]["value"], x[key]["value"]) for x in results]


def parse_query_response(query_results: SPARQLWrapper.query) -> List[str]:
    bindings = query_results.convert()['results']['bindings']
    check_invalid_query(query_results.response)  # can throw Exception
    return bindings


def replace_token(token) -> str:
    new_token = token.text
    if token.pos_ == 'VERB':
        new_token = '{v}'

    return new_token


def convert_question_to_template(question: str) -> Tuple[str, List[any]]:

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

    if config.FIGURES:
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

        svg = displacy.render(sentence, style="ent")
        output_path = Path("sentence-ents.svg")
        output_path.open("w", encoding="utf-8").write(svg)

        svg = displacy.render(sentence, style="dep")
        output_path = Path("sentence-deps.svg")
        output_path.open("w", encoding="utf-8").write(svg)

        log.debug(question)
        log.debug(tag_string)
        log.debug(template_string)

    return (template_string, entities)


def get_uri(label: str) -> Union[None, List[str]]:
    # loose_match = f"""SELECT DISTINCT * WHERE {{
    #     ?labelUri rdfs:label ?label .
    #     FILTER (
    #         langMatches(lang(?label), "EN") &&
    #         CONTAINS(LCASE(STR(?label)), "{label.lower()}")
    #     )
    #     optional {{?labelUri dbo:wikiPageRedirects ?redirectUri}}
    # }}"""

    exact_match = f"""SELECT DISTINCT * WHERE {{
        ?labelUri rdfs:label ?label .
        filter (
            ?label = "{label}"@en
        )
        optional {{?labelUri dbo:wikiPageRedirects ?redirectUri}}
    }}"""

    log.debug(f'Getting uris for {label}')
    result = query(exact_match)

    bindings = parse_query_response(result)  # can throw Exception
    if len(bindings) == 0:
        log.debug(f'No matching uri for {label}')
        return None

    # a label should have a URI associated with it (unless there is no match)
    # HOWEVER, a label might reference a URI that redirects to the real entity
    # i.e. J.K. Rowling is a valid label, but returns J.K._Rowling, which
    # redirects to the real entity, J. K. Rowling (J._K._Rowling)
    # SO, return the URI UNLESS a redirect URI is present
    uris = []

    for binding in bindings:
        key = 'labelUri' if 'redirectUri' not in binding else 'redirectUri'
        uris.append(get_result_value(binding, key=key))

    return uris


def get_uris(entities) -> List[str]:
    uris = []
    for entity in entities:
        # If the KB entiter linker is used, entities may have corresponding URIs
        # already in spaCy. If not, hit the DB and try to find it
        id = entity.kb_id_
        if id == '':
            id = get_uri(entity.text)

        if id != None:
            uris.append(id)

    return uris


def get_result_value(result, key="result") -> str:
    return result[key]["value"]


def replace_uris_in_query(query, uris) -> str:
    return query.format(uris)


apostrophe_regex = re.compile("'s\s")


def get_answer(question: str, templates: List) -> Union[None, List[str]]:
    # get question as template
    timer.tic()
    if config.STRIP_POSSESSIVE_APOSTROPHES:
        question = question.replace("'s ", ' ')
    question_template, entities = convert_question_to_template(question)
    log.info(
        f'Converted question to "{question_template}" with entities {entities} in: {timer.tocvalue()}')

    # get URIs for entities
    # TODO: not a good way to handle multiple entities...
    timer.tic()
    uris = get_uris(entities)

    if len(uris) == 0:
        return None

    log.info(
        f'Found {len(uris)} URIs for entities {entities} in: {timer.tocvalue()}')
    log.debug(uris)

    #  find similar templates
    log.info('Getting similar templates...')
    timer.tic()
    templates = get_similar_templates(question_template, templates)
    # templates is (similarity, question, query)
    log.info(
        f'Found {len(templates)} similar templates in: {timer.tocvalue()}'
    )

    if len(templates) == 0:
        log.info('Could not find any similar templates!')
        return None

    log.debug('Top 5 templates:')
    for x in templates[:min(len(templates) - 1, 5)]:
        log.debug(x)

    answers = []

    # try various entity URIs and templates
    # TODO: bad way of assigning URIs to specific entities... nested lists
    iterations = 0
    for template in templates:
        for entities in uris:
            if entities == None:
                iterations += 1
                continue
            for entity_uri in entities:
                if iterations >= config.MAX_TEMPLATE_SEARCHES:
                    log.info(
                        'Maximum iterations of templates exceeded, no results :(')
                    return []

                iterations += 1
                query_string = replace_uris_in_query(
                    template[2], entity_uri)
                log.debug(query_string)
                results = query(query_string)

                try:
                    bindings = parse_query_response(results)
                    if len(bindings) == 0:
                        continue

                    return [get_result_value(x) for x in bindings]
                except SPARQLQueryError as error:
                    log.info('Could not find matching entity URI')
                    log.debug(error)

    return answers
