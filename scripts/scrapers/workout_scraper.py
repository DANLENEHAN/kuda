import re
from enum import Enum
from bs4 import BeautifulSoup, element
import requests
from typing import List, TypedDict, Tuple, Dict
from itertools import cycle


class BBSetType(Enum):
    WEIGHT_REPS = "WEIGHT/REPS"
    REPS = "REPS"
    TIME = "TIME"


class SetTypes(Enum):
    STRAIGHT_SET = "STRAIGHT_SET"
    SUPER_SET = "SUPER_SET"
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
    cardio_time: str
    rating: str
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


def scrape_workout_page(url: str) -> Workout:
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

    # Get the Workout Time (seconds) looks like "00:00" hr:min
    workout_time = html_page.find(
        "span", {"wicketpath": "logResultsPanel_workoutSummary_totalWorkoutTime"}
    ).text.strip()
    hrs, mins = workout_time.split(":")
    workout["workout_time"] = str(int(hrs) * 3600 + int(mins) * 60)

    cardio_time = html_page.find(
        "span", {"wicketpath": "logResultsPanel_workoutSummary_totalCardioTime"}
    ).text.strip()
    hrs, mins = cardio_time.split(":")
    workout["cardio_time"] = str(int(hrs) * 3600 + int(mins) * 60)

    workout_footer = html_page.find("div", {"class": "workout-footer"})
    energy_level = workout_footer.findAll("span", {"class": "battery-cell"})
    workout["energy_level"] = len(energy_level)
    rating = workout_footer.find("span", {"class": "bigRating"}).text.strip()
    workout["self_rating"] = rating

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
        if workout_component_index < len(workout_component_rests):
            workout_component["rest_time"]: str = get_rest_time(
                string=workout_component_rests[workout_component_index].text,
            )
        else:
            workout_component["rest_time"]: str = None

        # The BB.com set tags are our Set Objects
        set_tags: List[element.Tag] = exercise_details[workout_component_index].findAll(
            "div", {"class": "set"}
        )

        set_component_rests: List[element.Tag] = exercise_details[
            workout_component_index
        ].findAll("div", {"class": "set-rest"})

        exercise_tags: List[element.Tag] = exercise_overview[
            workout_component_index
        ].findAll("div", {"class": "exercise-info"})

        exercise_muscle_and_equipment = exercise_overview[
            workout_component_index
        ].findAll("ul", {"class": "muscles-and-equipment"})

        exercise_data: Dict = []
        for index, exercise_tag in enumerate(exercise_tags):
            exercise_data.append(
                {
                    "exercise_name": exercise_tag.find("h3").text,
                    "exercise_link": exercise_tag.find("a").get("href"),
                    "exercise_muscle": exercise_muscle_and_equipment[index]
                    .findAll("li")[0]
                    .find("a")
                    .text.strip(),
                    "exercise_type": exercise_muscle_and_equipment[index]
                    .findAll("li")[1]
                    .find("a")
                    .text.strip(),
                    "exercise_equipment": exercise_muscle_and_equipment[index]
                    .findAll("li")[2]
                    .find("a")
                    .text.strip(),
                }
            )
        exercise_data: Dict = cycle(exercise_data)

        # For indexing 'set' rest times. Because BB.com treats sets and set components
        # there is a 'rest_time' under each 'set' which for us is a set_component in the
        # case of a super set. See where 'total_set_components' is used below.
        total_set_components: int = 0
        for set_index, set_tag in enumerate(set_tags):
            set_: Set = Set()
            set_["set_components"]: List[SetComponent] = []
            set_["sequence"] = set_index + 1

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
            if len(set_titles) > 0 and len(set_titles) < 2:
                set_["type"] = SetTypes.STRAIGHT_SET.value
            else:
                set_["type"] = SetTypes.SUPER_SET.value

            for set_component_index in range(number_set_components):
                set_component: SetComponent = SetComponent()
                set_component["sequence"] = set_component_index + 1

                bb_set_type = set_component_titles[set_component_index].text.strip()

                # Can be a span containing dropset info e.g. "DROP 1"
                if set_component_titles[set_component_index].find("span"):
                    title_info = (
                        set_component_titles[set_component_index].find("span").text
                    )
                    # We only find out in the set components that the "set" is a drop set
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

                # Populate the set component
                set_component["weight_metric"] = weight_metric
                set_component["weight"] = weight
                set_component["reps"] = reps

                exercise = next(exercise_data)
                set_component["exercise_link"] = exercise["exercise_link"]
                set_component["exercise_name"] = exercise["exercise_name"]
                set_component["exercise_muscle"] = exercise["exercise_muscle"]
                set_component["exercise_type"] = exercise["exercise_type"]
                set_component["exercise_equipment"] = exercise["exercise_equipment"]

                rest_time: str = None
                if set_component_rests is not None:
                    # Case: <Last set Rest time>
                    # will be the rest time of the workout component
                    if set_index == len(set_tags) - 1:
                        if set_["type"] != SetTypes.SUPER_SET.value:
                            rest_time = workout_component["rest_time"]
                        else:
                            # If superset there's a bug where the first set component
                            # of the last superset doesn't have a rest time.
                            if set_component_index < (number_set_components - 1):
                                # Not last set component
                                rest_time = None
                            elif set_component_index == (number_set_components - 1):
                                # Last set component
                                rest_time = workout_component["rest_time"]
                    else:
                        # Case: <Set Rest time>
                        # If superset we must index by the total number of set components
                        if set_["type"] != SetTypes.SUPER_SET.value:
                            rest_time = get_rest_time(
                                string=set_component_rests[set_index].text
                            )
                        else:
                            rest_time = get_rest_time(
                                string=set_component_rests[total_set_components].text
                            )

                # Case: <Set Rest time>
                if (
                    set_["type"] != SetTypes.DROP_SET.value
                    # Last set component
                    or (
                        set_["type"] == SetTypes.DROP_SET.value
                        and set_component_index == number_set_components - 1
                    )
                ):
                    set_component["rest_time"] = rest_time
                else:
                    # Case: <Dropset Rest time>
                    # Annoying case where we only find out about the drop
                    # set in the second set component. So we must retroactively
                    # remove the rest time from the first set component
                    if set_component_index == 1:
                        set_["set_components"][0]["rest_time"] = "0"
                    set_component["rest_time"] = "0"

                set_["set_components"].append(set_component)
                set_["rest_time"] = set_component["rest_time"]
                total_set_components += 1

            workout_component["sets"].append(set_)
        workout["workout_components"].append(workout_component)
    return workout


import time

start = time.time()
workout = scrape_workout_page(url1)
print(f"Time taken: {time.time() - start}")

import json

with open("workout.json", "w") as f:
    f.write(json.dumps(workout, indent=4))
