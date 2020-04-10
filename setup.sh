#!/bin/sh

set -eou pipefail

# install venv and create virtual environment
apt get install -y python3-venv
python3 -m venv venv
. venv/bin/activate

# install required dependencies
pip install -r requirements.txt
python3 -m spacy download en

# run application
python3 src/rdfqa.py