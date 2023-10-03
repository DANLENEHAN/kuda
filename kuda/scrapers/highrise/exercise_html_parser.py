import re
from typing import List, Optional, TypedDict

from bs4 import BeautifulSoup, element


class Exercise(TypedDict):
    """
    Exercise data.
    """

    exercise_link: str
    exercise_name: str
    benefits: List[str]
    exercise_type: str
    main_muscle_worked: str
    equipment: str
    equipment_link: str
    level: str
    rating: Optional[str]
    instructions: List[str]


# pylint: disable=too-many-locals, anomalous-backslash-in-string
def parse_exericse_html(url: str, html: str) -> Exercise:
    """
    Parse the html of a single exercise page.
    """

    html_tree: element.Tag = BeautifulSoup(
        html,
        "lxml",
    )
    exercise: Exercise = {"exercise_link": url}  # type: ignore

    exercise_name = html_tree.find("h1", {"class": "ExHeading"})
    exercise_name = (
        exercise_name.text.strip().lower() if exercise_name else None
    )
    exercise["exercise_name"] = exercise_name

    benefits = html_tree.find("div", {"class": "ExDetail-benefits"})
    if benefits:
        benefits = benefits.find_all("li")
        benefits = [benefit.text.strip() for benefit in benefits]
    exercise["benefits"] = benefits

    # Exercise details
    exercise_detail_section = html_tree.find("ul", {"class": "bb-list--plain"})
    detail_list = exercise_detail_section.find_all("li")

    for exercise_detail in detail_list:
        if "Type:" in exercise_detail.text:
            exercise_type = exercise_detail.text
            exercise["exercise_type"] = re.sub(
                pattern="\n|Type:|\s", repl="", string=exercise_type
            ).lower()
        elif "Main Muscle Worked:" in exercise_detail.text:
            main_muscle_worked = exercise_detail.text
            exercise["main_muscle_worked"] = re.sub(
                pattern="\n|Main Muscle Worked:|\s",
                repl="",
                string=main_muscle_worked,
            ).lower()
        elif "Equipment:" in exercise_detail.text:
            equipment = exercise_detail.text
            exercise["equipment"] = re.sub(
                pattern="\n|Equipment:|\s", repl="", string=equipment
            ).lower()
            equipment_link = exercise_detail.find("a")
            exercise["equipment_link"] = (
                equipment_link["href"] if equipment_link else None
            )
        elif "Level:" in exercise_detail.text:
            level = exercise_detail.text.strip()
            exercise["level"] = re.sub(
                pattern="\n|Level:|\s", repl="", string=level
            ).lower()
        else:
            raise ValueError(f"Unexpected exercise detail: {exercise_detail}")

    rating = html_tree.find("div", {"class": "ExRating-badge"})
    exercise["rating"] = (
        re.sub(pattern="\n|Level:|\s", repl="", string=rating.text).lower()
        if rating
        else None
    )

    exercise_instructions = html_tree.find(
        "section", {"class": "ExDetail-guide"}
    )
    if exercise_instructions:
        exercise_instructions = exercise_instructions.find_all("li")
        exercise_instructions = [
            instruction.text.strip() for instruction in exercise_instructions
        ]
    exercise["instructions"] = exercise_instructions

    return exercise
