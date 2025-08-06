from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from embedding import load_model
import tempfile
import requests
import fitz
import os
import io
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def find_relevant_image(user_query, pdf_list):
    if not pdf_list:
        return None

    # Step 1: Extract captions
    captions = [caption for _, caption in pdf_list]

    embedding_model = load_model()
    
    # Step 2: Embed captions
    caption_embeddings = embedding_model.embed_documents(captions)

    # Step 3: Embed user query
    query_embedding = embedding_model.embed_query(user_query)

    # Step 4: Compute cosine similarity
    similarities = cosine_similarity([query_embedding], caption_embeddings)[0]

    # Step 5: Get best matching image index
    
    if max(similarities) >= 0.6:
        best_index = np.argmax(similarities)
        return pdf_list[best_index][0]
    return None

def split_documents(documents, chunk_size=700, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)


def load_pdf(file_path):
    try:
        loader = PyMuPDFLoader(file_path)
        documents = split_documents(loader.load())
        embeddings = load_model()
        return FAISS.from_documents(documents, embeddings)
    except Exception as e:
        raise RuntimeError(f"Failed to load and embed PDF: {e}")


def load_img(file_path):
    images_with_captions = []
    try:
        doc = fitz.open(file_path)

        for page_number in range(len(doc)):
            page = doc[page_number]
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                image.save(temp_file, format="JPEG")
                temp_file_path = temp_file.name
                temp_file.close()

                caption = None
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if "lines" in b and b["type"] == 0:
                        text = " ".join(
                            [span["text"] for line in b["lines"] for span in line["spans"]]
                        )
                        if "figure" in text.lower() or "fig." in text.lower():
                            caption = text
                            break

                if caption:
                    images_with_captions.append([temp_file_path, caption])
                else:
                    os.remove(temp_file_path)

    except Exception as e:
        raise RuntimeError(f"Failed to extract images: {e}")

    return images_with_captions


def download_pdf(file: str, download=True):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            if download:
                response = requests.get(file)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            else:
                tmp_file.write(file.read())
                tmp_path = tmp_file.name

        vectorstore = load_pdf(tmp_path)
        pdf_list = load_img(tmp_path)

    except Exception as e:
        raise RuntimeError(f"Failed to process PDF: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    if download:
        return pdf_list, response.content, vectorstore
    else:
        return pdf_list, vectorstore
