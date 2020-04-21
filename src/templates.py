from typing import List, Tuple
import timeit
import logging

log = logging.getLogger('logger')


def simple_query_template(property: str) -> str:
    return f"""select ?result where {{{{
      <{{}}> {property} ?result
    }}}}"""


def base_query_template(projection: str = "?result", statements: List = []) -> str:
    query = 'select distinct ' + projection + ' where {{'
    for statement in statements:
        query += '\n' + statement
    query += '}}'

    return query


common_statements = {
    'blank': simple_query_template('{property}'),
    'location': simple_query_template('dbo:location'),
    'year': simple_query_template('dbo:year'),
    'month': simple_query_template('dbo:month'),
    'day': simple_query_template('dbo:day'),
    'date': simple_query_template('dbo:date'),
    'abstract': base_query_template(statements=['<{}> dbo:abstract ?result . filter langMatches(lang(?result), "EN")'])
}

# use %s for strings you want to replace with URIs
# question_templates = {
#     'date': [
#         ('what is {subject} {property}', common_statements['blank']),
#         ('what year was {subject}', common_statements['year']),
#         ('what year did {subject} happen',  common_statements['year']),
#         ('when was {subject}', common_statements['date']),
#         ('when did {subject} {property}', common_statements['blank']),
#         ('what day did {subject} {property}', common_statements['blank']),
#         ('what happened on {property}', common_statements['abstract']),
#     ],
#     'object': [
#         ('what is {subject}', common_statements['abstract']),
#         ('what is {subject} {property}', common_statements['blank']),
#         ('who is {subject}',  common_statements['abstract']),
#     ]
# }

question_templates = [
    ('what day did {subject} {property}', common_statements['day']),
    ('what year did {subject} {property}', common_statements['year']),
    ('what occured on {property}', common_statements['abstract']),
    ('what is {subject} {property}', common_statements['blank']),
    ('what is {subject}', common_statements['abstract']),
    ('what is there to {property} in {subject}', common_statements['blank']),
    ('what year did {subject} occur',  common_statements['year']),
    ('what year was {subject}', common_statements['year']),
    ('when did {subject} {property}', common_statements['blank']),
    ('when was {subject} {property}', common_statements['blank']),
    ('when was {subject}', common_statements['date']),
    ('where did {property} occur', common_statements['blank']),
    ('where did {subject} {property}', common_statements['blank']),
    ('where was {subject} when {property}', common_statements['blank']),
    ('where is {property}', common_statements['location']),
    ('who is {subject}',  common_statements['abstract']),

    # ('which {object} did {subject} {property}', ),
]


def generate_templates_from_properties(properties) -> List[Tuple[str, str]]:
    questions = set()

    for uri, label in properties:
        for template, query in question_templates:
            questions.add((
                template.format(subject='{e}', property=label),
                query.replace('{property}', '<' + uri + '>')
            ))

    # OLD WAY USING SPECIFIC QUESTION TYPES
    # for t, type_properties in properties.items():
    #     if t not in question_templates:
    #         continue
    #     else:
    #         log.info(f'Generating templates for {t} properties')

    #     for label, uri in type_properties:
    #         for template, query in question_templates[t]:
    #             questions.add((
    #                 template.format(subject='{}', property=label),
    #                 query.replace('{property}', '<' + uri + '>')
    #             ))

    log.info(f'Generated {len(questions)} question templates')

    return list(questions)
