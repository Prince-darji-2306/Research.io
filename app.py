import os
import random
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0"
]

app = FastAPI()


class PDFResult(BaseModel):
    title: str
    pdf_link: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/search", response_model=List[PDFResult])
def search_pdfs(query: str = Query(..., description="Search query"), max_results: int = Query(3, ge=1, le=10)):
    
    cx_id = os.getenv("CX_ID")
    if not cx_id:
        return []

    ua = random.choice(USER_AGENTS)

    options = uc.ChromeOptions()
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=options, use_subprocess=True)

    try:
        search_query = quote(query + " filetype:pdf")
        url = f"https://cse.google.com/cse?cx={cx_id}&q={search_query}"
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.gs-webResult, div.gs-result"))
        )

        results = []
        blocks = driver.find_elements(By.CSS_SELECTOR, "div.gs-webResult, div.gs-result")
        for blk in blocks:
            try:
                link_elem = blk.find_element(By.CSS_SELECTOR, "div.gs-title > a.gs-title")
                href = link_elem.get_attribute("href")
                title = link_elem.text.strip()
                if href and href.lower().endswith(".pdf"):
                    results.append({"title": title, "pdf_link": href})
                if len(results) >= max_results:
                    break
            except:
                continue

        return results
    finally:
        driver.quit()
