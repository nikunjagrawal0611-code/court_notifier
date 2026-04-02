from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import requests
import fitz  # PyMuPDF
import time
import os

CASE_NUMBER = "WRIC/45474/2023"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("Telegram response:", r.text)
    except Exception as e:
        print("Telegram error:", e)


def safe_click(xpath, retries=3):
    """Robust click handler to avoid stale element"""
    for attempt in range(retries):
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            time.sleep(1)  # allow DOM stabilize
            driver.execute_script("arguments[0].click();", element)
            print(f"✅ Clicked: {xpath}")
            return True
        except StaleElementReferenceException:
            print(f"⚠️ Stale element on attempt {attempt+1}, retrying...")
            time.sleep(2)
        except TimeoutException:
            print(f"❌ Timeout waiting for: {xpath}")
            return False
    return False


# 🔹 Start
send_telegram("🔎 Starting court list check...")
start_total = time.time()

# 🔹 Setup Chrome (GitHub Actions friendly)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 25)

try:
    driver.get("https://www.allahabadhighcourt.in/causelist/indexA.html")

    # Wait full load
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(2)

    # 🔹 Step 1: Click GO
    safe_click("//input[@value='GO']")

    # 🔹 Step 2: Select Court Wise
    wait.until(EC.element_to_be_clickable((By.ID, "court"))).click()
    time.sleep(1)

    # 🔹 Step 3: First Submit
    safe_click("//input[@value='Submit']")

    # Wait next page load
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(2)

    # 🔹 Step 4: Second Submit
    safe_click("//input[@value='Submit']")

    found = False

    # 🔹 Step 5: Wait for List 1
    try:
        list1 = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "List 1")))
        pdf_link = list1.get_attribute("href")
        print("📄 PDF:", pdf_link)

        # 🔹 Download PDF
        r = requests.get(pdf_link, timeout=15)

        start_pdf = time.time()

        doc = fitz.open(stream=r.content, filetype="pdf")

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")

            if CASE_NUMBER in text:
                send_telegram(f"⚖️ CASE FOUND on page {page_num}")
                found = True
                break

        doc.close()

        pdf_time = round(time.time() - start_pdf, 2)

        if not found:
            send_telegram("❌ CASE NOT LISTED IN COURT 1")

        send_telegram(f"⏱ PDF scan time: {pdf_time} sec")

    except Exception as e:
        print("List error:", e)
        send_telegram("❌ List 1 not available")

except Exception as e:
    print("Main error:", e)
    send_telegram(f"❌ Script error: {e}")

finally:
    # 🔹 Debug screenshot (VERY useful in GitHub)
    driver.save_screenshot("debug.png")

    driver.quit()

total_time = round(time.time() - start_total, 2)
send_telegram(f"⏱ Total script time: {total_time} sec")