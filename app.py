import io, os, zipfile, soundfile as sf
from fastapi import FastAPI, Body
from fastapi.responses import Response, JSONResponse
from vieneu_tts import VieNeuTTS

app = FastAPI(title="KVietSub VieNeu-TTS")
tts = VieNeuTTS(device="cpu")
VOICE_MAP = {"NAM_TRE": "voices/nam_tre.wav", "NU_CHINH": "voices/nu_chinh.wav", "LAO_GIA": "voices/lao_gia.wav", "DAN_TRUYEN": "voices/dan_truyen.wav"}

@app.get("/")
def home(): return {"status": "ok"}

@app.post("/api/batch_tts")
async def batch_tts(payload: dict = Body(...)):
    lines = payload.get("lines", [])
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in lines:
            idx, role, text = item.get("id", 0), item.get("role", "DAN_TRUYEN"), item.get("text", "").strip()
            if not text: continue
            ref = VOICE_MAP.get(role, VOICE_MAP["DAN_TRUYEN"])
            wav, sr = tts.synthesize(text=text, ref_audio_path=ref) if os.path.exists(ref) else tts.synthesize(text=text)
            wav_io = io.BytesIO()
            sf.write(wav_io, wav, sr, format="WAV")
            zf.writestr(f"line_{idx:04d}.wav", wav_io.getvalue())
    return Response(content=zip_buffer.getvalue(), media_type="application/zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
