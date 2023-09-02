import json

from deepdiff import DeepDiff

from kuda.scrapers import scrape_workout

from ..vars import WORKOUT_VARIANTS

FILE_PATH = "test/files/"


def test_scraped_links() -> None:
    """
    Test that the scraped links are the same as the ones
    in our correct test file.
    """

    with open(
        f"{FILE_PATH}tested_workout_links.json", "r", encoding="utf-8"
    ) as f:
        tested_links = json.loads(f.read())

    for index, workout in enumerate(WORKOUT_VARIANTS):
        link = workout["link"]
        print("Testing link: ", link)
        workout = scrape_workout(link)
        assert set(tested_links[index].pop("muscles_used")) == set(
            workout.pop("muscles_used")
        )
        assert DeepDiff(tested_links[index], workout) == {}
        print("Test passed!")
