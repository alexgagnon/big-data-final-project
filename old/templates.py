import time
import logging
import pickle
import json
from config import DEBUG
from typing import Dict, List
from SPARQLWrapper import SPARQLWrapper2, JSON

log = logging.getLogger("logger")

# Use SPARQLWrapper2 so we can do map operations directly on the response
sparql = SPARQLWrapper2("http://dbpedia.org/sparql")


def updateTemplates() -> Dict:
    """
    (Re)generates all the templates. Fetches the collection of objects and predicates from the knowledge base and then turns them into simple binary template questions with matching SPARQL queries
    """
    elements = {
        # "types": getAllTypes(),
        "predicates": getAllPredicates()
    }

    # with open("elements.pkl", "wb") as f:
    #     pickle.dump(elements, f)

    with open("element.json", "w", encoding="utf8") as f:
        json.dump(elements, f, ensure_ascii=False)

    return elements


def pagedQuery(query_string, page_size=10, delay=3, max_iterations=None) -> SPARQLWrapper2.query:
    """
    Virtuoso will only send PARTIAL results when the timeout is reached, so there is a chance you may not get back all results. To fix this, make paged requests
    """
    results = None
    i = 0
    while True:
        if max_iterations != None and i >= max_iterations:
            break
        offset = i * page_size
        paged_query = f"{query_string} limit {page_size} offset {offset}"
        result = query(paged_query)
        if len(result.bindings) > 0:
            if results == None:
                results = result.bindings
            results += result.bindings
            i += 1
            time.sleep(delay)
        else:
            break

    return results


def ask(triple: str) -> bool:
    result = query(f"""select * where {{
        {triple}
    }}""")

    return result.bindings


def query(query_string: str) -> SPARQLWrapper2.query:
    """
    Performs the query
    """
    query_string = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" + query_string
    log.debug(" Executing query: \n%s", query_string)
    sparql.setQuery(query_string)
    return sparql.query()


def getAllTypes() -> SPARQLWrapper2.query:
    """
    Returns all types in the knowledge base
    """
    result = query("""select distinct ?type ?label where {?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type ;
            rdfs:label ?label .
        filter langMatches( lang(?label), "EN" )
    }""")

    #  Transform the result into a useable array
    types = [[x["type"].value, x["label"].value]
             for x in result.bindings]

    return types

# select * where {
#   ?p a owl:DatatypeProperty ;
#      rdfs:range xsd:gYear .
# }


def isLabelled(element) -> bool:
    return "label" in element


def getAllPredicates(limit=None) -> List:
    """
    Returns all predicates in the knowledge base
    """

    where_clause = """where {
                        ?predicate a rdfs:predicate
                        optional {
                            ?predicate rdfs:label ?label .
                        }
                        filter langMatches(lang(?label), "EN")
                    } group by ?label order by ?label"""

    result = pagedQuery("select ?predicate ?label " +
                        where_clause, page_size=40, max_iterations=3)


    predicates = list(map(lambda x: [x["predicate"].value, x["label"].value], filter(
        hasValidLabel, result)))

    return predicates
