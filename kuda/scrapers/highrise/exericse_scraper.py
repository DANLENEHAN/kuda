import json
import os

import pandas as pd

from kuda.scrapers import parse_exericse_html
from kuda.scrapers.async_scrape import scrape_urls

current_script_path = os.path.abspath(__file__)
current_script_path = "/".join(current_script_path.split("/")[:-1])

with open(
    os.path.join(current_script_path, "files/exercise_links.json"),
    "r",
    encoding="utf-8",
) as f:
    exercise_links = json.load(f)


print(f"Scraping {len(exercise_links)} exercise pages...")
results = scrape_urls(
    urls=exercise_links,
    html_parser=parse_exericse_html,
    batch_size=10,
)
print("Done!")

successful_results = []
failed_results = []
for res in results:
    if isinstance(res, dict):
        successful_results.append(res)
    else:
        failed_results.append(res)

df = pd.DataFrame(successful_results)
df.to_csv(
    os.path.join(current_script_path, "files/exercises.csv"), index=False
)

with open(
    os.path.join(current_script_path, "files/failed_exercises.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(failed_results, f)
