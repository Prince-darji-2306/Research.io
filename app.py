import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from playwright.sync_api import sync_playwright

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    max_results: int = 3

def My_search_playwright(query: str, max_results: int = 3):
    start_time = time.time()
    results = []

    formatted_query = f'{query} (site:arxiv.org OR site:researchgate.net OR site:*.edu OR site:*.ac.in OR site:*.ac.uk OR site:ieeexplore.ieee.org OR site:springer.com) filetype:pdf'
    search_url = f"https://www.google.com/search?q={formatted_query.replace(' ', '+')}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            java_script_enabled=True,
            locale="en-US"
        )
        context.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""
        )

        page = context.new_page()
        page.goto(search_url, timeout=60000)
        page.wait_for_timeout(1000)  # Wait 1.5s to allow content to load

        result_blocks = page.query_selector_all("div.b8lM7")
        for block in result_blocks:
            try:
                title_el = block.query_selector("h3.LC20lb")
                if not title_el:
                    continue
                title = title_el.inner_text().strip()

                link_el = block.query_selector("a")
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

        browser.close()

    print(f"[Playwright] Time taken: {round(time.time() - start_time, 2)} seconds")
    return results

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Playwright PDF Fetch API running"}

@app.post("/search")
def fetch_pdfs(req: SearchRequest):
    try:
        result = My_search_playwright(req.query, req.max_results)
        return JSONResponse(content={"results": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
