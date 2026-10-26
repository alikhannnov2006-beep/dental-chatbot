import time
import numpy as np
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Smile Care Assistant", page_icon="🦷")
st.title("🦷 Smile Care Dental Clinic")
st.caption("AI assistant: English, Urdu ya Roman Urdu mein poochein")

API_KEY = st.secrets["GEMINI_API_KEY"].split()[0]
client = genai.Client(api_key=API_KEY)

CHAT_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash"]
EMBED_MODEL = "gemini-embedding-001"


@st.cache_resource
def load_knowledge():
    text = open("data.txt", encoding="utf-8").read()
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    res = client.models.embed_content(model=EMBED_MODEL, contents=chunks)
    vecs = np.array([e.values for e in res.embeddings])
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    return chunks, vecs


chunks, chunk_vecs = load_knowledge()


def retrieve(question, k=3):
    res = client.models.embed_content(model=EMBED_MODEL, contents=[question])
    q = np.array(res.embeddings[0].values)
    q = q / np.linalg.norm(q)
    top = np.argsort(chunk_vecs @ q)[::-1][:k]
    return [chunks[i] for i in top]


def answer(question):
    context = "\n\n".join(retrieve(question))
    system = (
        "You are the customer support assistant of Smile Care Dental Clinic. "
        "Answer ONLY using the context below. If the answer is not in the context, "
        "say you are not sure and ask the customer to call the clinic. "
        "Reply in the same language as the customer (English, Urdu, or Roman Urdu). "
        "Keep answers short, polite and friendly.\n\nContext:\n" + context
    )
    for model in CHAT_MODELS:
        for _ in range(3):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=question,
                    config=types.GenerateContentConfig(system_instruction=system),
                )
                return resp.text
            except Exception:
                time.sleep(3)
    return "Sorry, abhi system busy hai. Thori der baad try karein."


if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if q := st.chat_input("Apna sawal likhein..."):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        with st.spinner("Soch raha hoon..."):
            a = answer(q)
        st.write(a)
    st.session_state.messages.append({"role": "assistant", "content": a})
