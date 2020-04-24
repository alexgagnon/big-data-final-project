import logging
import json
import os
from utils import get_answer

log = logging.getLogger('logger')


def run_benchmark(templates):
    """
    Compare performance of algorithm against a sample dataset
    """

    answered = 0

    with open(f'./datasets/sample-questions.json') as file:
        training_data = json.load(file)
        total = len(training_data)
        for index, question in enumerate(training_data):
            log.info(f'Testing {index +1} of {total}: {question}')
            answer = get_answer(question, templates)
            if answer != None and len(answer) > 1:
                log.info(answer)
                answered += 1
            else:
                log.info('INCORRECT\n')

        log.info(f'Answered: {answered}\nTotal: {total}')
