import time
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = FastAPI()

def My_search(query: str, max_results: int = 3):
    start_time = time.time()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-images")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    formatted_query = f'{query} (site:arxiv.org OR site:researchgate.net OR site:*.edu OR site:*.ac.in OR site:*.ac.uk OR site:ieeexplore.ieee.org OR site:springer.com) filetype:pdf'
    search_url = f"https://www.google.com/search?q={formatted_query.replace(' ', '+')}"
    driver.get(search_url)

    time.sleep(1)

    results = []
    try:
        result_blocks = driver.find_elements(By.CSS_SELECTOR, "div.b8lM7")

        for block in result_blocks:
            try:
                title_el = block.find_element(By.CSS_SELECTOR, "h3.LC20lb.MBeuO.DKV0Md")
                title = title_el.text.strip()

                link_el = block.find_element(By.TAG_NAME, "a")
                href = link_el.get_attribute("href")

                if href and href.endswith(".pdf"):
                    results.append({
                        "title": title,
                        "pdf_link": href
                    })

                if len(results) >= max_results:
                    break

            except Exception:
                continue

    except Exception as e:
        print("[Selenium Error]", e)

    driver.quit()
    print(f"[Selenium] Time taken: {round(time.time() - start_time, 2)} seconds")
    return results

@app.get("/")
def health_check():
    return {"status": "ok", "message": "PDF Fetch API running"}

@app.get("/search")
def fetch_pdfs(query: str = Query(..., min_length=3), max_results: int = 3):
    try:
        result = My_search(query, max_results)
        return JSONResponse(content={"results": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
