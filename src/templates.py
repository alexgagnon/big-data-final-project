from typing import List, Tuple
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
    'person': simple_query_template('dbo:person'),
    'abstract': base_query_template(statements=['<{}> dbo:abstract ?result . filter langMatches(lang(?result), "EN")'])
}

question_templates = [
    ('when did {subject} {property}', ['date', 'year']),
    ('when was {subject} {property}', ['date', 'year']),
    ('when was {subject}', ['date']),
    ('what occured on {property}', [
        'date', 'year', 'month', 'day']),
    ('what occured in {property}', ['year', 'month', 'place']),
    ('what occured at {subject}', ['abstract']),
    ('what year did {subject} occur', ['year']),
    ('what year did {subject} {property}', ['year']),
    ('what day did {subject} {property}', ['day']),
    ('what month did {subject} {property}', ['month']),
    ('what happened at {property}', ['abstract']),
    ('what is {subject} {property}', ['blank']),
    ('what is {subject}', ['abstract']),
    ('what is there to {property} in {subject}', ['blank']),
    ('where did {property} occur', ['location']),
    ('where did {subject} {property}', ['location']),
    ('where was {subject} when {property}', ['location']),
    ('where is {property}', ['location']),
    ('who is {subject}',  ['abstract']),
    ('does {subject} {property}', ['boolean'])

    # ('in which {property} did {subject} {property}'),
    # ('in what {property} did {sobject} {object}'),
]

type_mapping = {
    ''
}


def generate_templates_from_properties(properties) -> List[Tuple[str, str]]:
    questions = set()

    print(properties)

    for property_type in:
        for template, property_types in question_templates:
            for property_type in property_types:
                query = common_statements[property_type]
                questions.add((
                    template.format(subject='{e}', property=label),
                    query.replace('{property}', '<' + uri + '>')
                ))

    return list(questions)
