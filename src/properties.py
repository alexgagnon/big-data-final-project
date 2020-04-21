import config
from typing import Union
from utils import paged_query, query, parse_query_response
from SPARQLWrapper import SPARQLWrapper, JSON
import logging
import re
import json
import os

log = logging.getLogger('logger')

valid_uri = re.compile('[\w-]+', re.IGNORECASE)

declared_properties = f"""
select distinct ?p ?label {{
    ?p a rdf:Property ;
        rdfs:label ?label
    filter langMatches(lang(?label), "EN")
}}"""


def get_number_of_property_references(uri):
    query_result = query(f"""
select (count(*) as ?count) where {{
    ?s <{uri}> ?o
}}
""")
    result = query_result.convert()['results']['bindings'][0]['count']['value']
    return int(result)


def get_all_properties():
    if os.path.exists("property_parsing.json"):
        os.remove("property_parsing.json")

    with open('property_parsing.json', 'a') as file:
        results = paged_query(declared_properties)
        log.info(f'Found {len(results)} properties')
        property_uri_label_pairs = []
        for index, result in enumerate(results):
            uri = result['p']['value']
            label = result['label']['value']
            log.debug(f'Analyzing property {index}, {label} - {uri}')
            try:
                num_references = get_number_of_property_references(uri)
                t = [uri, label, num_references]
                file.write(json.dumps(t))
                file.write('\n')
                property_uri_label_pairs.append(t)
            except Exception:
                log.error(f'Could not handle {uri}')

    return property_uri_label_pairs


def get_filtered_properties(properties, top_kth: Union[int, None] = None, min_references=config.MIN_PROPERTY_REFERENCE_COUNT):
    """
    Filters the properties to some manageable subset, removing the number of redirects
    """
    if top_kth != None:
        return [(x[0], x[1]) for x in sorted(properties, reverse=True, key=lambda x: x[2])][:top_kth]

    return [(x[0], x[1]) for x in properties if x[2] >= min_references]


def is_valid_property(uri, label):
    return is_valid_uri(uri) and has_enough_references(uri)


def is_valid_uri(uri):
    suffix = uri.split('/')[-1]
    return len(suffix) <= config.MAX_PROPERTY_LABEL_LENGTH and valid_uri.match(suffix)


def has_enough_references(uri):
    num_references = get_number_of_references(uri)
    log.debug(f'{uri} has {num_references} references')
    return num_references > config.MIN_PROPERTY_REFERENCE_COUNT
