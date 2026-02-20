import streamlit as st
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
class webscraper:
    def booking(destination:str, checkindate:str,checkoutdate:str,noofadult:int):
        return scrape_booking(destination,checkindate,checkoutdate,noofadult)
    def stayforlong(destination:str, checkindate:str,checkoutdate:str,noofadult:int):
        return scrape_stayforlong(destination,checkindate,checkoutdate,noofadult)
    
st.title("🏨 Hotel Scraper Dashboard")
st.sidebar.header("Search Options")

platform = st.sidebar.selectbox(
    "Select Platform",
    ["Booking", "Stayforlong"]
)

destination = st.sidebar.text_input("Hotel",placeholder="Please enter hotel name")
checkin = st.sidebar.date_input("Check-in",)
checkout = st.sidebar.date_input("Check-out")
run_button = st.sidebar.button("Run Scraper")
if run_button:
     my_info_message=st.info(f"Running scraper for {platform}...")
     if platform == "Booking":
        df = scrape_booking(destination, str(checkin.strftime("%Y-%m-%d")), str(checkout),2)

     elif platform == "Stayforlong":
        df = scrape_stayforlong(destination, str(checkin.strftime("%Y-%m-%d")), str(checkout),2)

     my_success_message=st.success("Scraping Completed!")

     st.dataframe(df)
     # Wait for a few seconds
     time.sleep(3)

    # Clear the alert from the page
     my_success_message.empty() 
     my_info_message.empty()
    #  st.download_button("Download CSV",
    #     df.to_csv(index=False),
    #     file_name=f"{platform}_{destination}.csv",
    #     mime="text/csv"
    #  )
    



