import re
from enum import Enum
from bs4 import BeautifulSoup, element
import requests
from typing import List, TypedDict, Tuple, Dict, Optional
from itertools import cycle


class BBSetType(Enum):
    WEIGHT_REPS = "WEIGHT/REPS"
    REPS = "REPS"
    TIME = "TIME"
    WEIGHT = "WEIGHT"
    # HEART_RATE = "HEARTRATE"


class SetTypes(Enum):
    STRAIGHT_SET = "STRAIGHT_SET"
    SUPER_SET = "SUPER_SET"
    DROP_SET = "DROP_SET"


class SetComponent(TypedDict):
    sequence: int
    weight_metric: str
    weight: str
    target: str
    reps: str
    rest_time: str
    exercise_name: str
    exercise_link: str


class Set(TypedDict):
    type: SetTypes
    sequence: int
    rest_time: str
    set_components: List[SetComponent]


class WorkoutComponent(TypedDict):
    sequence: int
    rest_time: str
    sets: List[Set]


class Workout(TypedDict):
    created_by: str
    name: str
    muscles_used: List[str]
    duration: str
    cardio_duration: str
    rating: str
    workout_components: List[WorkoutComponent]
    username: str


request_agent = "Mozilla/5.0 Chrome/47.0.2526.106 Safari/537.36"


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


def get_weight_reps(set_component_performance: element.Tag) -> Tuple[str, str, str]:
    string = set_component_performance.text
    if string is None:
        return None
    string = string.strip().replace("\n", "").lower()

    weight_reps = string.split("x")

    # BBSetType WEIGHT/REPS can also be the same
    # structure as REPS amazingly :(
    if len(weight_reps) == 1:
        reps = weight_reps[0]
        weight = None
        weight_metric = None
    elif len(weight_reps) == 2:
        weight, reps = weight_reps
    else:
        raise ValueError("Weight and Reps not found")

    if weight:
        if "lbs" in weight:
            weight_metric = "lbs"
            weight = re.sub("lbs.", "", weight)
        elif "kg" in weight:
            weight_metric = "kg"
            weight = re.sub("kg.", "", weight)
        else:
            raise ValueError("Weight Metric not found")

    reps = re.sub("reps|\.", "", reps)

    return (weight_metric, weight, reps)


def get_energy_level(workout_footer: element.Tag) -> int:
    if workout_footer.find("div", {"class": "high"}):
        return 4
    elif workout_footer.find("div", {"class": "mid-high"}):
        return 3
    elif workout_footer.find("div", {"class": "mid-low"}):
        return 2
    elif workout_footer.find("div", {"class": "low"}):
        return 1
    else:
        raise ValueError("Energy Level not found")


def handle_double_set_component(
    set_component_titles: List[element.Tag],
    set_component_performances: List[element.Tag],
    exercise: Dict,
    handle_type: str,
) -> SetComponent:
    set_component: SetComponent = SetComponent()

    set_component["exercise_link"] = exercise["exercise_link"]
    set_component["exercise_name"] = exercise["exercise_name"]
    set_component["exercise_muscle"] = exercise["exercise_muscle"]
    set_component["exercise_type"] = exercise["exercise_type"]
    set_component["exercise_equipment"] = exercise["exercise_equipment"]

    for index, title in enumerate(set_component_titles):
        raw_title = title.text

        if (
            raw_title.strip().replace("\n", "").lower() == "time"
            and handle_type == "cardio"
        ):
            performance = (
                set_component_performances[index].text.strip().replace("\n", "")
            )
            performance = re.sub("hr|min|sec", "", performance)
            hrs, mins, secs = performance.split(":")
            weight = str(
                int(hrs.replace("hr", "")) * 3600
                + int(mins.replace("min", "")) * 60
                + int(secs.replace("sec", ""))
            )
            weight_metric = "seconds"
            reps = None
            target = None
            break
        else:
            if handle_type == "weight":
                bb_set_type, target = get_bb_set_type_and_target(raw_title)
                if bb_set_type == BBSetType.WEIGHT_REPS.value:
                    weight_metric, weight, reps = get_weight_reps(
                        set_component_performances[index]
                    )
                    break
                elif bb_set_type == BBSetType.REPS.value:
                    string = (
                        set_component_performances[index]
                        .text.strip()
                        .replace("\n", "")
                        .lower()
                    )
                    weight_metric = None  # Could be "bodyweight"
                    weight = None
                    reps = re.sub("reps|\.", "", string)
                    break
                elif bb_set_type == BBSetType.WEIGHT.value:
                    string = (
                        set_component_performances[index]
                        .text.strip()
                        .replace("\n", "")
                        .lower()
                    )
                    if "lbs" in string:
                        weight_metric = "lbs"
                        weight = re.sub("lbs.", "", string)
                    elif "kg" in string:
                        weight_metric = "kg"
                        weight = re.sub("kg.", "", string)
                    reps = None
                    break
                elif bb_set_type == BBSetType.TIME.value:
                    weight_metric = "seconds"
                    time_string = (
                        set_component_performances[index].text.strip().replace("\n", "")
                    )
                    hrs, mins, secs = time_string.split(":")
                    weight = str(
                        int(hrs.replace("hr", "")) * 3600
                        + int(mins.replace("min", "")) * 60
                        + int(secs.replace("sec", ""))
                    )
                    reps = None
                    break
                else:
                    raise ValueError("BBSetType not found")

            else:
                continue

    set_component["weight_metric"] = weight_metric
    set_component["weight"] = weight
    set_component["reps"] = reps
    set_component["target"] = target

    rest_time = find_rest_for_set_component(
        set_title=set_component_titles[-1],
        set_type=SetTypes.STRAIGHT_SET.value,
    )
    set_component["rest_time"] = rest_time
    return set_component


