import logging
import time
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
BASE_URL = "https://bodyspace.bodybuilding.com/workouts/workout-logs/"


def click_element(
    driver: webdriver.Chrome,
    dropdown_id: str,
    by: By = By.CSS_SELECTOR,
    exceptions: Tuple = (
        NoSuchElementException,
        ElementNotInteractableException,
        StaleElementReferenceException,
    ),
) -> None:
    """
    Clicks on an element with the given ID.

    Args:
        driver: Selenium webdriver.
        dropdown_id: ID of the element to click.
        by: By object to use to find the element.
        exceptions: Exceptions to catch and retry on.

    Raises:
        NoSuchElementException: If the element is not found.
        ElementNotInteractableException: If the element is not interactable.
        StaleElementReferenceException: If the element is stale.
    """
    try:
        element = driver.find_element(by, dropdown_id)
        element.click()
    except exceptions:
        time.sleep(0.1)
        click_element(driver, dropdown_id, by)


def scrape_workout_link_page(
    driver: webdriver.Chrome,
) -> List[Dict]:  # noqa: R0914
    """
    Scrapes the workout links from the current page.

    Args:
        driver: Selenium webdriver.

    Returns:
        List of dictionaries containing the workout details.
    """
    soup = BeautifulSoup(driver.page_source, "html.parser")

    workouts = []

    for workout in soup.find_all("div", class_="columnTemplateReport"):
        try:
            workout_details = {}

            # Extracting workout name and URL
            title_tag = workout.find("a", class_="columnTitle")
            workout_details["workout_name"] = title_tag.text
            workout_details["workout_url"] = title_tag["href"]

            # Extracting creator details
            creator_tag = workout.find("div", class_="columnCreatedBy").find(
                "a"
            )
            workout_details["creator"] = creator_tag.text
            workout_details["creator_url"] = creator_tag["href"]

            # Extracting workout details
            fields = workout.find_all("div", class_="field")
            for field in fields:
                key = field.contents[0].strip()
                value = field.find("span").text.strip()
                workout_details[key.lower()] = value

            # Extracting date details
            month_tag = workout.find("span", class_="month-abbr")
            date_tag = workout.find("span", class_="month-date")
            year_tag = workout.find("span", class_="year")
            workout_details[
                "date"
            ] = f"{month_tag.text} {date_tag.text}, {year_tag.text}"

            # Extracting muscles worked
            muscles_worked = workout.find(
                "div", class_="temp-text"
            ).text.strip()
            workout_details["muscles_worked"] = muscles_worked

            # Extracting total weight lifted
            weight_lifted = (
                workout.find("div", class_="timeValue")
                .find("span")
                .text.strip()
            )
            weight_unit = (
                workout.find("div", class_="timeLabels")
                .find("span")
                .text.strip()
            )
            workout_details[
                "total_weight_lifted"
            ] = f"{weight_lifted} {weight_unit}"

            workouts.append(workout_details)
        except Exception:
            LOGGER.info("Failed to parse workout details")
            continue

    # The list "workouts" will now contain the extracted
    #  details for each workout
    return workouts


def remove_modal(driver: webdriver.Chrome) -> None:
    """
    Removes the modal iframe.

    Args:
        driver: Selenium webdriver.
    """
    click_element(driver, '//button[@data-button-id="close"]', By.XPATH)
    driver.switch_to.default_content()


def agree_cookie(driver: webdriver.Chrome) -> None:
    """
    Agree to cookie policy.

    Args:
        driver: Selenium webdriver.
    """
    click_element(driver, '//button/span[text()="AGREE"]', By.XPATH)


def reject_other_cookies(driver: webdriver.Chrome) -> None:
    """
    Reject other cookies.

    Args:
        driver: Selenium webdriver.
    """
    click_element(driver, "onetrust-reject-all-handler", By.ID)


def close_modal_iframe(driver: webdriver.Chrome) -> None:
    """
    Closes the modal iframe.

    Args:
        driver: Selenium webdriver.
    """
    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    iframe_element = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//iframe[@title="Single Page Modal"]')
        )
    )
    driver.switch_to.frame(iframe_element)
    remove_modal(driver)


def close_popups(driver: webdriver.Chrome) -> None:
    """
    Closes the popups that appear when navigating to a user's page.

    Args:
        driver: Selenium webdriver.
    """
    wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//iframe[@title="Single Page Modal"]')
            )
        )
        close_modal_iframe(driver)
        reject_other_cookies(driver)
    except TimeoutException:
        return


