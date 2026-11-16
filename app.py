import io, os, json, tempfile, zipfile, soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response
from vieneu_tts import VieNeuTTS

app = FastAPI(title="KVietSub VieNeu-TTS Clone")
tts = VieNeuTTS(device="cpu")

@app.get("/")
def home():
    return {"status": "ok", "model": "VieNeu-TTS Voice Cloning"}

@app.post("/api/clone_tts")
async def clone_tts(
    lines_json: str = Form(...),
    ref_audio: UploadFile = File(None)
):
    lines = json.loads(lines_json)
    temp_ref_path = None

    if ref_audio is not None:
        suffix = os.path.splitext(ref_audio.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await ref_audio.read())
            temp_ref_path = tmp.name

    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in lines:
                idx = item.get("id", 0)
                text = item.get("text", "").strip()
                if not text:
                    continue

                if temp_ref_path and os.path.exists(temp_ref_path):
                    wav, sr = tts.synthesize(text=text, ref_audio_path=temp_ref_path)
                else:
                    wav, sr = tts.synthesize(text=text)

                wav_io = io.BytesIO()
                sf.write(wav_io, wav, sr, format="WAV")
                zf.writestr(f"line_{idx:04d}.wav", wav_io.getvalue())
    finally:
        if temp_ref_path and os.path.exists(temp_ref_path):
            os.remove(temp_ref_path)

    return Response(content=zip_buffer.getvalue(), media_type="application/zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