def get_bb_set_type_and_target(
    set_component_title: str,
) -> Tuple[str, Optional[str]]:
    atts: List[str] = (
        set_component_title.strip().replace(" ", "").replace("\n\n", "-").split("-")
    )
    bb_set_type = atts[0].replace(":", "")
    target_string = None
    if len(atts) > 1:
        target_string = (
            atts[1].lower().replace("target", "").replace("reps", "").strip()
        )

    if target_string:
        if "lbs" in target_string:
            target_string = re.sub("lbs.", "", target_string)
        elif "kg" in target_string:
            target_string = re.sub("kg.", "", target_string)

        # Can be '00:02:00-00:03:00'
        if "-" in target_string:
            target_string = target_string.split("-")[0]
        if "to" in target_string:
            target_string = target_string.split("to")[0]

        if ":" in target_string:
            # Can be "TARGET: 00:00:00"
            components = target_string.split(":")
            if len(components) == 3:
                hrs, mins, secs = components
                target_string = str(int(hrs) * 3600 + int(mins) * 60 + int(secs))
            elif len(components) == 4:
                _, hrs, mins, secs = components
                target_string = str(int(hrs) * 3600 + int(mins) * 60 + int(secs))
            else:
                raise ValueError("Target string not found")
    return bb_set_type, target_string


def find_rest_for_set_component(set_title: element.Tag, set_type: str) -> str:
    set_row = set_title.find_parent()
    if set_type == SetTypes.SUPER_SET.value:
        while "set-body" not in set_row.get("class"):
            set_row = set_row.find_parent()
    else:
        while "set" not in set_row.get("class"):
            set_row = set_row.find_parent()

    divs = set_row.find_next_siblings("div")
    for div in divs:
        if "set-body" in div.get("class"):
            return None
        if "set-rest" in div.get("class"):
            return get_rest_time(div.text)


