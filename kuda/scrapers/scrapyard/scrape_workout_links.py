import asyncio
import logging
from typing import Dict, List

import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
BASE_URL = (
    "https://www.jefit.com/routines/"
    "?name=1&tag=1&keyword=0&gender=0&sort=4&search=&page="
)


def scrape_workout_link(element: BeautifulSoup) -> Dict:
    """
    Extracts the workout link from the provided HTML snippet

    Args:
        element (BeautifulSoup): HTML snippet containing the workout link

    Returns:
        Dict: Dictionary containing the workout link data
    """
    workout_url_suffix = element.find(
        "a", id=lambda x: x and x.startswith("routine-title-")
    )["href"]
    workout_url = f"https://www.jefit.com/routines/{workout_url_suffix}"
    return {
        "title": element.find("div").text.strip(),
        "duration": element.find_all("td", align="center")[0].text.strip(),
        "purpose": element.find_all("td", align="center")[1].text.strip(),
        "skill_level": element.find_all("td", align="center")[2].text.strip(),
        "likes_comments": element.find_all("td", align="center")[
            3
        ].text.strip(),
        "creator": element.find(
            "a", id=lambda x: x and x.startswith("routine-creator-")
        ).text.strip(),
        "availability": element.find_all("td", align="center")[
            -1
        ].text.strip(),
        "workout_url": workout_url,
    }


def scrape_workout_links(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extracts the workout links from the provided HTML snippet

    Args:
        soup (BeautifulSoup): HTML snippet containing the workout links

    Returns:
        List: List of dictionaries containing the workout link data"""
    table = soup.find("table", id="hor-minimalist_3")
    return [
        scrape_workout_link(element) for element in table.find_all("tr")[1:]
    ]


async def scrape_page(
    page_number: int, session: requests.Session
) -> List[Dict[str, str]]:
    """
    Scrapes the provided page number and returns the workout links

    Args:
        page_number (int): Page number to scrape
        session (requests.Session): Requests session object

    Returns:
        List: List of dictionaries containing the workout link data
    """
    async with session.get(BASE_URL + str(page_number)) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        workouts = scrape_workout_links(soup)
        LOGGER.info("Scraped page %s, Results: %s", page_number, len(workouts))
        return workouts


async def fetch_page(page: int) -> List[Dict[str, str]]:
    """
    Fetches the provided page number asynchronously

    Args:
        page (int): Page number to fetch

    Returns:
        List: List of dictionaries containing the workout link data

    Raises:
        Exception: If there is an error fetching the page
    """
    async with aiohttp.ClientSession() as session:
        try:
            workouts = await scrape_page(page, session)
            if page % 5 == 0:
                LOGGER.info("Scraped Page: %s", str(page))
            return workouts
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error("Error scraping page %s, %s", str(page), e)
            return []


async def main(start_index: int, end_index: int) -> List[Dict[str, str]]:
    """
    Fetches the provided page range asynchronously

    Args:
        start_index (int): Start page number
        end_index (int): End page number

    Returns:
        List: List of dictionaries containing the workout link data
    """
    tasks = [fetch_page(page) for page in range(start_index, end_index + 1)]
    scraped_workouts = await asyncio.gather(*tasks)
    # Flatten the list of lists into a single list
    scraped_workouts = [
        workout for sublist in scraped_workouts for workout in sublist
    ]
    return scraped_workouts


if __name__ == "__main__":
    max_page = 7064  # This was the max page as of 2023-09-21
    step_size = 20  # Number of pages to scrape at a time asynchronously
    min_page = 6982  # Start page
    for i in range(min_page, max_page + 1, step_size):
        start_idx = i
        end_idx = min(i + step_size - 1, max_page)
        LOGGER.info("Scraping pages %s to %s", start_idx, end_idx)
        all_workouts = asyncio.run(main(start_idx, end_idx))
        df = pd.DataFrame(all_workouts)
        df.to_csv(f"JeFit/workouts_{start_idx}_{end_idx}.csv", index=False)
