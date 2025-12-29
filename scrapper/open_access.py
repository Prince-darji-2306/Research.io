import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_semantic_scholar_pdfs(query):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={quote(query)}&limit=5&fields=title,url,openAccessPdf"
    response = requests.get(url, headers={"User-Agent": "AcademicBot/1.0"})
    data = response.json()
    results = []

    for paper in data.get("data", []):
        title = paper.get("title")
        pdf_url = paper.get("openAccessPdf", {}).get("url")
        if pdf_url:
            results.append({
                "title": title,
                "pdf_link": pdf_url
            })
    return results

def get_arxiv_pdfs(query):
    url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&start=0&max_results=10"
    response = requests.get(url, headers={"User-Agent": "AcademicBot/1.0"})
    root = ET.fromstring(response.text)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    results = []
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text.strip()
        pdf_url = None
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('type') == 'application/pdf':
                pdf_url = link.attrib.get('href')
                break
        if pdf_url:
            results.append({
                "title": title,
                "pdf_link": pdf_url
            })
    return results

def get_openalex_pdfs(query):
    url = (
        "https://api.openalex.org/works"
        f"?filter=title.search:{quote(query)},open_access.is_oa:true"
        "&per-page=5"
    )
    response = requests.get(url, headers={"User-Agent": "AcademicBot/1.0"})
    data = response.json()

    results = []
    for work in data.get("results", []):
        title = work.get("title")
        pdf_url = work.get("open_access", {}).get("oa_url")
        if pdf_url:
            results.append({
                "title": title,
                "pdf_link": pdf_url
            })
    return results

def get_springer(query, max_results=5):
    base_url = "https://link.springer.com"
    search_url = f"{base_url}/search?query={quote(query)}&openAccess=true&facet-discipline=%22Computer+Science%22&sortBy=relevance"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AcademicBot/1.0)"
    }

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    headings = soup.find_all("h3", class_="app-card-open__heading", limit=max_results)
    
    for h3 in headings:
        a_tag = h3.find("a", class_="app-card-open__link")
        if a_tag:
            title = a_tag.get_text(strip=True)
            relative_link = a_tag.get("href")
            full_link = urljoin(base_url, relative_link)
            full_link = full_link.replace('article','content/pdf') + '.pdf'
            results.append({"title": title, "pdf_link": full_link})

    return results

def osearch_pdf_links(query):
    sources = {
        "SemanticScholar": get_semantic_scholar_pdfs,
        "ArXiv": get_arxiv_pdfs,
        # "OpenAlex": get_openalex_pdfs,
        'Springer':get_springer
    }

    pdf_results = []

    with ThreadPoolExecutor(max_workers = 4) as executor:
        futures = {executor.submit(func, query): name for name, func in sources.items()}
        
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                pdf_results.extend(future.result())
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"No PDF links found, got error {str(e)}",
                    "data": None
                }
    
    return pdf_results
