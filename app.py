import time
import urllib.parse
import numpy as np
import streamlit as st
from google import genai
from google.genai import types

# ---------- Business settings (client ke hisaab se yahan badlein) ----------
CLINIC_NAME = "Smile Care Dental Clinic"
TAGLINE = "Aap ke daant, hamari zimmedari. Sawal poochein, 24/7."
PHONE = "0300-0000000"
TIMINGS = "Mon - Sat: 10am - 8pm"
LOCATION = "Karachi"
SUGGESTIONS = [
    "Clinic ki timings kya hain?",
    "Root canal ka kitna kharcha hoga?",
    "Teeth whitening ka rate kya hai?",
    "Appointment kaise book karun?",
]
DEBUG = False   # demo/client ko dene se pehle False kar dein
# --------------------------------------------------------------------------

st.set_page_config(page_title=CLINIC_NAME, page_icon="🦷", layout="centered")

# ---------- Teeth watermark (SVG pattern) ----------
TOOTH = (
    "M18 8 C10 8 6 15 8 24 C10 34 13 40 15 52 C16 58 22 58 24 50 "
    "C26 44 28 40 32 40 C36 40 38 44 40 50 C42 58 48 58 49 52 "
    "C51 40 54 34 56 24 C58 15 54 8 46 8 C40 8 36 11 32 11 C28 11 24 8 18 8 Z"
)


def make_bg(a, b, c, size=240):
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<path fill='{a[0]}' fill-opacity='{a[1]}' transform='translate(18 20) rotate(-18 32 32) scale(1.7)' d='{TOOTH}'/>"
        f"<path fill='{b[0]}' fill-opacity='{b[1]}' transform='translate(140 110) rotate(16 32 32) scale(1.3)' d='{TOOTH}'/>"
        f"<path fill='{c[0]}' fill-opacity='{c[1]}' transform='translate(70 150) rotate(-6 32 32) scale(0.9)' d='{TOOTH}'/>"
        "</svg>"
    )
    return 'url("data:image/svg+xml,' + urllib.parse.quote(svg) + '")'


# (colour, opacity): opacity badha kar teeth zyada dikha sakte hain
BG_APP = make_bg(("#7C5CD6", 0.09), ("#9BC400", 0.16), ("#FF6347", 0.07))
BG_HERO = make_bg(("#FFFFFF", 0.10), ("#C8F03A", 0.18), ("#FF6347", 0.14), size=200)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
.hero, .hero *, .chips span, .info-card, [data-testid="stChatMessage"] p,
.stButton button, .small-note {font-family: 'Poppins', sans-serif;}

