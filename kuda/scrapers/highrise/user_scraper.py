import logging
import time
from typing import Dict, List

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)


def click_element(  # pylint: disable=inconsistent-return-statements
    driver: webdriver,
    dropdown_id: str,
    by: By,
):
    """Clicks on an element with the given id and by type.

    Args:
        driver (webdriver): Selenium webdriver
        dropdown_id (str): Id of the element to click
        by (By): Type of the element to click
    """
    try:
        element = driver.find_element(by, dropdown_id)
        element.click()
    except (
        NoSuchElementException,
        ElementNotInteractableException,
        StaleElementReferenceException,
    ):
        time.sleep(0.1)
        return click_element(driver, dropdown_id, by)


def agree_cookie(driver: webdriver) -> None:
    """
    Agree to cookie policy.

    Args:
        driver (webdriver): Selenium webdriver.
    """
    click_element(driver, '//button/span[text()="AGREE"]', By.XPATH)


def reject_other_cookies(driver: webdriver) -> None:
    """
    Reject all other cookies.

    Args:
        driver (webdriver): Selenium webdriver.
    """
    click_element(driver, "onetrust-reject-all-handler", By.ID)


def remove_modal(driver: webdriver) -> None:
    """
    Remove modal.

    Args:
        driver (webdriver): Selenium webdriver.
    """
    click_element(driver, '//button[@data-button-id="close"]', By.XPATH)
    driver.switch_to.default_content()


def close_modal_iframe(  # pylint: disable=inconsistent-return-statements
    driver: webdriver,
):
    """
    Close modal iframe.

    Args:
        driver (webdriver): Selenium webdriver.
    """
    try:
        iframe_element = driver.find_element(
            By.XPATH, '//iframe[@title="Single Page Modal"]'
        )
    except NoSuchElementException:
        time.sleep(0.1)
        return close_modal_iframe(driver)
    driver.switch_to.frame(iframe_element)
    remove_modal(driver)


def open_members_page(driver: webdriver) -> None:
    """
    Open members page.

    Args:
        driver (webdriver): Selenium webdriver.
    """
    driver.get("https://bodyspace.bodybuilding.com/member-search")
    agree_cookie(driver)
    close_modal_iframe(driver)
    reject_other_cookies(driver)
    return driver


def select_gender(driver: webdriver, gender_id: int = 2):
    """
    Selects gender from dropdown.

    Args:
        driver (webdriver): Selenium webdriver.
        gender_id (int): ID for gender
    """
    # Male = 1, Female = 2
    click_element(driver, ".genderDropDown.bbDropDown", By.CSS_SELECTOR)
    click_element(
        driver,
        f"li.cape-item[data-option-value='{gender_id}']",
        By.CSS_SELECTOR,
    )
    LOGGER.info("Selected Gender")


def select_age(driver: webdriver, min_age: int, max_age: int) -> None:
    """
    Selects age from filter.

    Args:
        driver (webdriver): Selenium webdriver.
        min_age (int): Minimum age.
        max_age (int): Maximum age.
    """
    min_age_input = driver.find_element(
        By.CSS_SELECTOR, "input.rangeSliderFirst"
    )
    max_age_input = driver.find_element(
        By.CSS_SELECTOR, "input.rangeSliderSecond"
    )
    min_age_input.clear()
    max_age_input.clear()
    min_age_input.send_keys(f"{min_age}")
    max_age_input.send_keys(f"{max_age}")
    LOGGER.info("Ages Selected %s - %s", min_age, max_age)


def set_filters(
    driver: webdriver,
    gender_id: int,
    min_age: int,
    max_age: int,
) -> None:
    """
    Set filters.

    Args:
        driver (webdriver): Selenium webdriver.
        gender_id (int): Integer for target gender
        min_age (int): Minimum age.
        max_age (int): Maximum age.
    """
    select_gender(driver, gender_id)
    select_age(driver, min_age, max_age)


def select_num_results(driver: webdriver, result_num: int = 100) -> None:
    """
    Selects number of results per page.

    Args:
        driver (webdriver): Selenium webdriver.
        result_num (int): Number of results per page.
    """
    click_element(driver, ".resultsPerPage .bbDropDown", By.CSS_SELECTOR)
    click_element(
        driver,
        f"li.cape-item[data-option-value='{result_num}']",
        By.CSS_SELECTOR,
    )


