from bs4 import BeautifulSoup
import requests
import pandas as pd

properties_url = 'https://www.wikidata.org/wiki/Wikidata:Database_reports/List_of_properties/all'
page = requests.get(properties_url)
content = BeautifulSoup(page.text, 'html.parser')
table = content.find(id='bodyContent').find('table')

# read_html returns a list of dataframes, one for each 'table' element
df = pd.read_html(table.prettify(), flavor='bs4')[0]
df.to_pickle('properties.pkl')
