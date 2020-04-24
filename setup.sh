#!/bin/sh

set -eou pipefail

# install venv and create virtual environment
apt get install -y python3-venv
python3 -m venv venv
. venv/bin/activate

# install required dependencies
pip install -r requirements.txt
python3 -m spacy download en_core_web_lg

# download additional packages for
# mkdir -p dumps && cd dumps
# curl --output wikidata-all.json.bz2 https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2
# curl --output wikipedia-all.xml.bz2 enwiki-latest-pages-articles-multistream.xml.bz2

# run application
python3 src/rdfqa.py -h