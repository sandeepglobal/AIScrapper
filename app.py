import streamlit as st
from booking import scrape_booking
from stayforlong import scrape_stayforlong
import time
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
    
