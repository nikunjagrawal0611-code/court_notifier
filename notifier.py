from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pdfplumber
import io
import time
import os

CASE_NUMBER = "WRIC/45474/2023"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    print("Telegram response:", r.text)


# 🔹 Starting message
send_telegram("🔎 Starting court list check...")


# Setup Chrome for GitHub Actions (headless)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")   
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

driver.get("https://www.allahabadhighcourt.in/causelist/indexA.html")
time.sleep(3)

# Click GO
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='GO']"))).click()

# Select Court Wise
driver.find_element(By.ID, "court").click()
driver.find_element(By.CSS_SELECTOR, "input[value='Submit']").click()

time.sleep(3)

# Court selection page → just click Submit
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Submit']"))).click()
time.sleep(3)

found = False

try:
    # Wait for List 1
    list1 = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "List 1")))
    pdf_link = list1.get_attribute("href")
    print("PDF:", pdf_link)

    # Download PDF
    r = requests.get(pdf_link)
    pdf_file = io.BytesIO(r.content)

    # Search PDF for CASE_NUMBER
    with pdfplumber.open(pdf_file) as pdf:
        found_in_pdf = any(
            text and CASE_NUMBER in text
            for page in pdf.pages
            if (text := page.extract_text())
        )
        if found_in_pdf:
            send_telegram("⚖️ CASE LISTED IN COURT 1")
            found = True

    if not found:
        send_telegram("❌ CASE NOT LISTED IN COURT 1")

except Exception as e:
    print(f"List 1 not available ({e})")
    send_telegram("❌ List 1 not available")

driver.quit()
