# Doing some Analysis on the old Male Workout Links Data

import pandas as pd
import numpy as np
import os
from pprint import pprint

root_path: str = "./phase_zero/data/workout_links/male/set_2"

example_workout_link: str = (
    "https://bodyspace.bodybuilding.com/"  # base url
    "workouts/viewworkoutlog/reycuban/"  # username
    "5622848d0cf2002249c7305a"  # workout uuid
)


def extract_username(links: str) -> str:
    """
    Extracts the username from the links column
    """

    links = list(eval(links))
    if len(links) == 0:
        return "n/a"
    return links[0].split("viewworkoutlog")[1].split("/")[1]


def add_username_col() -> None:
    # Adding username column to the data
    for _, _, files in os.walk(root_path):
        for file in files:
            # Skipping non-csv files
            if ".csv" not in file:
                continue
            df = pd.read_csv(f"{root_path}/{file}")
            # Allowing re-running of the script
            if "username" in df.columns:
                continue
            print(f"Processing: '{file}'")
            df["username"] = df["Links"].apply(extract_username)
            # Removing the Names column as it wasn't consistent
            if "Names" in df.columns:
                df.drop(columns=["Names"], inplace=True)
            df.to_csv(f"{root_path}/{file}", index=False)


# Getting all files into one big DF
# Four loops because I'm lazy :)
data = []
root_path: str = "./phase_zero/data/workout_links/male/set_1"
for _, _, files in os.walk(root_path):
    for file in files:
        if ".csv" not in file:
            continue
        print(f"Processing: '{file}'")
        pdf = pd.read_csv(f"{root_path}/{file}")
        data.extend(pdf.to_dict(orient="records"))
        del pdf
root_path: str = "./phase_zero/data/workout_links/male/set_2"
for _, _, files in os.walk(root_path):
    for file in files:
        if ".csv" not in file:
            continue
        print(f"Processing: '{file}'")
        pdf = pd.read_csv(f"{root_path}/{file}")
        data.extend(pdf.to_dict(orient="records"))
        del pdf

print(f"Total Users: {len(data)}")

df = pd.DataFrame(data)
# Age can sometimes be an int
df["Age"] = df["Age"].astype(str)
df["Links"] = df["Links"].apply(lambda links: list(eval(links)))


def custom_aggregator(series: pd.Series) -> pd.Series:
    """
    Joining all the dataframes into a single dataframe.
    We seem to have duplicate user rows where we have their
    their profile data in one or not the other or a mix of both.
    This function aims to join all the data into a single row.
    Extending the Links column but also removing duplicates.
    For the rest of the columns, we take the first non-null value.
    """

    if len(series) <= 1:
        # If there's only one value, return it
        return series

    items = set()
    for item in series:
        # Aggregating and de-duplicating lists
        if isinstance(item, list):
            for i in item:
                items.add(i)
        else:
            # Taking the first non-null value for simple columns
            if item not in [np.nan, None, "--"] and not pd.isna(item):
                return pd.Series(item)

    # We'll either have a list of Links here or a null value
    # for one of our simple columns
    return pd.Series([list(items)]) if items else np.nan


# Groupby columns
cols = [
    "Age",
    "Body_Fat",
    "Gender",
    "Goal",
    "Height",
    "Member_Since",
    "Weight",
    "username",
]

df = df.groupby("username").agg(custom_aggregator).reset_index()

exploded_df = df.explode("Links")
print(
    f"Total Workouts: {len(exploded_df)}",
)

age_dist = exploded_df.groupby("Age").agg({"Links": "count"}).reset_index()
print(
    f"Age Workout Distribution:",
)
pprint(age_dist.to_dict(orient="records"))

most_wrks = age_dist.Links.nlargest(1, keep="all")
print(
    f"\nHighest workout count: Age: {age_dist.iloc[most_wrks.index[0]].Age} Num workouts: {most_wrks.iloc[0]}\n\n",
)
snd_most_wrks = age_dist.Links.nlargest(2, keep="all")
print(
    f"Second highest workout count: Age: {age_dist.iloc[snd_most_wrks.index[-1]].Age} Num workouts: {snd_most_wrks.iloc[-1]}\n\n",
)

least_wrks = age_dist.Links.nsmallest(1, keep="all")
print(
    f"Lowest workout count: Age: {age_dist.iloc[least_wrks.index[-1]].Age} Num workouts: {least_wrks.iloc[-1]}\n\n",
)

df.to_csv("./data/workoutlinks/full_male_workout_links.csv", index=False)
