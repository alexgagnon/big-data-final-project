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
    'year': simple_query_template('dbo:year'),
    'month': simple_query_template('dbo:month'),
    'day': simple_query_template('dbo:day'),
    'date': simple_query_template('dbo:date'),
    'abstract': base_query_template(statements=['<{}> dbo:abstract ?result . filter langMatches(lang(?result), "EN")'])
}

# use %s for strings you want to replace with URIs
question_templates = {
    'date': [
        ('what is {subject} {property}', common_statements['blank']),
        ('what year was {subject}', common_statements['year']),
        ('what year did {subject} happen',  common_statements['year']),
        ('when was {subject}', common_statements['date']),
        ('when did {subject} {property}', common_statements['blank']),
        ('what day did {subject} {property}', common_statements['blank']),
        ('what happened on {property}', common_statements['abstract']),
    ],
    'object': [
        ('what is {subject}', common_statements['abstract']),
        ('what is {subject} {property}', common_statements['blank']),
        ('who is {subject}',  common_statements['abstract']),
    ]
}


def generate_templates_from_properties(properties) -> List[Tuple[str, str]]:
    questions = set()

    for t, type_properties in properties.items():
        if t not in question_templates:
            continue
        else:
            log.info(f'Generating templates for {t} properties')

        for label, uri in type_properties:
            for template, query in question_templates[t]:
                questions.add((
                    template.format(subject='{}', property=label),
                    query.replace('{property}', '<' + uri + '>')
                ))

    log.info(f'Generated {len(questions)} question templates')

    return list(questions)
