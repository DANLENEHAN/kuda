from pprint import pprint

import requests

from kuda.scrapers import parse_exericse_html

url = "https://www.bodybuilding.com/exercises/pistol-squat"
html = requests.get(url).text

result = parse_exericse_html(url, html)

pprint(result)
