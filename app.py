import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

app = FastAPI(title="Scholar PDF Search API")


def get_random_user_agent():
    try:
        return UserAgent().random
    except:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
        )

async def my_search(query: str, max_results: int = 2):
    results = []
    ua = get_random_user_agent()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(user_agent=ua)
        page    = await ctx.new_page()
        url     = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
        await page.goto(url, timeout=15000)

        blocks = await page.query_selector_all("div.gs_r.gs_or.gs_scl")
        for block in blocks[:max_results]:
            title_el = await block.query_selector("h3.gs_rt")
            title    = await title_el.inner_text() if title_el else "No Title"

            link_el  = await title_el.query_selector("a") if title_el else None
            article  = await link_el.get_attribute("href") if link_el else None

            pdf_el   = await block.query_selector("div.gs_or_ggsm a")
            pdf_link = await pdf_el.get_attribute("href") if pdf_el else None

            results.append({
                "title": title,
                "article_url": article or "Not available",
                "pdf_url":     pdf_link or "No PDF found"
            })
        await browser.close()
    return results


class SearchRequest(BaseModel):
    query:       str
    max_results: int = 2


@app.post("/search")
async def search_endpoint(req: SearchRequest):
    papers = await my_search(req.query, req.max_results)
    return {"results": papers}
