# =========================
# XTTS AUDIOBOOK - GOLD
# =========================

import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"  # 🔥 ESSENCIAL no Mac

import re
import glob
import time
import logging
import subprocess
import numpy as np
import soundfile as sf
import torch
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig

# segurança PyTorch 2.6+
torch.serialization.add_safe_globals([XttsConfig])

# =========================
# CONFIG
# =========================
INPUT_TXT = "Nexus_0.txt"
SPEAKER_WAV = "Yuval_Harari.wav"

OUT_DIR = "result"
CHUNK_PREFIX = f"{OUT_DIR}/chunk"

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
LANGUAGE = "pt"

MAX_CHARS = 800
MIN_CHARS = 50
SLEEP = 0.05

FINAL_WAV = f"{OUT_DIR}/audiobook.wav"
FINAL_MP3 = f"{OUT_DIR}/audiobook_1.25x.mp3"
MP3_SPEED = 1.25
MP3_BITRATE = "96k"

# =========================
# LOG
# =========================
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("XTTS")

# =========================
# UTILS
# =========================
def split_text(text, max_chars, min_chars):
    parts = [p.strip() for p in re.split(r"[.,]", text) if p.strip()]
    chunks, current = [], ""

    for p in parts:
        if not current:
            current = p
            continue

        if len(current) < min_chars or len(p) < min_chars:
            if len(current) + len(p) <= max_chars:
                current += " " + p
            else:
                chunks.append(current)
                current = p
        else:
            chunks.append(current)
            current = p

        if len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars:]

    if current:
        chunks.append(current)

    return chunks


def merge_wavs(pattern, output):
    files = sorted(
        glob.glob(pattern),
        key=lambda x: int(re.search(r"_(\d+)\.wav$", x).group(1))
    )

    if not files:
        raise RuntimeError("Nenhum WAV encontrado para merge.")

    data_all, sr = [], None
    for f in files:
        data, rate = sf.read(f)
        sr = sr or rate
        data_all.append(data)

    combined = np.concatenate(data_all)
    sf.write(output, combined, sr)
    log.info(f"WAV final gerado: {output}")


def wav_to_mp3_speed(wav, mp3, speed, bitrate):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", wav,
        "-filter:a", f"atempo={speed}",
        "-b:a", bitrate,
        mp3
    ], check=True)

    log.info(f"MP3 final ({speed}x) gerado: {mp3}")

# =========================
# MAIN
# =========================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    log.info(f"Device: {device}")

    tts = TTS(MODEL_NAME, progress_bar=False).to(device)

    with open(INPUT_TXT, "r", encoding="utf-8") as f:
        text = f.read().strip()

    chunks = split_text(text, MAX_CHARS, MIN_CHARS)
    log.info(f"Texto dividido em {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        out = f"{CHUNK_PREFIX}_{i}.wav"
        if os.path.exists(out):
            continue

        log.info(f"Gerando chunk {i}/{len(chunks)} ({len(chunk)} chars)")
        tts.tts_to_file(
            text=chunk,
            speaker_wav=SPEAKER_WAV,
            language=LANGUAGE,
            file_path=out
        )
        time.sleep(SLEEP)

    merge_wavs(f"{CHUNK_PREFIX}_*.wav", FINAL_WAV)
    wav_to_mp3_speed(FINAL_WAV, FINAL_MP3, MP3_SPEED, MP3_BITRATE)


if __name__ == "__main__":
    main()
