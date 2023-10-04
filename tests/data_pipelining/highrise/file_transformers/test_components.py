from kuda.data_pipelining.highrise.file_transformers import functions
from kuda.data_pipelining.highrise.file_transformers.components import (
    SetComponentParser,
    SetParser,
    WorkoutComponentParser,
    WorkoutParser,
)
from tests.utils.functions import dict_comparsion
from tests.utils.test_objects import (
    HIGHRISE_SCRAPED_WORKOUT,
    HIGHRISE_SCRAPED_WORKOUT_COMPONENT,
    HIGHRISE_SCRAPED_WORKOUT_SET,
    HIGHRISE_SCRAPED_WORKOUT_SET_COMPONENT,
)


def test_workout_parser():
    """
    Test the Scraped Workout Parser
    is working as expected.
    """

    workout_parser = WorkoutParser(HIGHRISE_SCRAPED_WORKOUT)
    dict_comparsion(
        dict_a=workout_parser.__dict__,
        dict_b={
            "name": "Bi's,Tri's,Cardio!",
            "created_at": "2017-09-16 00:00:00",
            "duration": 4680,
            "url": (
                "https://bodyspace.bodybuilding.com/"
                "workouts/viewworkoutlog/Bldblu/"
                "59bd3ba1af19ce019c5216a5"
            ),
            "muscles_used": (
                "Chest;Abdominals;Quadriceps;"
                "Biceps;Lats;Forearms;Triceps;Traps"
            ),
            "energy_level": 4,
            "self_rating": 7,
            "cardio_duration": 0,
        },
        exclude_keys=["workout_id", "created_by"],
    )
    assert (
        functions.decrypt_string(workout_parser.created_by)
        == HIGHRISE_SCRAPED_WORKOUT["username"]
    )
    assert workout_parser.workout_id is not None


def test_workout_component_parser():
    """
    Test the Scraped Workout Component Parser
    is working as expected.
    """

    workout_component_parser = WorkoutComponentParser(
        raw_dict=HIGHRISE_SCRAPED_WORKOUT_COMPONENT,
    )
    dict_comparsion(
        dict_a=workout_component_parser.__dict__,
        dict_b={
            "workout_id": 1,
            "sequence": 1,
            "rest_time": 2,
            "created_at": "2017-09-16 00:00:00",
        },
        exclude_keys=["workout_component_id"],
    )
    assert workout_component_parser.workout_component_id is not None


def test_set_parser():
    """
    Test the Scraped Set Parser
    is working as expected.
    """

    set_parser = SetParser(
        raw_dict=HIGHRISE_SCRAPED_WORKOUT_SET,
    )
    dict_comparsion(
        dict_a=set_parser.__dict__,
        dict_b={
            "workout_component_id": 1,
            "sequence": 1,
            "rest_time": 0,
            "created_at": "2017-09-16 00:00:00",
            "type": "STRAIGHT_SET",
        },
        exclude_keys=["set_id"],
    )
    assert set_parser.set_id is not None


def test_set_component_parser():
    """
    Test the Scraped Set Component Parser
    is working as expected.
    """

    set_component_parser = SetComponentParser(
        raw_dict=HIGHRISE_SCRAPED_WORKOUT_SET_COMPONENT,
    )

    dict_comparsion(
        dict_a=set_component_parser.__dict__,
        dict_b={
            "set_id": 1,
            "created_at": "2017-09-16 00:00:00",
            "sequence": 1,
            "weight_metric": "lbs",
            "weight": 40.0,
            "reps": 10,
            "rest_time": 0,
            "exercise_link": (
                "http://www.bodybuilding.com/"
                "exercises/detail/view/name/"
                "alternate-incline-dumbbell-curl"
            ),
        },
        exclude_keys=["set_component_id"],
    )
    assert set_component_parser.set_component_id is not None
