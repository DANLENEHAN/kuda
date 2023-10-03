import json

from deepdiff import DeepDiff

from kuda.scrapers import parse_workout_html, scrape_urls
from tests.scrapers import FILE_PATH
from tests.vars import WORKOUT_VARIANTS


def test_workout_scraper() -> None:
    """
    Test that the scraped links are the same as the ones
    in our correct test file.
    """

    with open(f"{FILE_PATH}/parsed/workouts.json", "r", encoding="utf-8") as f:
        tested_links = json.loads(f.read())

    for index, workout in enumerate(WORKOUT_VARIANTS[:2]):
        link = workout["link"]
        print("Testing link: ", link)
        response = scrape_urls(urls=[link], html_parser=parse_workout_html)[0]

        if isinstance(response, str):
            assert response == link
            print("Test passed!")
        else:
            assert set(tested_links[index].pop("muscles_used")) == set(
                response.pop("muscles_used")
            )
            assert DeepDiff(tested_links[index], response) == {}
            print("Test passed!")
