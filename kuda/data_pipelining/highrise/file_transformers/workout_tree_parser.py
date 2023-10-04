from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, TypedDict, Union

from kuda.data_pipelining.highrise.file_transformers.components import (
    SetComponentParser,
    SetParser,
    WorkoutComponentParser,
    WorkoutParser,
)


class WorkoutTreeLevels(Enum):
    """
    Enums denoting the workout
    tree level names.
    """

    workouts = "workouts"
    workout_components = "workout_components"
    sets = "sets"
    set_components = "set_components"


class WorkoutTreeComponentPrimaryKeys(Enum):
    """
    Enums denoting the workout tree's
    component primary keys.
    """

    workout = "workout_id"
    workout_component = "workout_component_id"
    set = "set_id"
    set_component = "set_component_id"


class TreeLevelMap(TypedDict):
    """
    Dictionary for traversing and storing
    the workout tree levels.
    """

    parser: Union[
        type[WorkoutParser],
        type[WorkoutComponentParser],
        type[SetParser],
        type[SetComponentParser],
    ]
    primary_key: WorkoutTreeComponentPrimaryKeys
    components: List
    child_key: Optional[WorkoutTreeLevels]


TREE_TRAVERSE_MAP = {
    WorkoutTreeLevels.workouts.value: TreeLevelMap(
        {
            "parser": WorkoutParser,
            "primary_key": WorkoutTreeComponentPrimaryKeys.workout,
            "components": [],
            "child_key": WorkoutTreeLevels.workout_components,
        }
    ),
    WorkoutTreeLevels.workout_components.value: TreeLevelMap(
        {
            "parser": WorkoutComponentParser,
            "primary_key": WorkoutTreeComponentPrimaryKeys.workout_component,
            "components": [],
            "child_key": WorkoutTreeLevels.sets,
        }
    ),
    WorkoutTreeLevels.sets.value: TreeLevelMap(
        {
            "parser": SetParser,
            "primary_key": WorkoutTreeComponentPrimaryKeys.set,
            "components": [],
            "child_key": WorkoutTreeLevels.set_components,
        }
    ),
    WorkoutTreeLevels.set_components.value: TreeLevelMap(
        {
            "parser": SetComponentParser,
            "primary_key": WorkoutTreeComponentPrimaryKeys.set_component,
            "components": [],
            "child_key": None,
        }
    ),
}


def parse_workout_tree_level(
    nodes: List,
    level_name: str,
    components: Dict[str, List],
    foreign_key: Optional[Dict] = None,
    created_at: Optional[str] = None,
) -> Dict[str, List]:
    """
    Function for traversing the Workout Tree
    and storing all it's levels in seperate
    list whilst maintain the primary:foreign
    key linkage.
    """

    for node in nodes:
        level_info = TREE_TRAVERSE_MAP[level_name]
        parsed_node = level_info["parser"](node).__dict__
        child_key = level_info["child_key"]
        primary_key = level_info["primary_key"].value

        if level_name == WorkoutTreeLevels.workouts.value:
            created_at = parsed_node["created_at"]
        else:
            parsed_node["created_at"] = created_at

        if foreign_key:
            parsed_node.update(foreign_key)

        components[level_name].append(parsed_node)

        if child_key:
            parse_workout_tree_level(
                nodes=node[child_key.value],
                level_name=child_key.value,
                components=components,
                created_at=created_at,
                foreign_key={primary_key: parsed_node[primary_key]},
            )

    return components


def parse_workout_tree(workouts: List[Dict]):
    components: Dict[str, List] = defaultdict(list)

    parse_workout_tree_level(
        nodes=workouts,
        level_name=WorkoutTreeLevels.workouts.value,
        components=components,
    )

    return components