def scrape_workout_page(url: str) -> Workout:
    username = url.split("viewworkoutlog")[1].split("/")[1]
    html_page: element.Tag = BeautifulSoup(
        requests.get(url, headers={"User-Agent": request_agent}).text, "lxml"
    )
    workout: Workout = dict()

    # Get the Workout Name
    workout_name: element.Tag = html_page.find(
        "div", {"class": "rowSectionHeader"}
    ).text
    workout["name"] = workout_name
    workout["username"] = username

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
    workout["duration"] = str(int(hrs) * 3600 + int(mins) * 60)

    cardio_time = html_page.find(
        "span", {"wicketpath": "logResultsPanel_workoutSummary_totalCardioTime"}
    ).text.strip()
    hrs, mins = cardio_time.split(":")
    workout["cardio_duration"] = str(int(hrs) * 3600 + int(mins) * 60)

    workout_footer = html_page.find("div", {"class": "workout-footer"})
    workout["energy_level"] = get_energy_level(workout_footer)
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

        # Set with no data (Not completed)
        if len(set_tags) == 0:
            continue

        exercise_tags: List[element.Tag] = exercise_overview[
            workout_component_index
        ].findAll("div", {"class": "exercise-info"})

        exercise_muscle_and_equipment = exercise_overview[
            workout_component_index
        ].findAll("ul", {"class": "muscles-and-equipment"})

        exercise_data: Dict = []
        for index, exercise_tag in enumerate(exercise_tags):
            muscle = exercise_muscle_and_equipment[index].findAll("li")[0].find("a")
            exercise_type = (
                exercise_muscle_and_equipment[index].findAll("li")[1].find("a")
            )
            exercise_equipment = (
                exercise_muscle_and_equipment[index].findAll("li")[2].find("a")
            )
            exercise_link = exercise_tag.find("p", {"class": "exercise-nav"}).find("a")
            exercise_data.append(
                {
                    "exercise_name": exercise_tag.find("h3").text,
                    "exercise_link": exercise_link.get("href")
                    if exercise_link is not None
                    else None,
                    "exercise_muscle": muscle.text.strip()
                    if muscle is not None
                    else None,
                    "exercise_type": exercise_type.text.strip()
                    if exercise_type is not None
                    else None,
                    "exercise_equipment": exercise_equipment.text.strip()
                    if exercise_equipment
                    else None,
                }
            )
        exercise_data: Dict = cycle(exercise_data)

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

            set_bodies: List[element.Tag] = set_tag.findAll(
                "div", {"class": "set-body"}
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
                if "Cardio" in set_titles[0].text:
                    if len(set_component_titles) == 1:
                        pass
                    # complicated cardio
                    else:
                        set_["set_components"].append(
                            handle_double_set_component(
                                set_component_titles=set_component_titles,
                                set_component_performances=set_component_performances,
                                exercise=next(exercise_data),
                                handle_type="cardio",
                            )
                        )
                        workout_component["sets"].append(set_)
                        continue
            else:
                set_["type"] = SetTypes.SUPER_SET.value

            for set_component_index in range(number_set_components):
                if (
                    set_component_index < len(set_bodies)
                    and len(
                        set_bodies[set_component_index].findAll(
                            "div", {"class": "set-row"}
                        )
                    )
                    > 1
                ):
                    if (
                        "drop" not in set_component_titles[0].text.lower()
                        and "drop" not in set_component_titles[1].text.lower()
                    ):
                        set_["set_components"].append(
                            handle_double_set_component(
                                set_component_titles=set_component_titles
                                if len(exercise_tags) == 1
                                else set_component_titles[set_component_index:],
                                set_component_performances=set_component_performances
                                if len(exercise_tags) == 1
                                else set_component_performances[set_component_index:],
                                exercise=next(exercise_data),
                                handle_type="weight",
                            )
                        )
                        # workout_component["sets"].append(set_)
                        break

                set_component: SetComponent = SetComponent()
                set_component["sequence"] = set_component_index + 1

                # The set component type here is interesting
                # It can also give a target. e.g. "TARGET 300 REPS"
                # Some users don't fill in completed reps and weight
                # so we'll track this in case it's useful
                bb_set_type, target = get_bb_set_type_and_target(
                    set_component_title=set_component_titles[set_component_index].text
                )

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
                        set_component_performances[set_component_index]
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
                elif bb_set_type == BBSetType.REPS.value:
                    string = (
                        set_component_performances[set_component_index]
                        .text.strip()
                        .replace("\n", "")
                        .lower()
                    )
                    weight_metric = None  # Could be "bodyweight"
                    weight = None
                    reps = re.sub("reps|\.", "", string)
                elif bb_set_type == BBSetType.WEIGHT.value:
                    string = (
                        set_component_performances[index]
                        .text.strip()
                        .replace("\n", "")
                        .lower()
                    )
                    if "lbs" in string:
                        weight_metric = "lbs"
                        weight = re.sub("lbs.", "", string)
                    elif "kg" in string:
                        weight_metric = "kg"
                        weight = re.sub("kg.", "", string)
                    reps = None
                else:
                    raise ValueError("BBSetType not found")

                # Populate the set component
                set_component["weight_metric"] = weight_metric
                set_component["weight"] = weight
                set_component["reps"] = reps

                if target is not None:
                    set_component["target"] = target

                exercise = next(exercise_data)
                set_component["exercise_link"] = exercise["exercise_link"]
                set_component["exercise_name"] = exercise["exercise_name"]
                set_component["exercise_muscle"] = exercise["exercise_muscle"]
                set_component["exercise_type"] = exercise["exercise_type"]
                set_component["exercise_equipment"] = exercise["exercise_equipment"]

                # Finding the rest time for the set component
                rest_time = find_rest_for_set_component(
                    set_title=set_component_titles[set_component_index],
                    set_type=set_["type"],
                )

                # print(rest_time)

                if set_["type"] == SetTypes.DROP_SET.value:
                    # Last set component in a drop set should take the rest time of the set
                    if set_component_index == number_set_components - 1:
                        set_component["rest_time"] = rest_time
                    else:
                        set_component["rest_time"] = "0"
                        if set_component_index == 1:
                            # We only know if a set is a drop set in the second set component
                            set_["set_components"][0]["rest_time"] = "0"
                else:
                    set_component["rest_time"] = rest_time

                if (
                    set_index == len(set_tags) - 1
                    and set_component_index == number_set_components - 1
                ):
                    # Last set in a workout component should take the rest time of the workout component
                    set_component["rest_time"] = workout_component["rest_time"]

                set_["set_components"].append(set_component)
                set_["rest_time"] = set_component["rest_time"]
            workout_component["sets"].append(set_)
        workout["workout_components"].append(workout_component)
    return workout
