import json
import time

from kuda.scrapers.async_scrape import scrape_urls
from kuda.scrapers.workout.parser import parse_workout_html

BASE_WORKOUT_URL: str = (
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/"
)

start = time.time()

data = scrape_urls(
    urls=[
        f"{BASE_WORKOUT_URL}102561/54ff1aed0cf2b9e68f9ec26f",
        f"{BASE_WORKOUT_URL}coachdmurph/5bf3ec42176a3027b0ad04d8",
    ],
    html_parser=parse_workout_html,
    batch_size=10,
)

end = time.time()
print(f"Time taken: {end - start}")

with open(
    "data/workout_links/parsed/asnyc_test_run.json", "w", encoding="utf-8"
) as f:
    f.write(json.dumps(data, indent=4))
