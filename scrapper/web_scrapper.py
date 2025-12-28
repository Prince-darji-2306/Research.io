import requests

# Replace this with your actual deployed Render URL
def web_scrapper(query: str, max_results :int = 5):
    BASE_URL = "https://oscraper.onrender.com/search"

    params = {
        "query": query,
        "max_results": max_results
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"No PDF links found, got error {str(e)}",
            "data": None
        }