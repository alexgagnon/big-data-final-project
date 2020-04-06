import logging
import pickle
import json
from typing import Dict
from SPARQLWrapper import SPARQLWrapper2, JSON, Bindings

log = logging.getLogger("logger")

# Use SPARQLWrapper2 so we can do map operations directly on the response
sparql = SPARQLWrapper2("http://dbpedia.org/sparql")


def updateTemplates() -> Dict:
    """
    (Re)generates all the templates. Fetches the collection of objects and predicates from the knowledge base and then turns them into simple binary questions with matching SPARQL queries
    """
    elements = {
        "types": getAllTypes(),
        # "predicates": getAllProperties()
    }

    with open("elements.pkl", "wb") as f:
        pickle.dump(elements, f)

    with open("element.json", "w") as f:
        json.dump(elements, f)

    return elements


def query(query: str) -> Bindings:
    """
    Performs the query
    """
    sparql.setQuery(query)
    return sparql.query()


def getAllTypes():
    """
    Returns all types in the knowledge base
    """
    result = query("""select distinct ?label where {
        ?subject <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type ;
            rdfs:label ?label .
        filter langMatches( lang(?label), "EN" )
    } limit 10""")

    types = [{"label": x["label"].value, "type": x["label"].value}
             for x in result.bindings]

    return types


def getRootTypes():
    return query("""SELECT ?directSub ?super
                 WHERE {?directSub rdfs: subClassOf ?super .
                        FILTER NOT EXISTS {?directSub rdfs: subClassOf ?otherSub .
                            FILTER(?otherSub != ?directSub)
                                           }
                        }""")


def getAllProperties():
    return query("""SELECT DISTINCT ?pred WHERE { ?s ?pred ?o } limit 10""")


def printQueryResults(results) -> None:
    for result in results["results"]["bindings"]:
        print(result)
