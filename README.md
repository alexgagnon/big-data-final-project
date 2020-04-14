# RDFQA

This software and paper was produced as the final project deliverable for COMP5118

## Running the application

- an easy setup file is provided `./setup.sh`, otherwise do the following steps
- install a virtual environment if you want some isolation
  - i.e. `sudo apt install python3-venv && python3 -m venv venv && . venv/bin/activate`
- install dependencies: `pip install -r requirements.txt`
- [spaCy](https://spacy.io/) is used for NLP on the questions, and we need the english language model (NOTE: this file is almost 1GB)
  - `python -m spacy download en_core_web_lg`
- run: `python3 src/rdfqa.py -h`
- for development, you can set default CLI arguments in `src/config.py`

## Problem Definition

- restricted to:
  - english only
  - questions of the form `when/what/who/where/why ...`
  - 'used' predicates, as opposed to 'defined' predicates
    - used - `select ?p {?s ?p ?o}`
    - defined - `select distinct ?p {{select ?p {?p a rdf:Property}} union {select ?p { VALUES ?t { owl:ObjectProperty owl:DatatypeProperty owl:AnnotationProperty } ?p a ?t}}`

## TODO

- [ ] - better exception handling
- [ ] - use LSH for template matching
- [x] - edit distance similarity metric
- [ ] - move to objects or classes so we don't hardcode tuple indexes
- [ ] - query google to see if a given template makes sense
- [ ] - fix entity URIs data structure
- [ ] - waiting spinner
- [ ] - also find properties redirects (i.e. 'born' should redirect to 'birth date')
- [ ] - benchmark against other Simple QALD datasets
- [ ] - instead of

## Concepts

- if you're new to SPARQL, NLP, and Knowledge Bases, the following may help you understand the code base better

### SPARQL

- there are several large knowledge graphs available online, such as DBpedia and Wikidata, that you can query with the SPARQL language
- SPARQL is somewhat similar to SQL, and allows for create (CONSTRUCT) and read (SELECT), and also provides ASK (true/false) and DESCRIBE (summarize) operations
- all facts in the knowledge graph are stored as 3-tuples called _triples_: (subject, predicate, object)
  - i.e. `(Ottawa, capitalOf, Canada)` and `(Earth, instanceOf, Planet)`
- to avoid ambiguity, every thing is referenced by a URI, typically in the form of URLs (i.e. `<http://dbpedia.org/property/Artist>`)
- for common URIs, you can define a `PREFIX` short form (i.e. `PREFIX dbp: <http://dbpedia.org/property/>`)
- every statement has 3 positional arguments rhat correspond to the triples parameters
  - i.e. `select * {1 2 3}`
  - 1 = subject
  - 2 = predicate
  - 3 = object
- variables are prefixed with `?`, e.g. `?label`, and can be referenced throughout query, both in the statement and to select projections (i.e. `select ?label { ?s rdfs:label ?label }`, which returns all entities with labels)
- for each statement, you either fix an argument with a URI or literal, or assign a variable
- the SPARQL engine will find all matching triples in the graph, i.e.
  - `select * {?s <https://www.wikidata.org/wiki/Q5119> <https://www.wikidata.org/wiki/Q16>}`
- `a` is short for `rdf:type`, hence things like `?s a rdf:Property`
- `.` means to conjoin one statement to the next (i.e. keep context between them)
- `;` means to conjoin and use the **_same subject_** between statements (basically, you only need the `?p ?o` part)
- for each conjuction (`.` or `;`), an inner join will occur, meaning all subjects that don't match the statement will be filtered out.
  - if you want to still include these records even though they might not have the property, you'll need to use `OPTIONAL` keyword before the statement
- you can restrict the possible values using additional qualifiers, such as domain (input, subject), range (output, object), and datatype
- some URIs just redirect to another entity, so you need to follow these if you want to see

### NLP

- NLP is about deconstructing human language, with all its complexity and ambiguity, into something a computer can operate on
- given any bit of language, we have some operations we can perform:
  - tokenization - identifying pieces of text, like entities (nouns), verbs, adjectives, etc.
  - stemming - finding the 'stem' of a word, useful to find variations of a word (i.e. comput is the stem of compute, computed, computer, computing, etc.). The stem need not be a real word
  - lemmatization - similar to 'stemming', but the root is actually a word (i.e. compute is the lemma of computer, computed, computing, etc.)
- one crucial piece is to be able to identify entities ('things'), which might span multiple tokens (i.e. J. K. Rowling is a single entity)
