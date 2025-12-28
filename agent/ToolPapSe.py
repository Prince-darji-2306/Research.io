import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentType
from langchain.agents import initialize_agent, Tool
from scrapper.google_scrapper import gsearch_pdf_links
from scrapper.open_access import osearch_pdf_links
from scrapper.web_scrapper import web_scrapper
from utils.similarity import select_relevant_papers

load_dotenv()

API = os.getenv('GROQ')

llm = ChatGroq(
    api_key = API,
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.1,  # adjust for creativity
)

# --- Wrap scrapers as LangChain Tools ---
tools = [
    Tool(
        name="GoogleScraper",
        func = gsearch_pdf_links,
        description=(
            "General-purpose API for searching research papers via Google. "
            "It can fetch a wide variety of research papers—including those not commonly indexed on popular platforms—"
            "but should be used sparingly to avoid hitting API limits or returning noisy results."
        )
    ),
    Tool(
        name="OpenAccessScraper",
        func = osearch_pdf_links,
        description=(
            "Scrapes open-access research paper links from multiple niches. "
            "Use this to fetch academic papers from open-access sources (e.g., arXiv, PubMed, Semantic Scholar, OpenAlex). "
            "Ideal for discovering both the latest and older open-access papers, "
            "covering all open access research content."
        )
    ),
    Tool(
        name="WebScrapper",
        func = web_scrapper,
        description=(
            "Use this tool to scrape research papers from Google Search when other sources are insufficient. "
            "It returns a list of paper metadata based on a user query. "
        )
    ),
    
    Tool(
        name="SelectRelevantPapers",
        func=select_relevant_papers,
        description=(
            "Use this to select the most relevant papers. "
            "Input must be a JSON object with two keys: 'query' (str) and 'candidates' (list of paper metadata dicts). "
            "Returns the top 3 relevant papers as a list. If only 1 is found, it returns a single-item list."
        )
    ),
]

# --- Initialize a zero-shot agent with built-in fallback logic ---
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    max_iterations=4,
    early_stopping_method="generate"
)

# --- Paper Selector ---
def select_paper(query: str) -> dict:
    """
    Full selection pipeline via agent:
    1. Agent scrapes papers.
    2. Agent ranks papers.
    3. Agent returns 1 final paper.

    Args:
        query (str): Paper query/topic.
    Returns:
        dict: Chosen paper metadata.
    """

    prompt = f"""
    You are a helpful and systematic research assistant.

    You have access to the following 4 tools:

    1. OpenAccessScraper — Use this to fetch academic papers from open-access sources like arXiv and Semantic Scholar.
    2. GoogleScraper - Use this to fetch academic papers from Google API.
    2. WebScraper — Use this to fetch academic papers from Google Search. Only use this if the results are insufficient or missing.
    3. SelectRelevantPapers — Use this to select the top 3 most relevant papers from a list based on the query.

    Your task is to find the most relevant research paper for the query: "{query}"

    Follow these rules STRICTLY:

    Step 1: First, use ONLY ONE scraper tool — to fetch candidate papers.
    
    Step-2 : If results does not look good or insufficient, irrelevant, or missing, you MAY switch and call the other scraper tool.

    Step 2: Pass the fetched candidates to SelectRelevantPapers using the following input format:
    {{
    "query": "{query}",
    "candidates": [ ...paper metadata... ]
    }}

    Step 3: Select and return ONE best-matching paper from the result of SelectRelevantPapers.

    Step 4: If title is attention is all you need then return link : https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf in told format.
    Return output in this format exactly:

    {{
    "title": "...",
    "pdf_link": "..."
    }}
    """

    result = agent.invoke(prompt)
    return result['output']