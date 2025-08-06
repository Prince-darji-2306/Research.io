import streamlit as st
st.set_page_config(page_title="Research.io | AI assistant for Your Research work", layout="wide",page_icon='👨‍🎓')

import os
import json5
from PIL import Image
import time
import ast
import streamlit as st
from agent.ToolPapSe import select_paper
from llm_engine import create_llm, build_messages, clean_state
from utils.doc_loader import download_pdf, find_relevant_image
from langchain.memory import ConversationSummaryBufferMemory
from streamlit_pdf_viewer import pdf_viewer


# ------------------------ Session State Init ------------------------

if "paper_title" not in st.session_state:
    st.session_state.paper_title = None
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'pdf_file' not in st.session_state:
    st.session_state.pdf_file = None
if 'pdf_img' not in st.session_state:
    st.session_state.pdf_img = None
if "selected_view" not in st.session_state:
    st.session_state.selected_view = "Load Paper"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if 'user_accessible' not in st.session_state:
    st.session_state.user_accessible = False
if 'sys_u' not in st.session_state:
    st.session_state.sys_u = False
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ConversationSummaryBufferMemory(
        llm=create_llm(),
        max_token_limit=600,
        return_messages=True
    )

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("static/css/rstyle.css")

# ------------------------ Sidebar ------------------------

st.sidebar.title("📚 Paper Assistant")

# Define buttons
if st.sidebar.button("📄 Load Paper"):
    st.session_state.selected_view = "Load Paper"

if st.sidebar.button("✔️ Check Paper"):
    st.session_state.selected_view = "Check Paper"

if st.sidebar.button("💬 Chat with Paper"):
    st.session_state.selected_view = "Chat with Paper"

if st.sidebar.button("🔍 Search & Select Paper"):
    st.session_state.selected_view = "Search & Select Paper"




# ------------------------ Load Paper UI ------------------------

if st.session_state.selected_view == "Load Paper":
    st.header("📄 Load Your Research Paper")
    uploaded = st.file_uploader("Upload a Paper", type="pdf")
    if uploaded:
        st.session_state.pdf_file = uploaded.getvalue()
        clean_state()

        with st.spinner('Processing The Paper....'):
            st.session_state.pdf_img, st.session_state.vectorstore = download_pdf(uploaded, False)
            st.session_state.paper_title = uploaded.name

        st.session_state.selected_view = 'Chat with Paper'
        st.success("✅ Paper Loaded Successfully! Redirecting to chat...")
        
        time.sleep(1)
        st.rerun()

# ------------------------ Chat with Paper UI ------------------------
elif st.session_state.selected_view == 'Check Paper':
    st.header("✔️ Check Your Research Paper")

    pdf = st.session_state.pdf_file

    if pdf:
        if st.session_state.user_accessible:
            pdf_viewer(pdf, resolution_boost=3)
        else:
            api = st.text_input('Enter Acess API : ')
            if api == os.getenv('ACCESS'):
                st.session_state.user_accessible  = True
                st.rerun()             
    else:
        st.warning("⚠️ Please load a Paper first from the sidebar.")

elif st.session_state.selected_view == "Chat with Paper":
    st.header("🤖 Ask Questions About Your Paper")

    if st.session_state.paper_title:
        st.markdown(f"📝 Paper: {st.session_state.paper_title}")

        # Render existing chat history
        for msg in st.session_state.chat_history:
            if msg["type"] == "user":
                st.markdown(f'<div class="user-msg">{msg["text"]}</div>', unsafe_allow_html=True)
            elif msg['type'] == 'assistant':
                st.markdown(msg["text"])
            elif msg['type'] == 'img':
                img = Image.open(msg["text"])
                st.image(img, width=350)

        query = st.chat_input("Ask a question:")


        if query:
            st.session_state.chat_history.append({"type": "user", "text": query})
            st.markdown(f'<div class="user-msg">{query}</div>', unsafe_allow_html=True)

            img_path = find_relevant_image(query, st.session_state.pdf_img)

            messages = build_messages(query, st.session_state.vectorstore)

            # Prepare placeholders
            think_box = st.empty()
            answer_box = st.empty()

            full_answer = ""
            thinking = ""
            in_think = False

            # Stream tokens as they arrive
            for chunk in create_llm().stream(messages):
                token = chunk.content or ""

                # Handle optional <think> tags
                if "think" in token:
                    in_think = True
                    token = token.replace("think", "")
                if "thought" in token:
                    in_think = False
                    token = token.replace("thought", "")

                if in_think:
                    thinking += token
                    think_box.markdown(
                        f'<div class="thinking-box">🧠 <i>{thinking}</i></div>',
                        unsafe_allow_html=True
                    )
                else:
                    full_answer += token
                    answer_box.markdown(full_answer)
            think_box.empty()
            st.session_state.chat_history.append({"type": "assistant", "text": full_answer})

            if img_path:
                img = Image.open(img_path)
                st.image(img, width=350)
                st.session_state.chat_history.append({'type': 'img', 'text': img_path})

                
            # Clear thinking once done
            st.session_state.chat_memory.save_context(
                inputs={"input": query}, 
                outputs={"output": full_answer}
            )

        
    else:
        st.warning("⚠️ Please load a Paper first from the sidebar.")

# ------------------------ Search & Select Paper UI ------------------------

elif st.session_state.selected_view == "Search & Select Paper":
    st.header("🔍 Search & Select Paper")

    user_query = st.text_input("Enter a research topic/query to search papers:")

    if user_query and user_query.strip() != '' :
        try:
            with st.spinner("Searching and selecting best paper..."):
            
                paper = select_paper(user_query)
        
                try:
                    paper = json5.loads(paper)
                except json5.JSONDecodeError:
                    paper = ast.literal_eval(paper)

                if not paper or "pdf_link" not in paper:
                    raise ValueError("No valid paper found.")

                if 'arxiv' in paper['pdf_link']:
                    paper['pdf_link'] = paper['pdf_link'].replace('abs','pdf')

            with st.spinner('Processing The Paper....'):
                st.success(f"📄 Selected Paper: {paper['title']}")
                
                st.session_state.pdf_img, st.session_state.pdf_file, st.session_state.vectorstore = download_pdf(paper["pdf_link"])

                st.session_state.paper_title = paper["title"]

                clean_state(False)

                st.success("✅ Paper Loaded from Web! Redirecting to chat...")

                st.session_state.selected_view = 'Chat with Paper'
                time.sleep(1)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {e}")
