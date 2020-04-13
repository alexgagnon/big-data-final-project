from typing import List, Tuple
import logging

log = logging.getLogger('logger')

sparql_statements = {
    'age': {
        'statements': """%e dbo:birthDate ?birthdate .
                        %e dbo:deathDate ?deathdate .
                        bind(year(?deathdate) - year(?birthdate) - if(month(?deathdate) < month(?birthdate) || (month(?deathdate)=month(?birthdate) && day(?deathdate < day(?birthdate)), 1, 0) as ?age)}""",
        'filters': []
    },
    'time': {
        'statements': """%""",
        'filters': ""
    },
    'entity': """
        ?s a rdf:Resource ;
          rdfs:label ?label .
        filter (
            regex(str(?label), %s, 'i') &&
            langMatches( lang(?label), "EN" )
        )
    """
}

question_templates = {
    # ('how old is %e', sparql_statements['age']),
    # ('what age is %e', sparql_statements['age']),
    # ('did %e happen before %e'),
    # ('did %e happen after %e'),
    # ('did %e happen between %e and %e'),
    # ('when did %e occur', ""),
    # ('when did %e happen', ""),
    # ('when will %e occur', ""),
    # ('when will %e happen', ""),
    # ('in what year did %e happen', ""),
    # ('in what year did %e occur', ""),
    # ('in what month did %e happen', ""),
    # ('in what month did %e occur', ""),
    # ('in what year will %e happen', ""),
    # ('in what year will %e occur', ""),
    # ('in what month will %e happen', ""),
    # ('in what month will %e occur', ""),
    # ('on what day did %e happen', ""),
    # ('on what day did %e occur', ""),
    # ('on what day will %e happen', ""),
    # ('on what day will %e occur'""),
    # ('when did %e happen', ""),
    # ('when did %e occur', ""),

    'date': [('when did ?s {property}', ['date'],
              'select ?date {{?s {property} ?o ; dbo:date ?date}}')]
    # 'object': [('who has ?o')]
    # ('when did %o %v %s', 'select * {?s  ?')
    # ('when was %o', 'select * {?s dbo:date %o'),
    # ('when was %s %v', 'select * {?s dbo:date %o')
    # ('who %v %o', 'select * {?s %v %o}')
    # ('did %e %v'),
    # ('where did %s %v', 'select * {%s }')
}


def generate_templates_from_properties(properties) -> List[Tuple[str, str]]:
    questions = []

    for t, type_properties in properties.items():
        print(t)
        if t not in question_templates:
            log.info(f'Skipping {t}')
            continue
        else:
            log.info(f'Generating templates for {t}')

        for label, uri in type_properties:
            for template, keys, query in question_templates[t]:
                questions.append((
                    template.format(property=label),
                    keys,
                    query.format(property='<' + uri + '>')))

    return questions
