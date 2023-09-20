from typing import Dict, List

BASE_WORKOUT_URL: str = (
    "https://bodyspace.bodybuilding.com/workouts/viewworkoutlog/"
)

WORKOUT_VARIANTS: List[Dict[str, str]] = [
    {
        "link": f"{BASE_WORKOUT_URL}coachdmurph/5bf3ec42176a3027b0ad04d8",
        "summary:": (
            "Contains a seperate dropset, superset "
            "and straight set and cardio."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzyt/5721ad540cf2b58f38ced9d7",
        "summary:": (
            "Contains superset and straight " "set with mid energy level."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzupan90/5428c1e70cf2bb28d5a57422",
        "summary:": (
            "Contains all straight sets and 3 cardio workout "
            "components one with cardio superset. Also a cardio 'Set' with"
            "TIME, HEART_RATE and WEIGHT set components."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzneo/5bcad0494e400527ce7156fc",
        "summary:": (
            "Contains 8 workout components with dropsets a"
            " 'REPS' set type with target reps and no "
            "weights or reps filled in at all."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzohaib/5376f2f70cf28afcb6ce2e9a",
        "summary:": (
            "Empty Workout page. Only has the "
            "summary no workout components."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}-NYSE1-/4fb56f36b488e39f44f45352",
        "summary:": "Contains custom exercise, an uncompleted cardio Set",
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzshad/593210b4af19ce69876e7dcd",
        "summary:": "Contains 'REPS' set types and very specific rest times.",
    },
    {
        "link": f"{BASE_WORKOUT_URL}zzolowicz/5901402f36d69c3acb773dd4",
        "summary:": (
            "Contains 1 workout component with " "8 sets 5 supersets each."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}12LittLebit/5a024d9fb36829286bb464e9",
        "summary:": "Contains supersets of weight exercises with timed cardio",
    },
    {
        "link": f"{BASE_WORKOUT_URL}12laynew/58097f260cf27a6fb6996c8d",
        "summary:": (
            "Contains mix of set types with " "target reps and rest times."
        ),
    },
    {
        "link": f"{BASE_WORKOUT_URL}1243week/5a65f0b549cd4326e09821ca",
        "summary:": (
            "Broke the scraper with a weird set component title condition."
        ),
    },
]