def go_to_next_page(
    driver: webdriver.Chrome, next_page_number: int, attempts: int = 0
) -> bool:
    """
    Clicks on the next page button.

    Args:
        driver: Selenium webdriver.
        next_page_number: Page number to navigate to.
        attempts: Number of attempts made so far.

    Returns:
        True if the next page button was clicked successfully, False otherwise.
    """
    try:
        next_page = driver.find_element(
            By.XPATH, '//a[@title="Go to next page"]'
        )
    except NoSuchElementException:
        time.sleep(0.5)
        if attempts < 5:
            return go_to_next_page(driver, next_page_number, attempts + 1)
        return False

    # Check that the next page button is clickable
    next_page.click()
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, "span.button.active span"), str(next_page_number)
        )
    )
    return True


def scrape_user_workout_links(
    username: str,
    session: requests.Session,
    driver: Optional[webdriver.Chrome],
) -> webdriver.Chrome:
    """
    Scrapes the workout links for a user.

    Args:
        username: Username of the user to scrape.
        session: Requests session.
        driver: Selenium webdriver.

    Returns:
        Selenium webdriver.

    """
    results = []
    if check_user_has_workouts(username=username, session=session):
        LOGGER.info("Scraping %s", username)
        if driver is None:
            driver = init_webdriver(username=username)
        results = scrape_existing_links(username, driver=driver)
    else:
        LOGGER.info("Skipped: %s (No Workouts)", username)
    return driver, results


def scrape_existing_links(
    username: str, driver: webdriver.Chrome
) -> List[Dict]:
    """
    Scrapes the existing workout links for a user.

    Args:
        username: Username of the user to scrape.
        driver: Selenium webdriver.

    Returns:
        List of dictionaries containing the workout details.
    """
    driver.get(f"{BASE_URL}{username}")
    results: List[Dict] = []
    curret_page = 1
    wait = WebDriverWait(driver, 5)
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@class="columnTemplateReport workoutLog"]')
            )
        )
    except TimeoutException:
        LOGGER.info("No workouts found")
    while True:
        LOGGER.info(
            "Scraping %s, Page %s, Results so far: %s",
            username,
            str(curret_page + 1),
            str(len(results)),
        )
        results.extend(scrape_workout_link_page(driver))
        curret_page += 1
        if not go_to_next_page(driver, curret_page):
            break
    LOGGER.info("Scraped %s, Results %s", username, str(len(results)))
    return results


def check_user_has_workouts(username: str, session: requests.Session) -> bool:
    """
    Checks if a user has workouts.

    Args:
        username: Username to check.
        session: Requests session.

    Returns:
        True if the user has workouts, False otherwise.
    """
    html = session.get(f"{BASE_URL}{username}").text
    soup = BeautifulSoup(html, "html.parser")
    no_results_panel = soup.find("div", class_="no-results-panel noHistory")
    return no_results_panel is None


def init_webdriver(username: str) -> webdriver.Chrome:
    """
    Initializes the webdriver.

    Args:
        username: Username to navigate to.

    Returns:
        Selenium webdriver.
    """
    try:
        LOGGER.info("Initializing the webdriver...")

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )  # Disable images
        chrome_options.add_experimental_option(
            "prefs",
            {"profile.managed_default_content_settings.stylesheets": 2},
        )  # Disable CSS
        driver = webdriver.Chrome(options=chrome_options)
        LOGGER.info("Webdriver initialized successfully.")

        driver.get(f"{BASE_URL}{username}")
        LOGGER.info("Navigated to URL: %s", f"{BASE_URL}{username}")

        close_popups(driver)
        LOGGER.info("Closed pop-ups successfully.")

        return driver
    except Exception as exc:
        LOGGER.error("Error initializing the webdriver: %s", str(exc))
        raise


def execute(usernames: List[str]):
    """
    Executes the scraper.

    Args:
        usernames: List of usernames to scrape.
    Returns:
        List of dictionaries containing the workout details."""
    driver = None
    session = requests.Session()

    results = []
    for username in usernames:
        driver, user_results = scrape_user_workout_links(
            username, session, driver
        )
        results.extend(user_results)

    if driver is not None:
        driver.quit()
    return results
