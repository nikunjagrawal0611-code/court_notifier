from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import fitz  # PyMuPDF
import time
import os

CASE_NUMBER = "CRLA/1354/2018"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    print("Telegram response:", r.text)


# 🔹 Starting message
send_telegram("🔎 Starting court list check...")

start_total = time.time()

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

# Click GO
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='GO']"))).click()

# Select Court Wise
wait.until(EC.element_to_be_clickable((By.ID, "court"))).click()
driver.find_element(By.CSS_SELECTOR, "input[value='Submit']").click()

# Court selection page → just click Submit
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Submit']"))).click()

found = False

try:
    # Wait for List 1
    list1 = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "List 1")))
    pdf_link = list1.get_attribute("href")
    print("PDF:", pdf_link)

    # Download PDF
    r = requests.get(pdf_link)

    # 🔹 Start PDF timing
    start_pdf = time.time()

    doc = fitz.open(stream=r.content, filetype="pdf")

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")

        if CASE_NUMBER in text:
            send_telegram(f"⚖️ CASE FOUND on page {page_num}")
            found = True
            break

    doc.close()

    end_pdf = time.time()
    pdf_time = round(end_pdf - start_pdf, 2)

    if not found:
        send_telegram("❌ CASE NOT LISTED IN COURT 1")

    send_telegram(f"⏱ PDF scan time: {pdf_time} sec")

except Exception as e:
    print(f"List 1 not available ({e})")
    send_telegram("❌ List 1 not available")

driver.quit()

end_total = time.time()
total_time = round(end_total - start_total, 2)

send_telegram(f"⏱ Total script time: {total_time} sec")
