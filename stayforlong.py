from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time


def scrape_stayforlong(destination,  checkin, checkout,adults):
    """
    hotel_slug example:
    ae/atlantis-the-palm_dubai-coast
    """
    hotel_slug=f"ae/{destination}"
    base_url = "https://www.stayforlong.com/hotel/"
    url = f"{base_url}{hotel_slug}?adults={adults}&checkIn={checkin}&checkOut={checkout}&page=1"

    print("Opening:", url)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    driver.get(url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(6)

    # 🔥 Load all rooms
    while True:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)

            load_more = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'more')]")
                )
            )

            driver.execute_script("arguments[0].click();", load_more)
            print("Clicked Load More")
            time.sleep(6)

        except TimeoutException:
            print("No more rooms to load.")
            break

    print("All rooms loaded.")

    # 🔥 Parse page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    all_rooms = []

    properties = soup.find_all("li", {"data-testid": "rooms-list-item"})

    for prop in properties:
        roomname_tag = prop.find("button", {"data-testid": "room-name"})
        if not roomname_tag:
            continue

        roomname = roomname_tag.get_text(strip=True)
        offers = prop.find_all("div", {"data-testid": "room-offers-list"})

        for offer in offers:
            rate_basis = offer.select("[class*='styles_boardInfoButton']")
            prices = offer.select("[class*='styles_totalPrice']")

            for i in range(min(len(rate_basis), len(prices))):
                all_rooms.append({
                    "RoomName": roomname,
                    "RoomType": rate_basis[i].get_text(strip=True),
                    "Price": prices[i].get_text(strip=True)
                })

    # 🔥 Save dynamic filename
    # filename = f"{hotel_slug.split('/')[-1]}_{checkin}_{checkout}.csv"
    # df = pd.DataFrame(all_rooms)
    # df.to_csv(filename, index=False)

    # print(f"Saved {len(df)} rows to {filename}")
    return all_rooms


# # ===== USER INPUT =====
# hotel_slug = input("Enter hotel slug (example: ae/atlantis-the-palm_dubai-coast): ")
# adults = input("Enter number of adults: ")
# checkin = input("Enter check-in date (YYYY-MM-DD): ")
# checkout = input("Enter check-out date (YYYY-MM-DD): ")

# scrape_stayforlong(hotel_slug, adults, checkin, checkout)