#MainMenu, footer {visibility: hidden;}
.stApp, [data-testid="stAppViewContainer"] {
    background: __BG_APP__, linear-gradient(160deg, #F3EEFF 0%, #E9E1FB 55%, #F2FBD2 100%) !important;
    background-attachment: fixed !important;
}
[data-testid="stHeader"] {background: transparent !important;}
.block-container {padding-top: 1.4rem; max-width: 780px;}

.hero {
    position: relative; overflow: hidden; display: flex; align-items: center; gap: 18px;
    background: __BG_HERO__, linear-gradient(135deg, #4B2FB0 0%, #7C5CD6 55%, #A892EA 100%);
    padding: 26px 28px; border-radius: 22px; color: #fff;
    box-shadow: 0 14px 34px rgba(91,63,191,0.30);
    border-bottom: 6px solid #C8F03A; margin-bottom: 14px;
}
.hero-icon {
    font-size: 40px; background: #fff; width: 72px; height: 72px; min-width: 72px;
    border-radius: 20px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 0 4px #FF6347;
}
.hero h1 {margin: 0; padding: 0; font-size: 1.6rem; color: #fff !important; font-weight: 700;}
.hero p {margin: 4px 0 8px 0; opacity: 0.95; font-size: 0.95rem; color: #fff;}
.badge {
    display: inline-block; font-size: 0.78rem; font-weight: 600; margin-right: 6px;
    background: #C8F03A; color: #2A1F4D; padding: 4px 12px; border-radius: 20px;
}
.badge2 {
    display: inline-block; font-size: 0.78rem; font-weight: 600;
    background: #FF6347; color: #fff; padding: 4px 12px; border-radius: 20px;
}

.chips {display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 16px 0;}
.chips span {
    background: rgba(255,255,255,0.9); border: 1px solid #D5C9F3; color: #4B2FB0;
    padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500;
}
.chips span::before {content: "● "; color: #9BC400;}

[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.94); border: 1px solid #DCD2F5;
    border-left: 5px solid #B6E21F; border-radius: 16px; padding: 12px 16px;
    box-shadow: 0 4px 14px rgba(91,63,191,0.08);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #EFE9FD; border-left: 5px solid #FF6347;
}

.stButton > button {
    border-radius: 14px; border: 2px solid #FF6347; background: #FFFFFF;
    color: #D9432A; padding: 10px 12px; font-weight: 600;
}
.stButton > button:hover {
    background: #C8F03A; border-color: #C8F03A; color: #2A1F4D;
}

[data-testid="stChatInput"] {
    border: 2px solid #8F76E0; border-radius: 16px; background: #FFFFFF;
}
[data-testid="stChatInputSubmitButton"] {
    background: #FF6347 !important; color: #fff !important; border-radius: 12px;
}
[data-testid="stBottom"] > div {background: transparent !important;}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E4DAFB 0%, #F3EEFF 100%);
    border-right: 1px solid #D5C9F3;
}
.info-card {
    background: #FFFFFF; border-left: 5px solid #C8F03A; border-radius: 12px;
    padding: 10px 14px; margin-bottom: 10px; font-size: 0.88rem; color: #2A1F4D;
    box-shadow: 0 2px 8px rgba(91,63,191,0.08);
}
.info-card b {color: #4B2FB0;}
.small-note {font-size: 0.78rem; color: #6D5BA8; text-align: center; margin-top: 8px;}
</style>
"""
CSS = CSS.replace("__BG_APP__", BG_APP).replace("__BG_HERO__", BG_HERO)
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    f"""
<div class="hero">
  <div class="hero-icon">🦷</div>
  <div>
    <h1>{CLINIC_NAME}</h1>
    <p>{TAGLINE}</p>
    <span class="badge">● Online 24/7</span><span class="badge2">⚡ Instant jawab</span>
  </div>
</div>
<div class="chips">
  <span>English + Urdu + Roman Urdu</span>
  <span>Fees aur timings</span>
  <span>Appointment guide</span>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(f"### 🦷 {CLINIC_NAME}")
    st.markdown(f'<div class="info-card">📍 <b>Location</b><br>{LOCATION}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-card">🕒 <b>Timings</b><br>{TIMINGS}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="info-card">📞 <b>Call / WhatsApp</b><br>{PHONE}</div>', unsafe_allow_html=True)
    if st.button("🗑️ Nayi chat shuru karein", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("English, Urdu ya Roman Urdu mein poochein.")

API_KEY = st.secrets["GEMINI_API_KEY"].split()[0]
client = genai.Client(api_key=API_KEY)

CHAT_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash"]
EMBED_MODEL = "gemini-embedding-001"
BUSY = "Sorry, abhi system busy hai. Thori der baad dobara try karein."


@st.cache_resource
def load_knowledge():
    text = open("data.txt", encoding="utf-8").read()
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    res = client.models.embed_content(model=EMBED_MODEL, contents=chunks)
    vecs = np.array([e.values for e in res.embeddings])
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    return chunks, vecs


chunks, chunk_vecs = load_knowledge()


def with_retry(fn, tries=3):
    for i in range(tries):
        try:
            return fn()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (2 ** i))   # 2, 4 second ruk kar dobara


@st.cache_data(ttl=3600, show_spinner=False)
def embed_query(question):
    res = with_retry(
        lambda: client.models.embed_content(model=EMBED_MODEL, contents=[question])
    )
    return res.embeddings[0].values


def retrieve(question, k=3):
    q = np.array(embed_query(question))
    q = q / np.linalg.norm(q)
    top = np.argsort(chunk_vecs @ q)[::-1][:k]
    return [chunks[i] for i in top]


def answer(question):
    try:
        context = "\n\n".join(retrieve(question))
    except Exception as e:
        st.session_state.last_error = f"Embed: {type(e).__name__}: {str(e)[:200]}"
        return BUSY
    system = (
        f"You are the customer support assistant of {CLINIC_NAME}. "
        "Answer ONLY using the context below. If the answer is not in the context, "
        f"say you are not sure and ask the customer to call the clinic on {PHONE}. "
        "Reply in the same language as the customer (English, Urdu, or Roman Urdu). "
        "Keep answers short, polite and friendly.\n\nContext:\n" + context
    )
    for model in CHAT_MODELS:
        try:
            resp = with_retry(
                lambda: client.models.generate_content(
                    model=model,
                    contents=question,
                    config=types.GenerateContentConfig(system_instruction=system),
                )
            )
            return resp.text
        except Exception as e:
            st.session_state.last_error = f"{model}: {type(e).__name__}: {str(e)[:200]}"
    return BUSY


if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🦷"):
        st.write(m["content"])

prompt = st.chat_input("Apna sawal likhein...")

sugg = st.empty()
if not st.session_state.messages:
    with sugg.container():
        st.markdown("**✨ Jaldi poochein:**")
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

if DEBUG and st.session_state.get("last_error"):
    st.sidebar.caption("Debug: " + st.session_state.last_error)
