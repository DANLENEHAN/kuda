import datetime as dt
from typing import Dict
from uuid import uuid4

from kuda.data_pipelining.highrise.file_transformers import functions


# pylint: disable=too-many-instance-attributes
class WorkoutParser:
    """
    Parses a workout from the raw
    scraped highrise data.
    """

    def __init__(self, raw_dict: Dict) -> None:
        # ORM fields
        self.workout_id = str(uuid4())
        self.name = raw_dict["name"]
        self.created_at = self.parse_created_at(
            raw_dict["month"], raw_dict["month_date"], raw_dict["year"]
        )
        self.duration = functions.parse_int(raw_dict["duration"])
        self.created_by = functions.encrypt_string(
            raw_dict["username"]
        ).decode()

        # Non ORM fields
        self.url = raw_dict["url"]
        self.muscles_used = ";".join(raw_dict["muscles_used"])
        self.energy_level = raw_dict["energy_level"]  # already an int
        self.self_rating = functions.parse_int(raw_dict["self_rating"])
        self.cardio_duration = functions.parse_int(raw_dict["cardio_duration"])

    def parse_created_at(self, month: str, month_date: str, year: str) -> str:
        """
        Combined the three scraped date fields into a single
        date string in the PostgreSQL format.
        Args:
                month (str): The month in string format
                month_date (str): The date of the month
                year (str): The year
        Returns:
                str: The date in the PostgreSQL format
                        'YYYY-MM-DD HH:MM:SS'
        """
        month_num = functions.MONTH_STR_TO_NUM[month.lower()]
        date_string = f"{month_date}{month_num}{year}"
        return dt.datetime.strptime(date_string, "%d%m%Y").strftime(
            "%Y-%m-%d %H:%M:%S"
        )


class WorkoutComponentParser:
    """
    Parses a workout component from the raw
    scraped highrise data.
    """

    def __init__(self, raw_dict: Dict) -> None:
        # ORM fields
        self.workout_component_id = str(uuid4())
        self.rest_time = functions.parse_int(raw_dict.get("rest_time"))


class SetParser:
    """
    Parses a set from the raw
    scraped highrise data.
    """

    def __init__(self, raw_dict: Dict) -> None:
        # ORM fields
        self.set_id = str(uuid4())
        self.sequence = raw_dict["sequence"]  # already an int
        self.rest_time = functions.parse_int(raw_dict.get("rest_time"))
        # Non ORM fields
        self.type = raw_dict["type"]


class SetComponentParser:
    """
    Parses a set component from the raw
    scraped highrise data.
    """

    def __init__(self, raw_dict: Dict) -> None:
        # ORM fields
        self.set_component_id = str(uuid4())
        self.sequence = raw_dict.get("sequence")
        self.weight_metric = raw_dict["weight_metric"]
        self.weight = functions.parse_int(raw_dict.get("weight"))
        self.reps = functions.parse_int(raw_dict.get("reps"))
        self.rest_time = functions.parse_int(raw_dict.get("rest_time"))
        self.exercise_link = raw_dict["exercise_link"]
