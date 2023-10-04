import json

from deepdiff import DeepDiff

from kuda.scrapers import parse_workout_html
from tests.scrapers import FILE_PATH
from tests.vars import WORKOUT_VARIANTS


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
        assert DeepDiff(parsed_workouts[index], parsed_page) == {}
