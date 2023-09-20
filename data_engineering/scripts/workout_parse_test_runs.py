import json

import requests

from kuda.scrapers.workout.parser import parse_workout_html

broken = {
	"body": ["https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/52vizcaino/568065660cf215707caff8cb"],
	"bucket_key": "workout-data/male/age_21_25"
}


html = requests.get(broken["body"][0], timeout=20).text

workout = parse_workout_html(
    html_text=html,
    url=broken["body"][0],
)

with open("data/workout_links/parse_test.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(workout, indent=4))
