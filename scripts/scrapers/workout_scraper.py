import re
from enum import Enum
from bs4 import BeautifulSoup, element
import requests
from typing import List, TypedDict, Tuple


class BBSetType(Enum):
    WEIGHT_REPS = "WEIGHT/REPS"
    REPS = "REPS"
    TIME = "TIME"


class SetTypes(Enum):
    STRAIGHT_SET = "STRAIGHT_SET"
    SUPER_SET = "SUPER_SET"
    CARDIO = "CARDIO"
    DROP_SET = "DROP_SET"


class SetComponent(TypedDict):
    sequence: int
    weight_metric: str
    weight: str
    reps: str
    rest_time: str
    exercise_name: str
    exercise_link: str


class Set(TypedDict):
    type: SetTypes
    sequence: int
    set_sequence: int
    rest_time: str
    set_components: List[SetComponent]


class WorkoutComponent(TypedDict):
    sequence: int
    rest_time: str
    sets: List[Set]


class Workout(TypedDict):
    name: str
    muscles_used: List[str]
    workout_time: str
    workout_components: List[WorkoutComponent]


request_agent = "Mozilla/5.0 Chrome/47.0.2526.106 Safari/537.36"
url1 = "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/coachdmurph/5bf3ec42176a3027b0ad04d8"


def get_rest_time(string: str) -> str:
    if string is None:
        return None
    string = re.sub(
        ("Rest Between Exercises|" "Rest Between Sets|\s|\n"),
        "",
        string,
    ).lower()
    min = string.split("min")[0]
    secs = string.split("min")[1].split("sec")[0]
    return str(int(min) * 60 + int(secs))


def get_weight_reps(string: str) -> Tuple[str, str, str]:
    if string is None:
        return None
    string = string.strip().replace("\n", "").lower()
    weight, reps = string.split("x")

    if "lbs" in weight:
        weight_metric = "lbs"
        weight = re.sub("lbs|\.", "", weight)
    elif "kg" in weight:
        weight_metric = "kg"
        weight = re.sub("kg|\.", "", weight)
    else:
        raise ValueError("Weight Metric not found")

    reps = re.sub("reps|\.", "", reps)

    return (weight_metric, weight, reps)


def scrape_workout_page(url: str):
    html_page: element.Tag = BeautifulSoup(
        requests.get(url, headers={"User-Agent": request_agent}).text, "lxml"
    )
    workout: Workout = dict()

    # Get the Workout Name
    workout_name: element.Tag = html_page.find(
        "div", {"class": "rowSectionHeader"}
    ).text
    workout["name"] = workout_name

    # Get the Muslces worked according to the App
    muscles_used_tag: element.Tag = html_page.find(
        "div", {"class": "musclesWorked"}
    ).find("span", {"class", "value"})
    muscles_used: List[str] = [m.strip() for m in muscles_used_tag.text.split(",")]
    workout["muscles_used"] = muscles_used

    # Get the Workout Time
    workout_time = html_page.find(
        "span", {"wicketpath": "logResultsPanel_workoutSummary_totalWorkoutTime"}
    ).text.strip()
    workout["workout_time"] = workout_time

    # From exercise overiew we want the Name and Link to the exercise page.
    exercise_overview: List[element.Tag] = html_page.findAll(
        "div", {"class": "exercise-overview"}
    )

    # Exercise Details contains the sets and reps, weight, rest time etc.
    exercise_details: List[element.Tag] = html_page.findAll(
        "div", {"class": "exercise-details"}
    )

    workout_component_rests: List[element.Tag] = html_page.findAll(
        "div", {"class": "exercise-rest"}
    )

    # The exercise BB.com details/overview sections are our Workout Components
    number_workout_components: int = len(exercise_overview)

    workout["workout_components"]: List[WorkoutComponent] = []
    for workout_component_index in range(number_workout_components):
        workout_component: WorkoutComponent = WorkoutComponent()
        workout_component["sequence"]: int = workout_component_index + 1
        workout_component["sets"]: List[Set] = []
        workout_component["rest_time"]: str = get_rest_time(
            string=workout_component_rests[workout_component_index].text,
        )

        # The BB.com set tags are our Set Objects
        set_tags: List[element.Tag] = exercise_details[workout_component_index].findAll(
            "div", {"class": "set"}
        )

        set_rests: List[element.Tag] = exercise_details[
            workout_component_index
        ].findAll("div", {"class": "set-rest"})

        exercise_tags: List[element.Tag] = exercise_overview[
            workout_component_index
        ].findAll("div", {"class": "exercise-info"})

        for set_index, set_tag in enumerate(set_tags):
            set_: Set = Set()
            set_["set_components"]: List[SetComponent] = []
            set_["sequence"] = set_index + 1

            if set_rests:
                if set_index == len(set_rests):
                    set_["rest_time"] = workout_component["rest_time"]
                else:
                    set_["rest_time"] = get_rest_time(string=set_rests[set_index].text)

            # Our Set components are within the set tags
            # For a straight set there will be one set component
            # For a super set there will be more than one

            # Will be more than one if it's a super set. If exercise
            # name isn't here it's also indicative of a Straight, Cardio, Dropset
            set_titles: List[element.Tag] = set_tag.findAll(
                "div", {"class": "set-title"}
            )

            set_component_titles: List[element.Tag] = set_tag.findAll(
                "label", {"class": "left-label"}
            )
            set_component_performances: List[element.Tag] = set_tag.findAll(
                "div", {"class": "inputWrapper"}
            )

            number_set_components: int = len(set_component_titles)

            # Look for more cases than the below
            set_["type"] = (
                SetTypes.STRAIGHT_SET.value
                if len(set_titles) == 1
                else SetTypes.SUPER_SET.value
            )

            for set_component_index in range(number_set_components):
                set_component: SetComponent = SetComponent()
                set_component["sequence"] = set_component_index + 1

                bb_set_type = set_component_titles[set_component_index].text.strip()

                # Can be a span containing dropset info e.g. "DROP 1"
                if set_component_titles[set_component_index].find("span"):
                    title_info = (
                        set_component_titles[set_component_index].find("span").text
                    )
                    if "drop" in title_info.lower():
                        set_["type"] = SetTypes.DROP_SET.value

                if (
                    bb_set_type == BBSetType.WEIGHT_REPS.value
                    or set_["type"] == SetTypes.DROP_SET.value
                ):
                    weight_metric, weight, reps = get_weight_reps(
                        set_component_performances[set_component_index].text
                    )
                elif bb_set_type == BBSetType.TIME.value:
                    weight_metric = "seconds"
                    time_string = (
                        set_component_performances[set_component_index]
                        .text.strip()
                        .replace("\n", "")
                    )
                    hrs, mins, secs = time_string.split(":")
                    weight = str(
                        int(hrs.replace("hr", "")) * 3600
                        + int(mins.replace("min", "")) * 60
                        + int(secs.replace("sec", ""))
                    )
                    reps = None

                set_component["weight_metric"] = weight_metric
                set_component["weight"] = weight
                set_component["reps"] = reps

                if set_["type"] != SetTypes.SUPER_SET:
                    set_component["exercise_link"] = (
                        exercise_tags[0].find("a").get("href")
                    )
                    set_component["exercise_name"] = exercise_tags[0].find("h3").text
                else:
                    print("do something here")

                set_["set_components"].append(set_component)
            workout_component["sets"].append(set_)
        workout["workout_components"].append(workout_component)


scrape_workout_page(url1)
