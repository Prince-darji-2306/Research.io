import os
import requests
from urllib.parse import quote


API_KEY = os.getenv('API_KEY') 
CSE_ID = os.getenv('CSE_ID')

def gsearch_pdf_links(query, max_results=10):
    query = query + ' filetype:pdf'
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": max_results
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Google API request failed: {str(e)}",
            "data": None
        }

    results = response.json().get("items", [])
    if not results:
        return {
            "status": "error",
            "message": "No results returned by Google API.",
            "data": None
        }

    pdf_links = []
    for item in results:
        title = item.get("title")
        
        if 'lecture' in title.lower() or 'presentation' in title.lower():
            continue

        link = item.get("link")
        if link.endswith(".pdf") or ".pdf" in link:
            pdf_links.append({
                "title": title,
                "pdf_link": link
            })

    if not pdf_links:
        return {
            "status": "error",
            "message": "No PDF links found in the search results.",
            "data": None
        }

    return {
        "status": "success",
        "message": "PDF links retrieved successfully.",
        "data": pdf_links
    }
