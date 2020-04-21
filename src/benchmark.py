import logging
import json
import os
from utils import get_answer, get_answer_property

log = logging.getLogger('logger')


def run_benchmark(templates):
    """
    Compare performance of algorithm against a sample dataset
    """

    correct = 0

    with open('./datasets/SimpleDBpediaQA-train.json') as file:
        training_data = json.load(file)['Questions']
        total = len(training_data)
        for index, question in enumerate(training_data):
            query = question['Query']
            answer_property_uris = [x['Predicate']
                                    for x in question['PredicateList']]
            log.info(f'Testing {index +1} of {total}: {query}')
            answer = get_answer_property(query, templates)
            if answer != None and len(set(answer) & set(answer_property_uris)):
                log.info(
                    f'Correct answer: \n{answer}\n{answer_property_uris}')
                correct += 1
            else:
                log.info('Incorrect')

        return (correct, total)
