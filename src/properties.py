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

types = {
    # 'object': None,
    # 'string': ['string'],
    'boolean': ['boolean'],
    'integer': ['integer', 'long'],
    # 'decimal': ['float', 'double'],
    # 'date': ['datetime', 'date', 'gYear', 'gMonth', 'gDay'],
    # 'time': ['datetime', 'time'],
}


def get_number_of_property_references(uri):
    query_result = query(f"""
select (count(*) as ?count) where {{
    ?s <{uri}> ?o
}}
""")
    result = query_result.convert()['results']['bindings'][0]['count']['value']
    return int(result)


def get_property_types(query: str, property_key, label_key):
    properties = []
    results = paged_query(query)
    num_results = len(results)
    for index, result in enumerate(results):
        uri = result[property_key]['value']
        label = result[label_key]['value']
        log.debug(
            f'Analyzing property {index} of {num_results}, {label} - {uri}')
        try:
            num_references = get_number_of_property_references(uri)
            properties.append((uri, label, num_references))
        except Exception:
            log.debug(f'Could not handle {uri}')

    return properties


def get_all_properties():
    # if os.path.exists("property_parsing.json"):
    #     os.remove("property_parsing.json")

    # with open('property_parsing.json', 'a') as file:

    #     results = paged_query(declared_properties)
    #     log.info(f'Found {len(results)} properties')
    #     property_uri_label_pairs = []
    #     for index, result in enumerate(results):
    #         uri = result['p']['value']
    #         label = result['label']['value']
    #         log.debug(f'Analyzing property {index}, {label} - {uri}')
    #         try:
    #             num_references = get_number_of_property_references(uri)
    #             t = [uri, label, num_references]
    #             file.write(json.dumps(t))
    #             file.write('\n')
    #             property_uri_label_pairs.append(t)
    #         except Exception:
    #             log.error(f'Could not handle {uri}')

    # return property_uri_label_pairs

    property_key = 'property'
    label_key = 'label'
    properties = {}

    for property_type, sub_types in types.items():
        log.debug('Querying for %s', property_type)
        if property_type not in properties:
            properties[property_type] = []

        if property_type not in ['object', 'location']:
            for sub_type in sub_types:
                query = f"""select distinct ?{property_key} ?{label_key} where {{
                                        ?{property_key} a owl:DatatypeProperty ;
                                        rdfs:range xsd:{sub_type} ;
                                        rdfs:label ?{label_key}
                                        filter langMatches( lang(?label), "EN" )
                                }}"""
                properties[property_type].extend(
                    get_property_types(query, property_key, label_key))

        elif property_type == 'object':
            query = f"""select distinct ?{property_key} ?{label_key} where {{
                            ?{property_key} a owl:ObjectProperty ;
                            rdfs:label ?{label_key}
                            filter langMatches( lang(?label), "EN" )
                    }}"""

            properties[property_type].extend(
                get_property_types(query, property_key, label_key))

    return properties


def get_filtered_properties(all_properties, top_kth: Union[int, None] = None, min_references=config.MIN_PROPERTY_REFERENCE_COUNT):
    """
    Filters the properties to some manageable subset, removing the number of redirects
    """
    properties = {}
    for property_type in types.keys():
        if top_kth != None:
            properties[property_type] = [(x[0], x[1]) for x in sorted(
                all_properties[property_type], reverse=True, key=lambda x: x[2])][:top_kth]

        else:
            properties[property_type] = [
                (x[0], x[1]) for x in all_properties[property_type] if x[2] >= min_references]

    return properties
