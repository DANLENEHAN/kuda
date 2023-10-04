from typing import Dict, List, Optional, TypedDict, Union

from kuda.data_pipelining.highrise.file_transformers.components import (
    SetComponentParser,
    SetParser,
    WorkoutComponentParser,
    WorkoutParser,
)


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
    primary_key: str
    components: List
    child_key: Optional[str]


TREE_TRAVERSE_MAP = {
    "workout": TreeLevelMap(
        {
            "parser": WorkoutParser,
            "primary_key": "workout_id",
            "components": [],
            "child_key": "workout_components",
        }
    ),
    "workout_components": TreeLevelMap(
        {
            "parser": WorkoutComponentParser,
            "primary_key": "workout_component_id",
            "components": [],
            "child_key": "sets",
        }
    ),
    "sets": TreeLevelMap(
        {
            "parser": SetParser,
            "primary_key": "set_id",
            "components": [],
            "child_key": "set_components",
        }
    ),
    "set_components": TreeLevelMap(
        {
            "parser": SetComponentParser,
            "primary_key": "set_component_id",
            "components": [],
            "child_key": None,
        }
    ),
}


def parse_workout_tree_level(
    nodes: List,
    level_name: str,
    foreign_key: Optional[Dict] = None,
    created_at: Optional[str] = None,
):
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
        primary_key = level_info["primary_key"]

        if level_name == "workout":
            created_at = parsed_node.get("created_at")
        else:
            parsed_node["created_at"] = created_at

        if foreign_key:
            parsed_node.update(foreign_key)

        level_info["components"].append(parsed_node)

        if child_key:
            parse_workout_tree_level(
                nodes=node[child_key],
                level_name=child_key,
                created_at=created_at,
                foreign_key={primary_key: parsed_node[primary_key]},
            )


if __name__ == "__main__":
    import json
    from pprint import pprint

    workout = json.load(
        open(
            "/Users/dan/Work/kuda/data/workout_links/parse_test.json",
            "r",
            encoding="utf-8",
        )
    )

    parse_workout_tree_level(
        nodes=[workout],
        level_name="workout",
    )

    pprint(TREE_TRAVERSE_MAP)
