import streamlit as st
import pandas as pd
import os
import re
import asyncio
import io
import tempfile
import edge_tts
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Venixa — Ask. Listen. Connect.",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp, .main { background-color: #F7F1E8 !important; }
.block-container {
    max-width: 680px !important;
    padding: 48px 24px 80px !important;
    font-family: 'Inter', -apple-system, sans-serif;
    color: #2D2D2D;
}
.stApp::before {
    content: ''; position: fixed; top: -200px; right: -200px;
    width: 600px; height: 600px; border-radius: 50%;
    background: radial-gradient(circle, rgba(217,195,165,0.18) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
}
.v-hero { text-align: center; padding: 64px 32px 48px; margin-bottom: 8px; }
.v-wordmark { font-size: 48px; font-weight: 700; color: #2D2D2D; letter-spacing: -1.5px; line-height: 1; margin-bottom: 12px; }
.v-wordmark span { color: #CDB493; }
.v-tagline { font-size: 15px; font-weight: 400; color: #6B6B6B; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 14px; }
.v-desc { font-size: 14px; color: #9A8A78; line-height: 1.7; max-width: 380px; margin: 0 auto 24px; font-weight: 300; }
.v-pills { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.v-pill { background: #FFFDF8; border: 1px solid #ECE4D8; color: #9A8A78; font-size: 11px; font-weight: 500; padding: 5px 14px; border-radius: 20px; }
.v-status { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 0 0 36px; }
.v-status-dot { width: 7px; height: 7px; border-radius: 50%; background: #CDB493; animation: breathe 2.5s ease-in-out infinite; }
@keyframes breathe { 0%,100% { opacity:0.4; transform:scale(1); } 50% { opacity:1; transform:scale(1.3); } }
.v-status-text { font-size: 12px; color: #9A8A78; font-weight: 400; letter-spacing: 0.5px; }
.v-card {
    background: #FFFDF8; border: 1px solid #ECE4D8; border-radius: 24px; padding: 32px; margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(180,150,100,0.06), 0 12px 40px rgba(180,150,100,0.04);
    transition: box-shadow 0.3s ease, transform 0.2s ease;
}
.v-card:hover { box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 6px 24px rgba(180,150,100,0.10), 0 16px 48px rgba(180,150,100,0.06); transform: translateY(-1px); }
.v-card-label { font-size: 10px; font-weight: 600; color: #CDB493; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 6px; }
.v-card-title { font-size: 20px; font-weight: 600; color: #2D2D2D; letter-spacing: -0.3px; margin-bottom: 4px; }
.v-card-sub { font-size: 13px; color: #9A8A78; font-weight: 400; margin-bottom: 20px; }
.v-divider { height: 1px; background: #ECE4D8; margin: 20px 0; }
[data-testid="stFileUploader"] { background: transparent !important; }
[data-testid="stFileUploader"] section {
    background: #F7F1E8 !important; border: 1.5px dashed #D9C3A5 !important;
    border-radius: 16px !important; padding: 28px 20px !important; transition: all 0.2s ease !important;
}
[data-testid="stFileUploader"] section:hover { border-color: #CDB493 !important; background: #F2EAD8 !important; }
[data-testid="stFileUploader"] section p, [data-testid="stFileUploader"] section span { color: #9A8A78 !important; font-size: 13px !important; }
.v-bubble-wrap { margin-top: 20px; }
.v-bubble-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.v-bubble-avatar { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #D9C3A5, #CDB493); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; color: #FFFDF8; flex-shrink: 0; }
.v-bubble-name { font-size: 12px; font-weight: 600; color: #2D2D2D; }
.v-bubble { background: #F7F1E8; border: 1px solid #ECE4D8; border-radius: 4px 16px 16px 16px; padding: 16px 18px; font-size: 15px; color: #2D2D2D; line-height: 1.7; white-space: pre-wrap; }
.v-response-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.v-response-dot { width: 8px; height: 8px; border-radius: 50%; background: #CDB493; flex-shrink: 0; }
.v-response-label { font-size: 11px; font-weight: 600; color: #CDB493; letter-spacing: 1.5px; text-transform: uppercase; }
.v-response-text { font-size: 15px; color: #2D2D2D; line-height: 1.9; white-space: pre-wrap; font-weight: 400; }
.v-response-border { border-left: 2px solid #ECE4D8; padding-left: 16px; margin-top: 4px; }
.v-audio-card { background: #F7F1E8; border: 1px solid #ECE4D8; border-radius: 16px; padding: 20px; margin-top: 16px; }
.v-audio-label { font-size: 11px; font-weight: 600; color: #9A8A78; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 12px; }
audio { width: 100%; height: 36px; border-radius: 8px; accent-color: #CDB493; }
.v-how-row { display: flex; gap: 14px; align-items: flex-start; padding: 14px 0; border-bottom: 1px solid #F0E8DC; }
.v-how-row:last-child { border-bottom: none; }
.v-how-num { width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0; background: #F7F1E8; border: 1px solid #ECE4D8; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; color: #CDB493; }
.v-how-title { font-size: 13px; font-weight: 600; color: #2D2D2D; margin-bottom: 2px; }
.v-how-desc  { font-size: 12px; color: #9A8A78; line-height: 1.6; }
.v-how-badge { display: inline-block; margin-top: 5px; background: #F0E8DC; border: 1px solid #ECE4D8; color: #9A8A78; font-size: 9px; font-weight: 600; padding: 1px 8px; border-radius: 20px; letter-spacing: 0.5px; }
div.stButton > button {
    background: #2D2D2D !important; color: #FFFDF8 !important;
    font-family: 'Inter', sans-serif !important; font-weight: 500 !important;
    font-size: 14px !important; border: none !important; border-radius: 12px !important;
    padding: 13px 0 !important; width: 100% !important;
    box-shadow: 0 2px 8px rgba(45,45,45,0.15) !important; transition: all 0.2s ease !important;
}
div.stButton > button:hover { background: #1A1A1A !important; box-shadow: 0 4px 16px rgba(45,45,45,0.25) !important; transform: translateY(-1px) !important; }
div.stDownloadButton > button { background: transparent !important; color: #6B6B6B !important; border: 1px solid #ECE4D8 !important; border-radius: 10px !important; font-size: 13px !important; width: 100% !important; padding: 10px 0 !important; transition: all 0.2s ease !important; }
div.stDownloadButton > button:hover { border-color: #CDB493 !important; color: #2D2D2D !important; background: #F7F1E8 !important; }
.stSpinner > div { border-top-color: #CDB493 !important; }
.stError { background: #FDF5F5 !important; border: 1px solid #E8C8C0 !important; border-radius: 12px !important; font-size: 13px !important; }
[data-testid="stExpander"] { background: #FFFDF8 !important; border: 1px solid #ECE4D8 !important; border-radius: 16px !important; }
.v-footer { text-align: center; padding-top: 40px; margin-top: 16px; }
.v-footer-logo { font-size: 18px; font-weight: 700; color: #D9C3A5; margin-bottom: 6px; }
.v-footer-text { font-size: 11px; color: #C4B49A; letter-spacing: 0.5px; line-height: 1.8; }
.v-footer-sep { color: #D9C3A5; margin: 0 6px; }
</style>
""", unsafe_allow_html=True)

# ── API & Data Setup ──────────────────────────────────────────────────────────
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    st.error("Missing GROQ_API_KEY in .env file.")
    st.stop()

groq_client = Groq(api_key=groq_key)

try:
    services_df     = pd.read_csv("services.csv")
    service_names   = services_df["service"].tolist()
    service_context = services_df.to_string(index=False)
except FileNotFoundError:
    st.error("services.csv not found.")
    st.stop()

MIME_MAP = {"mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4", "ogg": "audio/ogg"}

# Telugu female voice in edge-tts
TELUGU_VOICE  = "te-IN-ShrutiNeural"
ENGLISH_VOICE = "en-IN-NeerjaNeural"

# ── Helpers ───────────────────────────────────────────────────────────────────
def transcribe(audio_bytes: bytes, ext: str) -> str | None:
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            with open(tmp, "rb") as f:
                result = groq_client.audio.transcriptions.create(
                    file=(f"audio.{ext}", f.read()),
                    model="whisper-large-v3",
                    language="te",
                    response_format="text",
                )
            return result.strip() if isinstance(result, str) else result.text.strip()
        finally:
            os.remove(tmp)
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

def get_reply(user_text: str) -> str | None:
    system = f"""You are Venixa, a native Telugu-speaking female AI voice assistant for Hindu rituals and spiritual services.

PERSONALITY:
- Warm, calm, respectful, conversational — like a trusted elder sister or family guide.
- Speak fluent, natural Telugu with authentic expressions. Never sound robotic.
- Understand Telugu, English, Sanskrit, and mixed Tenglish naturally.
- Use natural expressions like "అలాగే", "తప్పకుండా", "మీకు చాలా మేలు జరుగుతుంది" where fitting.
- NEVER use bullet points, asterisks, markdown, or formatting symbols.
- Write as if speaking aloud — natural pauses with commas, warm tone.

AVAILABLE SERVICES:
{service_context}

RULES:
1. Detect user language and reply in that same language. If Telugu or Tenglish, always reply in Telugu.
2. Match query to services above. Give service name, price, duration, warm description.
3. If no match, say so warmly in user's language.
4. Keep it concise and conversational — spoken style, not written.
5. End with: "బుక్ చేసుకోవడానికి +91 90300 56111 కి కాల్ చేయండి" for Telugu, "To book, call +91 90300 56111" for English.

Services list: {', '.join(service_names)}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_text}
            ],
            temperature=0.7,
            max_tokens=512,
        )
        raw   = response.choices[0].message.content
        reply = re.sub(r"\*+|#+|`+", "", raw).strip()
        return reply
    except Exception as e:
        st.error(f"Response error: {e}")
        return None

def detect_language(text: str) -> str:
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Detect the language of this text. Return ONLY one word: English, Telugu, Hindi, Tamil, or Kannada.\nText: {text}"}],
            max_tokens=5,
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return "Telugu"

async def _tts(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text=text, voice=voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.getvalue()

def text_to_speech(text: str, lang: str) -> bytes | None:
    try:
        voice = TELUGU_VOICE if lang.lower() == "telugu" else ENGLISH_VOICE
        return asyncio.run(_tts(text, voice))
    except Exception as e:
        st.error(f"Voice error: {e}")
        return None

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="v-hero">
  <div class="v-wordmark">Veni<span>xa</span></div>
  <div class="v-tagline">Ask &nbsp;·&nbsp; Listen &nbsp;·&nbsp; Connect</div>
  <div class="v-desc">Native Telugu voice guidance for rituals,<br>poojas, and spiritual services.</div>
  <div class="v-pills">
    <span class="v-pill">🇮🇳 Telugu</span>
    <span class="v-pill">English</span>
    <span class="v-pill">Sanskrit</span>
    <span class="v-pill">Tenglish</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── STATUS ────────────────────────────────────────────────────────────────────
status_map = {
    "idle":        "Ready to listen",
    "uploaded":    "Audio received — ready to transcribe",
    "transcribed": "Understood — ready to respond",
    "replied":     "Response ready — generate voice",
    "complete":    "Complete",
}
if "audio_bytes" in st.session_state:       s = "complete"
elif "reply" in st.session_state:           s = "replied"
elif "user_text" in st.session_state:       s = "transcribed"
elif "uploaded_bytes" in st.session_state:  s = "uploaded"
else:                                        s = "idle"

st.markdown(f"""
<div class="v-status">
  <div class="v-status-dot"></div>
  <div class="v-status-text">{status_map[s]}</div>
</div>
""", unsafe_allow_html=True)

# ── CARD 1 — UPLOAD ───────────────────────────────────────────────────────────
st.markdown("""
<div class="v-card">
  <div class="v-card-label">Step 01</div>
  <div class="v-card-title">Your Voice</div>
  <div class="v-card-sub">Upload a recording of your question in Telugu or English</div>
  <div class="v-divider"></div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("", type=["mp3", "wav", "m4a", "ogg"], label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

if uploaded:
    st.audio(uploaded)
    if st.session_state.get("uploaded_name") != uploaded.name:
        st.session_state.uploaded_bytes = uploaded.getvalue()
        st.session_state.uploaded_name  = uploaded.name
        st.session_state.uploaded_ext   = uploaded.name.rsplit(".", 1)[-1].lower()
        for k in ["user_text", "reply", "audio_bytes", "lang"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── CARD 2 — TRANSCRIBE ───────────────────────────────────────────────────────
if "uploaded_bytes" in st.session_state:
    st.markdown("""
    <div class="v-card">
      <div class="v-card-label">Step 02</div>
      <div class="v-card-title">Understanding</div>
      <div class="v-card-sub">Groq Whisper converts your voice to text</div>
      <div class="v-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("Transcribe →"):
        with st.spinner("Listening..."):
            text = transcribe(st.session_state.uploaded_bytes, st.session_state.uploaded_ext)
        if text:
            st.session_state.user_text = text
            for k in ["reply", "audio_bytes", "lang"]:
                st.session_state.pop(k, None)
            st.rerun()

    if "user_text" in st.session_state:
        st.markdown(f"""
        <div class="v-bubble-wrap">
          <div class="v-bubble-meta">
            <div class="v-bubble-avatar">Y</div>
            <div class="v-bubble-name">You said</div>
          </div>
          <div class="v-bubble">{st.session_state.user_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── CARD 3 — RESPONSE ─────────────────────────────────────────────────────────
if "user_text" in st.session_state:
    st.markdown("""
    <div class="v-card">
      <div class="v-card-label">Step 03</div>
      <div class="v-card-title">Guidance</div>
      <div class="v-card-sub">Personalized response based on your query</div>
      <div class="v-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("Get Response →"):
        with st.spinner("Preparing your guidance..."):
            reply = get_reply(st.session_state.user_text)
            lang  = detect_language(st.session_state.user_text)
        if reply:
            st.session_state.reply = reply
            st.session_state.lang  = lang
            st.session_state.pop("audio_bytes", None)
            st.rerun()

    if "reply" in st.session_state:
        lang = st.session_state.get("lang", "Telugu")
        st.markdown(f"""
        <div style="margin-top:16px;">
          <div class="v-response-header">
            <div class="v-response-dot"></div>
            <div class="v-response-label">Venixa &nbsp;·&nbsp; {lang}</div>
          </div>
          <div class="v-response-border">
            <div class="v-response-text">{st.session_state.reply}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── CARD 4 — VOICE ────────────────────────────────────────────────────────────
if "reply" in st.session_state:
    st.markdown("""
    <div class="v-card">
      <div class="v-card-label">Step 04</div>
      <div class="v-card-title">Voice Reply</div>
      <div class="v-card-sub">Listen to your personalized guidance</div>
      <div class="v-divider"></div>
    """, unsafe_allow_html=True)

    if st.button("Generate Voice →"):
        with st.spinner("Generating voice..."):
            lang        = st.session_state.get("lang", "Telugu")
            audio_bytes = text_to_speech(st.session_state.reply, lang)
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes
            st.rerun()

    if "audio_bytes" in st.session_state:
        st.markdown('<div class="v-audio-card"><div class="v-audio-label">Now Playing</div>', unsafe_allow_html=True)
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("Download audio", data=st.session_state.audio_bytes, file_name="venixa_response.mp3", mime="audio/mp3")

    st.markdown("</div>", unsafe_allow_html=True)

# ── HOW IT WORKS ──────────────────────────────────────────────────────────────
with st.expander("How Venixa works"):
    st.markdown("""
<div style="padding:4px 0;">
  <div class="v-how-row">
    <div class="v-how-num">1</div>
    <div><div class="v-how-title">Voice Input</div>
    <div class="v-how-desc">Upload MP3, WAV, M4A or OGG in Telugu, English, or Tenglish.</div>
    <span class="v-how-badge">Any format</span></div>
  </div>
  <div class="v-how-row">
    <div class="v-how-num">2</div>
    <div><div class="v-how-title">Speech Recognition</div>
    <div class="v-how-desc">Groq Whisper Large v3 transcribes your audio with high accuracy for Telugu and Indian languages.</div>
    <span class="v-how-badge">Groq Whisper Large v3</span></div>
  </div>
  <div class="v-how-row">
    <div class="v-how-num">3</div>
    <div><div class="v-how-title">Intelligent Response</div>
    <div class="v-how-desc">Llama 3.3 70B matches your query to Venixa's services and replies in your language with pricing and details.</div>
    <span class="v-how-badge">Llama 3.3 70B</span></div>
  </div>
  <div class="v-how-row">
    <div class="v-how-num">4</div>
    <div><div class="v-how-title">Voice Synthesis</div>
    <div class="v-how-desc">Microsoft Edge TTS with te-IN-ShrutiNeural — a native Telugu female voice — speaks the response naturally.</div>
    <span class="v-how-badge">te-IN-ShrutiNeural</span></div>
  </div>
  <div class="v-how-row">
    <div class="v-how-num">5</div>
    <div><div class="v-how-title">Delivery</div>
    <div class="v-how-desc">Play or download the voice reply. Full voice-to-voice cycle, completely free.</div>
    <span class="v-how-badge">100% Free</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="v-footer">
  <div class="v-footer-logo">Venixa</div>
  <div class="v-footer-text">
    © 2025 Venixa
    <span class="v-footer-sep">·</span> Groq Whisper Large v3
    <span class="v-footer-sep">·</span> Llama 3.3 70B
    <span class="v-footer-sep">·</span> Edge TTS te-IN-ShrutiNeural
  </div>
</div>
""", unsafe_allow_html=True)
