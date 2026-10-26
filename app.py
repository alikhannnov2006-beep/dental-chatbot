import time
import numpy as np
import streamlit as st
from google import genai
from google.genai import types

# ---------- Business settings (client ke hisaab se yahan badlein) ----------
CLINIC_NAME = "Smile Care Dental Clinic"
TAGLINE = "Aap ke sawalon ke jawab, 24/7"
PHONE = "0300-0000000"
TIMINGS = "Mon - Sat: 10am - 8pm"
LOCATION = "Karachi"
SUGGESTIONS = [
    "Clinic ki timings kya hain?",
    "Root canal ka kitna kharcha hoga?",
    "Teeth whitening ka rate kya hai?",
    "Appointment kaise book karun?",
]
# --------------------------------------------------------------------------

st.set_page_config(page_title=CLINIC_NAME, page_icon="🦷", layout="centered")

CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.5rem; max-width: 760px;}
.hero {
    display: flex; align-items: center; gap: 16px;
    background: linear-gradient(135deg, #0E9F9A 0%, #2BC4BC 100%);
    padding: 22px 24px; border-radius: 18px; color: white;
    box-shadow: 0 8px 24px rgba(14,159,154,0.25); margin-bottom: 18px;
}
.hero-icon {
    font-size: 40px; background: rgba(255,255,255,0.22);
    width: 64px; height: 64px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
}
.hero h1 {margin: 0; font-size: 1.55rem; color: white; padding: 0;}
.hero p {margin: 2px 0 0 0; opacity: 0.92; font-size: 0.95rem;}
.badge {
    display: inline-block; margin-top: 8px; font-size: 0.78rem;
    background: rgba(255,255,255,0.22); padding: 3px 10px; border-radius: 20px;
}
[data-testid="stChatMessage"] {
    background: #FFFFFF; border: 1px solid #E3F0EF;
    border-radius: 16px; padding: 12px 16px;
    box-shadow: 0 2px 8px rgba(18,52,59,0.05);
}
.stButton > button {
    border-radius: 12px; border: 1px solid #BFE5E2; background: #FFFFFF;
    color: #0B6E6A; padding: 10px 12px; font-weight: 500;
}
.stButton > button:hover {
    border-color: #0E9F9A; background: #E9F8F7; color: #0B6E6A;
}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #E3F0EF;}
.small-note {font-size: 0.78rem; color: #6B8A8E; text-align: center; margin-top: 6px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    f"""
<div class="hero">
  <div class="hero-icon">🦷</div>
  <div>
    <h1>{CLINIC_NAME}</h1>
    <p>{TAGLINE}</p>
    <span class="badge">● Online 24/7</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(f"### 🦷 {CLINIC_NAME}")
    st.markdown(f"📍 **Location:** {LOCATION}")
    st.markdown(f"🕒 **Timings:** {TIMINGS}")
    st.markdown(f"📞 **Call / WhatsApp:** {PHONE}")
    st.divider()
    if st.button("🗑️ Nayi chat shuru karein", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("English, Urdu ya Roman Urdu mein poochein.")

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
    try:
        context = "\n\n".join(retrieve(question))
    except Exception:
        return "Sorry, abhi system busy hai. Thori der baad dobara try karein."
    system = (
        f"You are the customer support assistant of {CLINIC_NAME}. "
        "Answer ONLY using the context below. If the answer is not in the context, "
        f"say you are not sure and ask the customer to call the clinic on {PHONE}. "
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
    return "Sorry, abhi system busy hai. Thori der baad dobara try karein."


if "messages" not in st.session_state:
    st.session_state.messages = []

# purani chat dikhayein
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🦷"):
        st.write(m["content"])

prompt = st.chat_input("Apna sawal likhein...")

# sample sawal (sirf khali chat par)
sugg = st.empty()
if not st.session_state.messages:
    with sugg.container():
        st.markdown("**Jaldi poochein:**")
        cols = st.columns(2)
        for i, s in enumerate(SUGGESTIONS):
            if cols[i % 2].button(s, use_container_width=True, key=f"sugg{i}"):
                prompt = s

if prompt:
    sugg.empty()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.write(prompt)
    with st.chat_message("assistant", avatar="🦷"):
        with st.spinner("Jawab likh raha hoon..."):
            reply = answer(prompt)
        st.write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

st.markdown(
    '<div class="small-note">AI assistant. Pakki maloomat ke liye clinic se rabta karein.</div>',
    unsafe_allow_html=True,
)
