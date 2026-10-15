import asyncio
import io
import json
import os
import re
from pathlib import Path

import edge_tts
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SERVICES_CSV = BASE_DIR / "services.csv"
INPUT_AUDIO = BASE_DIR / "input" / "user_audio.wav"
OUTPUT_AUDIO = BASE_DIR / "outputs" / "reply.mp3"

app = FastAPI(title="Venixa Voice Agent Backend")


def load_environment() -> dict:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)
    return {
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
        "VOICE_NAME": os.environ.get("VOICE_NAME", "en-US-JennyNeural"),
        "MODEL_NAME": os.environ.get("MODEL_NAME", "gemini-1.0"),
        "AUDIO_FILE": os.environ.get("AUDIO_FILE", str(INPUT_AUDIO)),
        "OUTPUT_FILE": os.environ.get("OUTPUT_FILE", str(OUTPUT_AUDIO)),
    }


def load_services(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing services configuration: {csv_path}")
    df = pd.read_csv(csv_path)
    if "service_name" not in df.columns or "keywords" not in df.columns:
        raise ValueError("services.csv must include columns: service_name, description, keywords")
    df["keywords"] = df["keywords"].fillna("")
    return df


def detect_language(text: str) -> str:
    telugu_chars = set("అబధెంాఇఉఊొఋఌఌఌఏఐఠడఢఘఙఘచఛజఝఞతథదధనణపబమయరలవశషసహళకడఢగహఞ఼ౘౡ్ౄెేొోా౿ఀ")
    has_hinglish = any(ch in text for ch in "ng")
    return "Telugu" if any(ch in text for ch in telugu_chars) else ("English" if has_hinglish else "Telugu")


def transcribe_audio(audio_file: Path, model_name: str = "base") -> str:
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_file))
    return result.get("text", "").strip()


def recommend_service(user_text: str, services_df: pd.DataFrame):
    normalized = user_text.lower()
    best_match, best_score = None, 0
    for _, row in services_df.iterrows():
        keywords = [k for k in str(row["keywords"]).lower().split() if k]
        score = sum(1 for kw in keywords if kw in normalized)
        if score > best_score:
            best_score, best_match = score, row
    if best_match is not None and best_score > 0:
        return best_match["service_name"], best_match.get("description", "")
    return services_df.iloc[0]["service_name"], services_df.iloc[0].get("description", "")


def build_gemini_prompt(transcript: str, services_df: pd.DataFrame) -> str:
    service_lines = [f"- {r['service_name']}: {r.get('description', '')}" for _, r in services_df.iterrows()]
    service_list = "\n".join(service_lines)
    return (
        "You are Venixa, a voice agent that listens to the user, selects the most appropriate service, "
        "and responds in a concise, helpful way.\n"
        "Return a JSON object only, with keys: service_name, reply_text.\n"
        "Available services:\n"
        f"{service_list}\n\n"
        f"User transcript:\n{transcript}\n\n"
        "Do not include extra commentary outside the JSON object."
    )


def parse_gemini_response(raw_output: str, services_df: pd.DataFrame):
    for m in re.finditer(r"\{.*\}", raw_output, re.DOTALL):
        try:
            parsed = json.loads(m.group(0))
            service_name = parsed.get("service_name", "")
            reply_text = parsed.get("reply_text", "")
            if service_name:
                return service_name, reply_text
        except json.JSONDecodeError:
            continue
    for s in services_df["service_name"]:
        if s.lower() in raw_output.lower():
            return s, raw_output.strip()
    return services_df.iloc[0]["service_name"], raw_output.strip()


def call_gemini(prompt: str, api_key: str, model_name: str) -> str:
    if not api_key:
        raise EnvironmentError("Missing GOOGLE_API_KEY in .env")
    try:
        from google import genai
    except ImportError:
        raise RuntimeError(
            "google-genai is required. Install with: pip install google-genai"
        ) from None

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return response.text or ""


async def synthesize_voice(text: str, voice_name: str, output_path: str) -> bytes:
    communicator = edge_tts.Communicate(text=text, voice=voice_name)
    buffer = io.BytesIO()
    await asyncio.get_running_loop().run_in_executor(
        None, lambda: communicator.save(buffer)
    )
    buffer.seek(0)
    return buffer.read()


def validate_service(service_name: str, services_df: pd.DataFrame) -> None:
    if service_name not in services_df["service_name"].values:
        raise ValueError(f"Recommended service '{service_name}' is not listed in services.csv")


app = FastAPI(title="Venixa Voice Agent Backend")

CONFIG = load_environment()
SERVICES_DF = load_services(SERVICES_CSV)


@app.post("/ask", response_class=PlainTextResponse)
async def ask(file: UploadFile = File(..., media_type="audio/*")):
    audio_bytes = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else "wav"

    mime = file.content_type or ""
    language = "te" if "telugu" in mime else "en"
    voice = "te-IN-ShrutiNeural" if language == "te" else "en-US-JennyNeural"

    tmp_path = BASE_DIR / "input" / f"upload_{os.urandom(8).hex()}.{ext}"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        tmp_path.write_bytes(audio_bytes)
        transcript = transcribe_audio(tmp_path, model_name="base")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not transcript:
        raise HTTPException(status_code=400, detail="Could not transcribe audio.")

    services_df = load_services(SERVICES_CSV)
    prompt = build_gemini_prompt(transcript, services_df)
    gemini_output = call_gemini(prompt, CONFIG["GOOGLE_API_KEY"], CONFIG["MODEL_NAME"])
    service_name, reply_text = parse_gemini_response(gemini_output, services_df)
    validate_service(service_name, services_df)

    audio = await synthesize_voice(reply_text, voice, str(OUTPUT_AUDIO))
    return PlainTextResponse(content=reply_text, media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok", "services": SERVICES_DF["service_name"].tolist()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
