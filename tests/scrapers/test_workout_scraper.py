import json

from deepdiff import DeepDiff

from kuda.scrapers import scrape_urls
from kuda.scrapers.workout.parser import parse_workout_html
from tests.vars import WORKOUT_VARIANTS

FILE_PATH = "tests/files/workout_links"


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


def test_workout_link_html_parser() -> None:
    """
    Test that the parsed data is the same as the one
    """

    # pylint: disable=consider-using-with
    raw_html = json.load(
        open(f"{FILE_PATH}/html/workouts.json", "r", encoding="utf-8")
    )
    parsed_workouts = json.load(
        open(f"{FILE_PATH}/parsed/workouts.json", "r", encoding="utf-8")
    )

    for index, html_page in enumerate(raw_html):
        parsed_page = parse_workout_html(
            html_text=html_page, url=WORKOUT_VARIANTS[index]["link"]
        )
        assert set(parsed_page.pop("muscles_used")) == set(
            parsed_workouts[index].pop("muscles_used")
        )
        assert DeepDiff(parsed_page, parsed_workouts[index]) == {}
