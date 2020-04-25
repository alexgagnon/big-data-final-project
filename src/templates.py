# Template question/SPARQL pairs are generated from the pre-computed properties
# and a list of question templates. The goal is to produce a set of these
# templates that make similarity matching very simple, fast, and effective.
# One mechanism is to filter based on the datatype of the property used.
# Some questions contain a property label or variation of it, others may have
# the desired property in the context of the question itself, such as
# 'who is ...'. Other questions may have additional qualifiers that could be
# used to restrict the range of generated result
# Some examples:
#   who is {subject} -
#     select ?result where {?{subject} dbo:abstract ?result}
#   who is the mother of Michael Jordan -
#     select ?result where {<michaelJordanURI>  <hasMotherURI> ?result}


from properties import Property
from typing import List, Tuple, Dict
import logging

log = logging.getLogger('logger')


class Template:
    def __init__(self, question, query):
        self.question = question
        self.query = query


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


# these are used to generate SPARQL query templates. Questions that contain a
# {property} placeholder should use the 'property' key, as it allows for
# replacement when generating the templates
common_statements = {
    'abstract': base_query_template(statements=['<{}> dbo:abstract ?result . filter langMatches(lang(?result), "EN")']),
    'property': simple_query_template('{property}'),
    'location': simple_query_template('dbo:location'),
    'year': simple_query_template('dbo:year'),
    'month': simple_query_template('dbo:month'),
    'day': simple_query_template('dbo:day'),
    'date': simple_query_template('dbo:date'),
    'person': simple_query_template('dbo:person'),
    'ask': 'ask {{{subject} {property} {object}}}'
}

# list of question templates, combined with properties in order to produce
# the question/query pairs. In templates with the {property} placeholder, it is # replaced with a matching property based on the answer's expected range. For
# those without this placeholder, the property is conferred using the context
# of the question. For example, if the question is 'when did', we can assume
# that only properties of types related to dates would be meaningful.
# To reduce the template search space, we want to only create templates that
# make sense. Therefore, we restrict given templates to be created only for
# the properties whose datatypes are within the range of expected answers
# NOTE: that the {subject} placeholder is looked up dynamically by the system
# at execution time, replacing it with the URI of the entity if it can be found
# (template, property_type, common_type)
question_templates = [
    ('when did {subject} {property}', ['date', 'year'], None),
    ('when was {subject} {property}', ['date', 'year'], None),
    ('when was {subject}', None, ['date', 'year']),
    ('what occured at {subject}', None, ['abstract', 'location']),
    ('what occured on {subject}', None, ['abstract', 'date']),
    ('what occured in {subject}', None, ['abstract', 'date']),
    ('what year did {subject} occur', None, ['year']),
    ('what year did {subject} {property}', ['year'], None),
    ('what day did {subject} {property}', ['day'], None),
    ('what month did {subject} {property}', ['month'], None),
    ('what is {subject}', None, ['abstract']),
    ('what is {subject} {property}', [
     'object', 'string', 'number', 'date', 'year'], None),
    # ('what is {subject}\'s {property}', ['object', 'string', 'number'], None),
    # ('what was {subject}\'s {property}', ['object', 'string', 'number'], None),
    ('what is a {property} of {subject}', [
     'object', 'string', 'number'], None),
    ('what is there to {property} in {subject}', ['object', 'string'], None),
    ('where did {subject} {property}', ['object', 'string'], None),
    # ('where was {subject} {property}', ['object', 'string'], None),
    ('where was {subject} when {property}', ['object', 'string'], None),
    ('where is {subject}', None, ['location']),
    ('who is {subject}',  None, ['abstract']),
    ('who {property} the {subject}', ['object', 'string', 'date'], None),
    ('who is the {property} of {subject}', ['object', 'string'], None),
    ('does {subject} {property}', ['boolean'], None),
    ('does the {property} of {subject} {subject}', ['boolean'], None),
    ('how does {subject} work', None, ['abstract']),
    ('how does {subject} {property}', ['object', 'string'], None),
    ('what is an example of {subject}', None, ['abstract']),
    # ('in what {{}} did {subject} {property}', ['object', 'string'], None),
]


def generate_templates_from_properties(properties: Dict[str, List[Property]]) -> List[Template]:
    """
    Generate a dictionary of question/query templates, where the keys represent the datatype of the range of the answers
    """
    questions = set()

    for template, property_types, common_types in question_templates:
        if property_types != None:
            for type in property_types:
                if type not in properties:
                    continue

                for property in properties[type]:
                    try:
                        questions.add((
                            template.format(
                                subject='{e}', property=property[1]),
                            common_statements['property'].replace(
                                '{property}', '<' + property[0] + '>')
                        ))
                    except Exception as ex:
                        log.error(
                            f'Stumbled at {template}, {type}, {property}')

        elif common_types != None:
            for common_type in common_types:
                try:
                    questions.add((
                        template.format(subject='{e}'),
                        common_statements[common_type]
                    ))

                except Exception as ex:
                    log.error(
                        f'Stumbled at {template}, {common_type}')

    return list(questions)