def scrape_user(user) -> Dict[str, str]:
    """
    Scrape user information from user card.

    Args:
        user (BeautifulSoup): User card.

    Returns:
        Dict[str, str]: User information.
    """
    user_info = {}

    user_info["real_name"] = (
        user.find("div", class_="bbcRealName").text
        if user.find("div", class_="bbcRealName")
        else None
    )
    user_info["url"] = user.find("a", class_="noBBC")["href"]
    user_info["user_name"] = user.find("a", class_="noBBC").text
    user_info["profile_pic"] = user.find("img")["src"]

    bbc_details = user.find("div", class_="bbcDetails")
    metrics = bbc_details.find_all("div", class_="bbcMetric")
    for metric in metrics:
        key = metric.find("span", class_="bbcField").text.strip(":").lower()
        value = metric.find("span", class_="bbcValue").text.lower()
        user_info[key] = value

    head_metrics = bbc_details.find("div", class_="bbcHeadMetrics").find_all(
        "span", class_="bbcValue"
    )
    user_info["age"] = head_metrics[0].text
    user_info["height"] = head_metrics[1].text
    user_info["weight"] = head_metrics[2].text
    user_info["bodyfat_percentage"] = head_metrics[3].text

    return user_info


def scrape_page(driver: webdriver) -> List[Dict[str, str]]:
    """
    Scrapes page for user information.

    Args:
        driver (webdriver): Selenium webdriver.

    Returns:
        List[Dict[str, str]]: List of user information.
    """
    page_content = driver.page_source
    soup = BeautifulSoup(page_content, "html.parser")
    users = soup.find_all("div", class_="bbcContainer")
    return [scrape_user(user) for user in users]


def go_to_next_page(
    driver: webdriver, next_page_number: int, attempts: int = 0
) -> bool:
    """
    Clicks on the next page button.

    Args:
        driver (webdriver): Selenium webdriver.
        next_page_number (int): Page number to go to.
        attempts (int): Number of attempts to click on the next page button.

    Returns:
        bool: True if successful, False otherwise.
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
    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, "span.button.active span"), str(next_page_number)
        )
    )
    return True


def save_users(
    users: List[Dict],
    min_age: int,
    max_age: int,
    gender_id: int,
    output_path: str,
) -> None:
    """
    Saves users to csv file.

    Args:
        users (List[Dict[str, str]]): List of user information.
        min_age (int): Minimum age.
        max_age (int): Maximum age.
        gender_id (int): ID for target gender.
        output_path (str): Path to save csv file.
    """
    gender_name = "male"
    if gender_id == 2:
        gender_name = "female"

    df = pd.DataFrame(users)
    unique_ages = df.age.unique()
    df = df[~df.age.isnull()]
    valid_ages = [age for age in unique_ages if min_age <= int(age) <= max_age]
    for age in valid_ages:
        age_df = df[df.age == age]
        LOGGER.info("Saving %s users with age %s", len(age_df), age)
        age_df.to_csv(
            f"{output_path}/users_{gender_name}_{age}.csv", index=False
        )


def init_webdriver() -> webdriver.Chrome:
    """
    Initializes the webdriver.

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
        return driver
    except Exception as exc:
        LOGGER.error("Error initializing the webdriver: %s", str(exc))
        raise


def execute(
    gender_id: int, min_age: int, max_age: int, output_path: str
) -> None:
    """
    Scrapes users from Bodybuilding.com.

    Args:
        gender_id (gender_id): Id for target gender
        min_age (int): Minimum age.
        max_age (int): Maximum age.
        output_path (str): Path to save csv file.
    """
    driver = init_webdriver()
    open_members_page(driver)
    LOGGER.info("Members page opened")
    set_filters(driver, gender_id, min_age, max_age)
    time.sleep(6)
    select_num_results(driver, 100)
    time.sleep(2)

    users: List = []
    page_num = 1
    while True:
        LOGGER.info(
            "Scraping page %s (Results so far: %s)", page_num, len(users)
        )
        results = scrape_page(driver)
        users.extend(results)
        page_num += 1
        if not go_to_next_page(driver, page_num):
            break
    LOGGER.info("Scraped %s users", len(users))
    save_users(users, min_age, max_age, gender_id, output_path)
    driver.close()


if __name__ == "__main__":
    execute(gender_id=2, min_age=18, max_age=25, output_path="users")
