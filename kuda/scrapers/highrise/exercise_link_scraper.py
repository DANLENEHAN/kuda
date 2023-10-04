"""
Module for scraping all the exercise links from
highrise's exercise db
"""

import json
import os
import time
from typing import Tuple

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

current_script_path = os.path.abspath(__file__)
current_script_path = "/".join(current_script_path.split("/")[:-1])
script_start = time.time()


def create_chrome_driver() -> webdriver.Chrome:
    """
    Creates a chrome driver with the necessary
    options for scraping
    Returns:
            webdriver.Chrome: The chrome driver
    """

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-web-security")
    # headless mode
    options.add_experimental_option("detach", True)

    return webdriver.Chrome(options=options)


def pass_cookies_and_email_opt(driver: webdriver.Chrome) -> None:
    """
    Passes the highris e cookies and email opt-in
    Args:
            driver (webdriver.Chrome): The chrome driver
    """
    # Click cookie button
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "css-47sehv"))
    )
    button.click()
    print("Clicked cookie button")

    # Email opt-in is in an iframe
    iframe_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ab-in-app-message"))
    )
    driver.switch_to.frame(iframe_element)
    print("Switched to iframe")

    # Click off email opt-in button
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "modal__cross-web"))
    )
    button.click()
    print("Clicked email opt-in button")

    # Switch back to main frame
    driver.switch_to.default_content()
    print("Switched to main frame")

    # Remove ads
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "fs-close-button-sticky"))
    )
    button.click()
    print("Removed ads")

    # Close cookie footer
    button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "banner-close-button"))
    )
    button.click()
    print("Closed cookie footer")


def find_and_click_btn(
    driver: webdriver.Chrome, button_locator: Tuple[By, str]
) -> None:
    """
    Finds and clicks a button
    Args:
        driver (webdriver.Chrome): The chrome driver
        button_locator (Tuple[By, str]): The button locator
    """

    button = driver.find_element(*button_locator)
    scroll_position = button.location["y"] - 100
    driver.execute_script(f"window.scrollTo(0, {scroll_position});")
    time.sleep(2)
    button.click()
    time.sleep(2)


if __name__ == "__main__":
    chrome_driver = create_chrome_driver()
    chrome_driver.get("https://www.bodybuilding.com/exercises/finder")

    pass_cookies_and_email_opt(driver=chrome_driver)

    locator = (By.CLASS_NAME, "ExLoadMore-btn")
    exercise_count = 0
    retry_count = 0
    while True:
        try:
            find_and_click_btn(driver=chrome_driver, button_locator=locator)
            exercise_count += 15
            if exercise_count % 100 == 0:
                print(f"Scrolled past {exercise_count} workouts.")
        except NoSuchElementException:
            retry_count += 1
            if retry_count < 4:
                print("Button not found. Retrying.")
                time.sleep(5)
                continue
            print("Button no longer exists. Exiting.")
            break

    exercise_result_div = chrome_driver.find_element(
        By.CLASS_NAME, "ExCategory-results"
    )

    all_links = []
    for link_element in exercise_result_div.find_elements(By.TAG_NAME, "a"):
        href = link_element.get_attribute("href")
        if href:
            if not any(
                s in href for s in ("/muscle/", "/equipment/", "finder")
            ):
                all_links.append(href)

    with open(
        os.path.join(current_script_path, "files/exercise_links.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(all_links, f, indent=4)

    print(f"Script took {round((time.time() - script_start)/60, 2)}/  to run.")
