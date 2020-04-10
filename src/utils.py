import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

base_url = 'https://google.com/search?q='


# DOESN'T WORK, Google has restricted their search api to behind a key wall
def google(search_term: str, exact=True, count_only=True) -> int:
    search_term = f'"{quote_plus(search_term)}"'
    print(search_term)
    response = requests.get(f'{base_url}{search_term}')
    with open("google.html", "w") as f:
        f.write(response.text)
    content = BeautifulSoup(response.text, 'html.parser')
    stats = content.find(id='result-stats').text
    stats.replace(',', '')
    count = [int(s) for s in stats.split() if s.isdigit()]
    print(count)
    return count[0]


google("hello there")
