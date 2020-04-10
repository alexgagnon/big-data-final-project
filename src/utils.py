import requests
import spacy
import logging
import pprint
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from typing import List

sp = spacy.load('en_core_web_sm')

log = logging.getLogger("logger")

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

question_templates = [
    '(when (did|will)|in what (year|month) did) ??s?? (occur|happen)'
]

question_template = '??q?? ??h?? ??s?? ??v?? ??o??'


def generate_question(
    question: str = '??q??',
    helper_verb: str = '??h??',
    subject: str = '??s??',
    verb: str = '??v??',
    obj: str = '??o??'
) -> str:
    return f'{question} {helper_verb} {subject} {verb} {obj}'

# May not need these...


def find_all_indexes(iterable, character):
    return [i for i, letter in enumerate(iterable) if letter == character]


def generate_questions_from_template(template: str) -> List[str]:
    questions = []
    fork_points = find_all_indexes(template, '(')


def get_option(string: str):
    return [x for x in str.split('|')]
    return str.split(')')[0]


# DOESN'T WORK, Google has restricted their search api to behind an api key
def google(search_term: str, exact=True, count_only=True) -> int:
    search_term = f'"{quote_plus(search_term)}"'
    print(search_term)
    response = requests.get(f'https://google.com/search?q={search_term}')
    with open("google.html", "w") as f:
        f.write(response.text)
    content = BeautifulSoup(response.text, 'html.parser')
    stats = content.find(id='result-stats').text
    stats.replace(',', '')
    count = [int(s) for s in stats.split() if s.isdigit()]
    print(count)
    return count[0]


def convert_question_to_template(question: str) -> str:
    sentence = sp(question)
    log.debug([(word.text, word.pos_) for word in sentence])
    log.debug([entity for entity in sentence.ents])


def get_answer(question: str) -> str:
    template = convert_question_to_template(question)
    return 'TODO: Working on it!'
