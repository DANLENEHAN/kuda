import json
import os

from tests.utils.functions import dict_comparsion
from kuda.data_pipelining.highrise.file_transformers import parse_workout_tree


def test_workout_tree_parser():
    test_file_path = "tests/files/workout_links/parsed"

    with open(
        os.path.join(test_file_path, "single_workout.json"),
        "r",
        encoding="utf-8",
    ) as f:
        workout = json.load(f)
        components = parse_workout_tree(
            workouts=[workout],
        )

        assert all(
            key in components
            for key in [
                "workouts",
                "workout_components",
                "sets",
                "set_components",
            ]
        )
        assert len(components["workouts"]) == 1
        assert len(components["workout_components"]) == 10
        assert len(components["sets"]) == 29
        assert len(components["set_components"]) == 55

        workout_id = components["workouts"][0]["workout_id"]
        dict_comparsion(
            dict_a=components["workouts"][0],
            dict_b={
                "name": "Jim Stoppani's Shortcut To Shred: Day 24 - Back, Traps, Biceps",
                "created_at": "2017-11-07 00:00:00",
                "duration": 3780,
                "url": (
                    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/"
                    "12LittLebit/5a024d9fb36829286bb464e9"
                ),
                "muscles_used": (
                    "Traps;Middle Back;Shoulders;Quadriceps;"
                    "Biceps;Hamstrings;Forearms;Lats"
                ),
                "energy_level": 4,
                "self_rating": 4,
                "cardio_duration": 0,
            },
            exclude_keys=["created_by", "workout_id"],
        )

        first_workout_component_id = components["workout_components"][0][
            "workout_component_id"
        ]
        last_workout_component_id = components["workout_components"][-1][
            "workout_component_id"
        ]
        dict_comparsion(
            dict_a=components["workout_components"][0],
            dict_b={
                "workout_component_id": "21b60620-5e6a-4a2d-80e2-f87035d48115",
                "rest_time": 45,
                "created_at": "2017-11-07 00:00:00",
                "workout_id": workout_id,
            },
            exclude_keys=["workout_component_id"],
        )

        dict_comparsion(
            dict_a=components["workout_components"][-1],
            dict_b={
                "rest_time": None,
                "created_at": "2017-11-07 00:00:00",
                "workout_id": workout_id,
            },
            exclude_keys=["workout_component_id"],
        )

        first_set_id = components["sets"][0]["set_id"]
        last_set_id = components["sets"][-1]["set_id"]
        dict_comparsion(
            dict_a=components["sets"][0],
            dict_b={
                "workout_component_id": first_workout_component_id,
                "sequence": 1,
                "rest_time": 45,
                "type": "STRAIGHT_SET",
                "created_at": "2017-11-07 00:00:00",
            },
            exclude_keys=["set_id"],
        )

        dict_comparsion(
            dict_a=components["sets"][-1],
            dict_b={
                "workout_component_id": last_workout_component_id,
                "sequence": 3,
                "rest_time": None,
                "type": "SUPER_SET",
                "created_at": "2017-11-07 00:00:00",
            },
            exclude_keys=["set_id"],
        )

        dict_comparsion(
            dict_a=components["set_components"][0],
            dict_b={
                "set_id": first_set_id,
                "sequence": 1,
                "weight_metric": "seconds",
                "weight": 1,
                "reps": None,
                "rest_time": 45,
                "exercise_link": (
                    "http://www.bodybuilding.com/exercises"
                    "/detail/view/name/fast-skipping"
                ),
                "created_at": "2017-11-07 00:00:00",
            },
            exclude_keys=["set_component_id"],
        )

        dict_comparsion(
            dict_a=components["set_components"][-1],
            dict_b={
                "set_id": last_set_id,
                "sequence": 2,
                "weight_metric": None,
                "weight": None,
                "reps": 1,
                "rest_time": None,
                "exercise_link": "http://www.bodybuilding.com/exercises/detail/view/name/battling-ropes",
                "created_at": "2017-11-07 00:00:00",
            },
            exclude_keys=["set_component_id"],
        )
