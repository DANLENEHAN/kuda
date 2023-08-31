import pandas as pd
import json
from random import randint
import time
from typing import Dict

from deepdiff import DeepDiff

from workout_scraper import scrape_workout_page


def scrape_all_links() -> None:
    pdf = pd.read_csv("data/workoutlinks/full_male_workout_links.csv")
    pdf.Links = pdf.Links.apply(eval)
    links = list(pdf.Links)

    probelm_links = []
    for index, link_list in enumerate(links):
        if index <= 225:
            continue
        rand_index = randint(0, len(link_list) - 1)
        link = link_list[rand_index]
        print(f"Processing link: {rand_index} of list: {index}, link: {link}")
        try:
            scrape_workout_page(link)
        except Exception as e:
            print(e, e.__str__())
            probelm_links.append((link, e.__str__()))


TESTED_LINKS: Dict = [
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/coachdmurph/5bf3ec42176a3027b0ad04d8",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzyt/5721ad540cf2b58f38ced9d7",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzupan90/5428c1e70cf2bb28d5a57422",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzneo/5bcad0494e400527ce7156fc",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzohaib/5376f2f70cf28afcb6ce2e9a",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/-NYSE1-/4fb56f36b488e39f44f45352",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzshad/593210b4af19ce69876e7dcd",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/zzolowicz/5901402f36d69c3acb773dd4",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/12LittLebit/5a024d9fb36829286bb464e9",
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/12laynew/58097f260cf27a6fb6996c8d",
]


def test_scraped_links() -> None:
    with open("./data/scraped_data/workouts/tested_links.json", "r") as f:
        tested_links = json.loads(f.read())

    for index, link in enumerate(TESTED_LINKS):
        print("Testing link: ", link)
        workout = scrape_workout_page(link)
        assert set(tested_links[index].pop("muscles_used")) == set(
            workout.pop("muscles_used")
        )
        assert DeepDiff(tested_links[index], workout) == {}
        print("Test passed!")


def save_tested_links() -> None:
    tested_links = []
    for link in TESTED_LINKS:
        print("Processing link: ", link)
        workout = scrape_workout_page(link)
        tested_links.append(workout)

    with open("./data/scraped_data/workouts/tested_links.json", "w") as f:
        f.write(json.dumps(tested_links, indent=4))
    print("Saved!")


def scrape_single_workout(link: str):
    start = time.time()
    workout = scrape_workout_page(link)
    print(f"Time taken: {time.time() - start}")
    with open("./data/scraped_data/workouts/workout.json", "w") as f:
        f.write(json.dumps(workout, indent=4))
    return workout


scrape_single_workout(TESTED_LINKS[-1])
