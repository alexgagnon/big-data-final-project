import config
from typing import Union, List, Dict, Tuple
from utils import paged_query, query, parse_query_response, nlp
from SPARQLWrapper import SPARQLWrapper, JSON
import logging
import re
import json
import os

log = logging.getLogger('logger')

valid_uri = re.compile('[\w-]+', re.IGNORECASE)


class Property(dict):
    def __init__(self, uri, label, lemma, pos, num_references):
        self.uri = uri
        self.label = label
        self.num_references = num_references
        self.lemma = lemma
        self.pos = pos


all_declared_properties_SPARQL = f"""
select distinct ?property ?label {{
    ?property a rdf:Property ;
        rdfs:label ?label
    filter langMatches(lang(?label), "EN")
}}"""

datatype_property_SPARQL = """select distinct ?property ?label where {{
                                        ?property a owl:DatatypeProperty ;
                                        rdfs:range xsd:{sub_type} ;
                                        rdfs:label ?label
                                        filter langMatches( lang(?label), "EN" )
                                }}"""

object_property_SPARQL = """select distinct ?property ?label where {{
                            ?property a owl:ObjectProperty ;
                            rdfs:label ?label
                            filter langMatches( lang(?label), "EN" )
                    }}"""

generic_type_SPARQL = """select distinct ?property ?label where {{
                                        ?property a {type} ;
                                        rdfs:label ?label
                                        filter langMatches( lang(?label), "EN" )
                                }}"""


# creates generic types matching OWL property types, with the associated SPARQL
# OWL defines the specific datatypes based on the ranges they can produce
types = [
    ('object', None, object_property_SPARQL),  # 'objects' are other entities
    ('string', ['string'], datatype_property_SPARQL),
    ('boolean', ['boolean'], datatype_property_SPARQL),
    (
        'number',
        ['integer', 'long', 'float', 'double'],
        datatype_property_SPARQL
    ),
    ('date', ['date'], datatype_property_SPARQL),
    ('time', ['datetime', 'time'], datatype_property_SPARQL),
    ('year', ['gYear'], datatype_property_SPARQL),
    ('month', ['gMonth'], datatype_property_SPARQL),
    ('day', ['gDay'], datatype_property_SPARQL),
]


def get_number_of_property_references(uri: str) -> int:
    """
    Returns the number of times a property is actually used in the DB
    """
    query_result = query(f"""
        select (count(*) as ?count) where {{
            ?s <{uri}> ?o
        }}
    """)
    result = query_result.convert()['results']['bindings'][0]['count']['value']
    return int(result)


def get_property_types(
    query: str,
    property_key: str,
    label_key: str
) -> List[Tuple]:
    """
    Returns a dictionary of datatype - property pairs
    """
    properties = []
    results = paged_query(query)
    num_results = len(results)
    for index, result in enumerate(results):

        uri = result[property_key]['value']
        label = result[label_key]['value']
        doc = nlp(label)
        lemmas = [token.lemma_ for token in doc]
        poss = [token.pos_ for token in doc]
        log.debug(
            f'Analyzing property {index} of {num_results}, {label} - {uri}')
    # try:
        num_references = get_number_of_property_references(uri)
        properties.append((uri, label, num_references, lemmas, poss))

    return properties


def get_all_properties() -> Dict[str, List]:
    """
    Downloads and parses all properties from the DB
    """
    property_key = 'property'
    label_key = 'label'
    properties = {}

    for property_type, sub_types, query in types:
        log.debug('Querying for %s', property_type)
        if property_type not in properties:
            properties[property_type] = []

        if sub_types != None:
            for sub_type in sub_types:
                properties[property_type].extend(
                    get_property_types(query.format(sub_type=sub_type), property_key, label_key))

        else:
            properties[property_type].extend(
                get_property_types(query, property_key, label_key))

    return properties


def get_filtered_properties(
        all_properties: Dict[str, List[Property]],
        top_kth: Union[int, None] = None,
        min_references: int = config.MIN_PROPERTY_REFERENCE_COUNT):
    """
    Filters the properties to some manageable subset, reducing the number of templates generated
    """
    properties = {}
    for property_type, a, b in types:
        if top_kth != None:
            properties[property_type] = [(x[0], x[1]) for x in sorted(
                all_properties[property_type], reverse=True, key=lambda x: x[2])][:top_kth]

        else:
            properties[property_type] = [
                (x[0], x[1]) for x in all_properties[property_type] if x[2] >= min_references]

    return properties
