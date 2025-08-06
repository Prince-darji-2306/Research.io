import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

API = os.getenv('GROQ')

if 'sys_u' not in st.session_state:
    st.session_state.sys_u = False

@st.cache_resource
def create_llm():
    return ChatGroq(
        api_key = API,
        model="openai/gpt-oss-120b",
        temperature=0.3,  # adjust for creativity
    )

def get_context(query, vectorstore):
    docs = vectorstore.similarity_search(query)
    context = ""
    for i, doc in enumerate(docs):
        page = doc.metadata.get("page_label", doc.metadata.get("page", "N/A"))
        source = doc.metadata.get("source", "unknown")
        context += f"\n---\n[Page {page} from {source}]\n{doc.page_content.strip()}\n"

    return (context)

def build_messages(query: str, vectorstore):
    context = get_context(query, vectorstore)

    memory_msgs = st.session_state.chat_memory.load_memory_variables({})["history"]

    messages = []

    if not st.session_state.sys_u:
        messages.append(SystemMessage(content=os.getenv('SYSTEM')))
        st.session_state.sys_u = True

    messages.extend(memory_msgs)

    prompt = f"""
    {os.getenv('THINK')}

    Context:
    {context}

    User Query:
    {query}

    """.strip()

    messages.append(HumanMessage(content= prompt))

    return messages

def clean_state(mode = True):
    st.session_state.pdf_img = None
    st.session_state.user_accessible = mode
    st.session_state.chat_history = []
    st.session_state.chat_memory.clear()
    

