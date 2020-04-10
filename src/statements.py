used_predicates = f"""
select distinct ?predicate ?label where {{
  ?subject ?predicate ?object
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
      }} ?p a ?t
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
PREFIX dbpo: <http://dbpedia.org/ontology/>
PREFIX dbpp: <http://dbpedia.org/property/>
"""
