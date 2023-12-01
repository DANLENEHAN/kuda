import asyncio
import json
import logging
from typing import Dict, Generator, List

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)

FAILED_URLS = []
SCRAPED_URLS = []


def scrape_workout(workout: BeautifulSoup) -> Dict:
    """
    Extracts the workout information from the provided HTML snippet

    Args:
        workout (BeautifulSoup): HTML snippet containing the workout
            information

    Returns:
        Dict: Dictionary containing the workout information
    """
    # Parsing the provided HTML snippet
    # Extracting the routine title and details
    routine_title = (
        workout.find("div", class_="mt-2 ml-3 text-black fs-4")
        .text.strip()
        .split("\u2002")
    )
    title = routine_title[0].strip()
    exercise_count = routine_title[1].split(" ")[0]
    duration = routine_title[1].split(" ")[2]

    # Extracting the exercises
    exercises = []
    exercise_rows = workout.find("table", class_="ex-table").find_all("tr")
    for idx, row in enumerate(exercise_rows):
        sets_reps = row.find_all("td")[2].text.strip().split(" ")[0]
        reps = sets_reps.split("x")[1]
        sets = sets_reps.split("x")[0]

        exercise = {
            "name": row.find("a", class_="ex-title text-black").text.strip(),
            "sets": sets,
            "reps": reps,
            "set_rep": sets_reps,
            "rest": row.find_all("td")[3].text.strip().split(" ")[1],
            "link": row.find("a", class_="ex-title text-black")["href"],
            "sequence": idx,
        }
        exercises.append(exercise)

    # Combining the extracted information into a dictionary
    routine_info = {
        "routine_title": routine_title,
        "title": title,
        "exercise_count": exercise_count,
        "duration": duration,
        "exercises": exercises,
    }

    return routine_info


def scrape_workouts(soup: BeautifulSoup) -> Generator[Dict, None, None]:
    """
    Extracts the workouts from the provided HTML snippet

    Args:
        soup (BeautifulSoup): HTML snippet containing the workouts
    """
    workout_elements = soup.find_all("div", class_="tab-pane")
    for idx, workout in enumerate(workout_elements):
        workout = scrape_workout(workout)
        workout["sequence"] = idx
        yield workout


def scrape_plan_details(soup: BeautifulSoup) -> Dict:
    """
    Extracts the plan details from the provided HTML snippet

    Args:
        soup (BeautifulSoup): HTML snippet containing the plan details

    Returns:
        Dict: Dictionary containing the plan details
    """
    sidebar = soup.find(
        "div", class_="my-3 mx-0 p-2 pt-1 bg-white rounded shadow-sm"
    )
    plan_info = sidebar.find("div", class_="scroll-bar-mod")
    info_divs = plan_info.find_all("div")

    downloads_views = info_divs[0].text.strip()
    duration_goal_level = info_divs[2].text.split("-")
    rating_text = info_divs[1].text.strip()
    equipment_needed = (
        plan_info.find_all("strong")[-1]
        .text[20:]
        .replace(" and ", " ")
        .split(",")
    )
    equipment_needed = [equipment.strip() for equipment in equipment_needed]

    return {
        "title": plan_info.find("h1").text.strip(),
        "downloads": downloads_views.split(":")[1].split("/")[0].strip(),
        "views": downloads_views.split(":")[1].split("/")[1].strip(),
        "rating_value": rating_text[8:].split("(")[0].strip(),
        "num_ratings": rating_text.split("(")[1][5:].split(" ")[0],
        "num_days": duration_goal_level[0].strip().split(" ")[0],
        "goal": duration_goal_level[1].strip(),
        "level": duration_goal_level[2].strip(),
        "equipment_needed": equipment_needed,
        "description": info_divs[-1]
        .text.strip()
        .replace("\n", "")
        .replace("\r", ""),
    }


async def scrape_plan(plan_url: str, session: aiohttp.ClientSession):
    """
    Extracts the plan details from the provided HTML snippet

    Args:
        plan_url (str): URL of the plan to scrape
        session (aiohttp.ClientSession): aiohttp session object

    Returns:
        Dict: Dictionary containing the plan details
    """
    async with session.get(plan_url) as response:
        try:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            workouts = list(scrape_workouts(soup))
            plan_data = scrape_plan_details(soup)
            plan_data["workouts"] = workouts
            plan_data["url"] = plan_url
            plan_data["num_workouts"] = len(workouts)
            plan_data["workout_titles"] = [
                workout["title"] for workout in workouts
            ]
            LOGGER.info(
                "Scrape plan: %s (%s Workouts)",
                plan_data["title"],
                len(workouts),
            )
            SCRAPED_URLS.append(plan_url)
            return plan_data
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error("Error scraping plan %s, %s", plan_url, e)
            FAILED_URLS.append(plan_url)
            return {}


async def scrape(plan_url_list: List[str]):
    """
    Scrapes the provided plan URLs asynchronously

    Args:
        plan_url_list (List): List of plan URLs to scrape
    """
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_plan(plan_url, session) for plan_url in plan_url_list]
        plans = await asyncio.gather(*tasks)
        with open(  # pylint: disable=unspecified-encoding
            "workouts.json", "a"
        ) as f:
            json.dump(plans, f, indent=4)


if __name__ == "__main__":
    step_size = 10
    workout_links = pd.read_csv("workout_links.csv")
    try:
        FAILED_URLS = list(pd.read_csv("failed_urls.csv")["0"])
    except:  # pylint: disable=bare-except
        FAILED_URLS = []
    try:
        SCRAPED_URLS = list(pd.read_csv("scraped_urls.csv")["0"])
    except:  # pylint: disable=bare-except
        SCRAPED_URLS = []
    LOGGER.info(
        "Already scraped %s URLs", len(SCRAPED_URLS) + len(FAILED_URLS)
    )
    workout_links = workout_links[
        ~workout_links["workout_url"].isin(SCRAPED_URLS)
    ]
    workout_links = workout_links[
        ~workout_links["workout_url"].isin(FAILED_URLS)
    ]
    max_page = len(workout_links)
    scrape_steps = len(range(0, max_page, step_size))
    for i in range(0, len(workout_links), step_size):
        LOGGER.info(
            "Scraping step %s of %s", str(i // step_size + 1), scrape_steps
        )
        start_idx = i
        end_idx = min(i + step_size - 1, max_page)
        plan_urls = workout_links["workout_url"].tolist()[
            start_idx : end_idx + 1
        ]
        asyncio.run(scrape(plan_urls))
        pd.DataFrame(FAILED_URLS).to_csv("failed_urls.csv", index=False)
        pd.DataFrame(SCRAPED_URLS).to_csv("scraped_urls.csv", index=False)
    pd.DataFrame(FAILED_URLS).to_csv("failed_urls.csv", index=False)
    pd.DataFrame(SCRAPED_URLS).to_csv("scraped_urls.csv", index=False)
