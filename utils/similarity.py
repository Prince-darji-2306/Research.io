import ast
import json
import numpy as np
from embedding import load_model

# Initialize the embedding model
embedding_model = load_model()

def select_relevant_papers(all_metadata, similarity_threshold: float = 0.96):
    try:
        all_metadata = json.loads(all_metadata)
    except json.JSONDecodeError:
        all_metadata = ast.literal_eval(all_metadata)

    user_query = all_metadata['query']
    papers = all_metadata['candidates']

    all_titles = []
    title_to_info = {}
    seen = set()

    for paper in papers:
        title = paper["title"].strip().replace("\n", " ")
        key = (title.lower(), paper["pdf_link"])
        if key in seen:
            continue
        seen.add(key)
        all_titles.append(title)
        title_to_info[title] = {
            "pdf": paper["pdf_link"]
        }

    if not all_titles:
        return []

    # Compute embeddings and cosine similarity
    title_embeddings = embedding_model.embed_documents(all_titles)
    query_embedding = embedding_model.embed_query(user_query)

    similarities = np.dot(title_embeddings, query_embedding) / (
        np.linalg.norm(title_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Step 1: Exact match if above threshold
    max_sim_idx = int(np.argmax(similarities))
    max_score = float(similarities[max_sim_idx])
    if max_score >= similarity_threshold:
        title = all_titles[max_sim_idx]
        return [{
            "title": title,
            "pdf": title_to_info[title]["pdf"],
            "score": max_score
        }]

    # Step 2: Return up to 3 papers within 0.1 similarity range of max
    top_papers = [
        {
            "title": all_titles[i],
            "pdf": title_to_info[all_titles[i]]["pdf"],
            "score": float(score)
        }
        for i, score in enumerate(similarities)
        if abs(max_score - score) <= 0.1
    ]

    top_papers = sorted(top_papers, key=lambda x: x["score"], reverse=True)
    return top_papers[:3]