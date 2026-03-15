from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pdfplumber
import io
import time

CASE_NUMBER = "A227/1258/2019"

BOT_TOKEN = "8700751412:AAG9RBuCaNHSYjTHq55jz-GS9WCVZXQ1UhQ"
CHAT_ID = "5547409819"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


driver = webdriver.Chrome()

wait = WebDriverWait(driver, 20)

driver.get("https://www.allahabadhighcourt.in/causelist/indexA.html")

time.sleep(3)

# Click GO
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='GO']"))).click()

# Select Court Wise
wait.until(EC.element_to_be_clickable((By.ID, "court"))).click()

# Submit
wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Submit']"))).click()

time.sleep(3)

found = False

for court in range(1, 11):

    print("Checking Court", court)

    # Select court number
    Select(wait.until(EC.presence_of_element_located((By.NAME, "courtNo")))).select_by_value(str(court))

    # Click submit
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='Submit']"))).click()

    try:

        # Wait for List 1
        list1 = wait.until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "List 1"))
        )

        pdf_link = list1.get_attribute("href")

        print("PDF:", pdf_link)

        # Download PDF
        r = requests.get(pdf_link)

        pdf_file = io.BytesIO(r.content)

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text and CASE_NUMBER in text:

                    send_telegram(f"⚖️ CASE LISTED\nCourt No.{court}")

                    found = True
                    break

        if found:
            break

    except:
        print("List 1 not available for Court", court)

    driver.back()

    time.sleep(2)

driver.quit()

if not found:
    send_telegram("❌ CASE NOT LISTED IN COURT 1–10")