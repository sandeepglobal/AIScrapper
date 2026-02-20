from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse


def scrape_booking(destination, checkin, checkout, adults=2, pages=1):
    """
    destination : e.g. "Dubai"
    checkin     : "2026-03-11"
    checkout    : "2026-03-13"
    adults      : number of adults
    pages       : how many result pages to scrape
    """

    # Build dynamic search URL
    encoded_dest = urllib.parse.quote(destination)
    url = (
        f"https://www.booking.com/searchresults.html?"
        f"ss={encoded_dest}"
        f"&checkin={checkin}"
        f"&checkout={checkout}"
        f"&group_adults={adults}"
        f"&no_rooms=1&group_children=0"
    )

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)

    driver.get(url)
    time.sleep(5)

    all_hotels = []

    def get_room_details(hotel_url):
        driver.get(hotel_url)
        time.sleep(5)

        rooms_list = []

        try:
            table = driver.find_element(By.ID, "hprt-table")
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

            current_room_type = ""

            for row in rows:
                try:
                    room_name_elements = row.find_elements(By.CLASS_NAME, "hprt-roomtype-icon-link")
                    if room_name_elements:
                        current_room_type = room_name_elements[0].text.strip()

                    price_element = row.find_element(By.CLASS_NAME, "prco-valign-middle-helper")
                    price = price_element.text.strip()

                    rooms_list.append({
                        "RoomType": current_room_type,
                        "Price": price
                    })

                except:
                    continue
        except:
            pass

        driver.back()
        time.sleep(4)

        return rooms_list


    current_page = 1

    while current_page <= pages:
        try:
            # Close popup if exists
            try:
                close_btn = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'button[aria-label="Dismiss sign-in info."]')
                    )
                )
                close_btn.click()
            except:
                pass

            soup = BeautifulSoup(driver.page_source, "html.parser")
            properties = soup.find_all("div", {"data-testid": "property-card-container"})

            for prop in properties[0]:
                name_tag = prop.find("div", {"data-testid": "title"})
                location_tag = prop.find("span", {"data-testid": "address"})
                link_tag = prop.find("a", {"data-testid": "title-link"})

                if not link_tag:
                    continue

                name = name_tag.text.strip() if name_tag else "N/A"
                location = location_tag.text.strip() if location_tag else "N/A"
                hotel_url = link_tag["href"]

                room_details = get_room_details(hotel_url)

                for room in room_details:
                    all_hotels.append({
                        "HotelName": name,
                        "Location": location,
                        "RoomType": room["RoomType"],
                        "Price": room["Price"]
                    })

            print(f"Page {current_page} scraped. Total rows: {len(all_hotels)}")

            if current_page == pages:
                break

            # Click next page
            next_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@aria-label='Next page']")
                )
            )
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(5)

            current_page += 1

        except:
            print("No more pages available.")
            break

    driver.quit()

    # df = pd.DataFrame(all_hotels)

    # filename = f"{destination}_{checkin}_{checkout}.csv".replace(" ", "_")
    # df.to_csv(filename, index=False)

    # print(f"\nExtraction Complete! Saved {len(df)} rows to {filename}")

    # return df
    return all_hotels

#scrape_booking('atlantis-the-palm', '2026-04-02', '2026-04-04', adults=2, pages=1)