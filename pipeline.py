import os
import re
import subprocess
from pathlib import Path
# from TTS.api import TTS
import torch
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================
# CONFIG
# ==========================
INPUT_TXT = "/Volumes/PortableSSD/Audiolivos/Um_Grande_Projeto_Nacional_1994/livro.txt"
# SPEAKER_WAV = "Yuval_Harari.wav"
OUTPUT_DIR = "/Volumes/PortableSSD/Audiolivos/Um_Grande_Projeto_Nacional_1994"
# MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
# MODEL_NAME = "tts_models/pt/cv/vits"
# MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DDC"
# LANGUAGE = "pt"
CHUNK_SIZE = 150
MP3_SPEED = 1.0

os.makedirs(OUTPUT_DIR, exist_ok=True)

# device = "mps" if torch.backends.mps.is_available() else "cpu"
device = "cpu"
print(f"INFO: Usando device: {device}")

# ==========================
# CHAPTER DETECTION (GOLD)
# ==========================
def is_probable_title(line: str) -> float:
    line = line.strip()
    if not line:
        return 0.0

    score = 0.0
    words = line.split()

    if re.match(r"^\d+\.", line):
        score += 0.5

    if ":" in line:
        left, right = line.split(":", 1)
        if 2 <= len(left.split()) <= 6:
            score += 0.3
        if len(right.split()) <= 8:
            score += 0.2

    cap_ratio = sum(1 for w in words if w[:1].isupper()) / max(len(words), 1)
    if cap_ratio >= 0.5:
        score += 0.2

    if 3 <= len(words) <= 14:
        score += 0.2

    if line.endswith((".", ",", ";")):
        score -= 0.2

    return min(max(score, 0.0), 1.0)

# ==========================
# SPLIT CHAPTERS
# ==========================
def split_chapters(text: str):
    chapters = []
    current_title = "Introducao"
    current_lines = []

    for line in text.splitlines():
        score = is_probable_title(line)

        if score >= 0.6:
            if current_lines:
                chapters.append((current_title, "\n".join(current_lines)))
            current_title = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        chapters.append((current_title, "\n".join(current_lines)))

    return chapters

# ==========================
# TEXT CHUNKER
# ==========================
def chunk_text(text, size=150):
    # Limite rígido: nunca retornar chunks maiores que 200 caracteres
    HARD_LIMIT = 200
    max_size = min(size, HARD_LIMIT)

    sentences = re.split(r'(?<=[,.!?])\s+', text)
    chunks = []
    current = ""

    def flush_current():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
            current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        # Se a sentença cabe inteira no chunk atual, tenta anexar
        if current and len(current) + 1 + len(s) <= max_size:
            current += " " + s
            continue

        # Se a sentença inteira cabe sozinha, finaliza o chunk atual e inicia nova
        if len(s) <= max_size:
            if current:
                flush_current()
            current = s
            continue

        # Sentença maior que max_size: dividir por palavras
        words = s.split()
        for w in words:
            if not w:
                continue

            # Se a palavra é maior que o limite, fatiar a palavra
            if len(w) > max_size:
                # primeiro, flush current se existir
                if current:
                    flush_current()
                # fatiar a palavra em pedaços de max_size
                for i in range(0, len(w), max_size):
                    part = w[i:i+max_size]
                    chunks.append(part)
                continue

            # Palavra cabe no chunk atual?
            if current and len(current) + 1 + len(w) <= max_size:
                current += " " + w
            else:
                # flush current e iniciar novo com a palavra
                if current:
                    flush_current()
                current = w

    flush_current()
    return chunks

# ==========================
# AUDIO HELPERS
# ==========================
def concat_wavs(wavs, output):
    list_file = "wav_list.txt"
    with open(list_file, "w") as f:
        for w in wavs:
            f.write(f"file '{os.path.abspath(w)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output
    ], check=True)

    os.remove(list_file)

def wav_to_mp3(input_wav, output_mp3):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_wav,
        "-filter:a", f"atempo={MP3_SPEED}",
        "-ab", "64k",
        output_mp3
    ], check=True)

# ==========================
# MAIN PIPELINE
# ==========================
def main():
    with open(INPUT_TXT, "r", encoding="utf-8") as f:
        text = f.read()

    chapters = split_chapters(text)
    print(f"INFO: {len(chapters)} capítulos detectados")

    # tts = TTS(MODEL_NAME, progress_bar=False).to(device)

    for idx, (title, content) in enumerate(chapters, start=1):
        safe_title = re.sub(r"[^\w]+", "_", title)[:40]
        chapter_dir = Path(OUTPUT_DIR) / f"{idx:02d}_{safe_title}"
        chapter_dir.mkdir(parents=True, exist_ok=True)

        chapter_txt = chapter_dir / "chapter.txt"
        # sempre atualiza o texto do capítulo (útil se o código for reexecutado)
        chapter_txt.write_text(content, encoding="utf-8")

        chapter_mp3 = chapter_dir / "chapter.mp3"
        if chapter_mp3.exists():
            print(f"INFO: Capítulo {idx} já processado (pulei): {title}")
            continue

        chunks = chunk_text(content, CHUNK_SIZE)
        print(f"INFO: Capítulo {idx}: {title} ({len(chunks)} chunks)")

        # gerar chunks, pulando os já existentes
        for i, chunk in enumerate(chunks):
            wav_path = chapter_dir / f"chunk_{i:03d}.wav"

            if wav_path.exists():
                print(f"  - Chunk {i+1} já existe, pulando")
                continue

            if not isinstance(chunk, str):
                print("Chunk inválido (não é string), pulando")
                continue

            chunk = chunk.strip()
            if not chunk:
                print("Chunk vazio, pulando")
                continue

            try:
                print(f"  - Gerando chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                # tts.tts_to_file(
                #     text=chunk.replace(".", ","),
                #     speaker_wav=SPEAKER_WAV,
                #     language=LANGUAGE,
                #     file_path=str(wav_path)
                # )

                subprocess.run(["python", "Piper_Voicer/piper_voicer.py", "--text", str(chunk.replace(".", ",")), "--output", str(wav_path)], check=True)
                print("    ✔ Chunk gerado com sucesso")
            except Exception as e:
                # Em caso de erro ao gerar um chunk, aborta o capítulo mas mantém os arquivos já gerados
                print(f"ERRO: falha ao gerar chunk {i+1} do capítulo {idx}: {e}")
                print("INFO: Interrompendo processamento deste capítulo. Rode novamente para continuar onde parou.")
                break

        # após tentativa de geração, concatena apenas os wavs existentes (em ordem)
        existing_wavs = sorted(chapter_dir.glob("chunk_*.wav"))
        if not existing_wavs:
            print(f"WARN: Nenhum chunk disponível para concatenação no capítulo {idx}, pulando.")
            continue

        chapter_wav = chapter_dir / "chapter.wav"
        try:
            concat_wavs(existing_wavs, chapter_wav)
        except Exception as e:
            print(f"ERRO: falha ao concatenar wavs do capítulo {idx}: {e}")
            print("INFO: Mantendo chunks para retomar depois. Pulando conversão para mp3 deste capítulo.")
            continue

        try:
            wav_to_mp3(chapter_wav, chapter_mp3)
        except Exception as e:
            print(f"ERRO: falha ao converter para mp3 capítulo {idx}: {e}")
            print("INFO: Mantendo wavs e chapter.wav para retomar depois.")
            continue

        # limpeza: remove apenas os chunk wavs e o chapter.wav após sucesso em mp3
        try:
            for w in existing_wavs:
                try:
                    w.unlink()
                except Exception:
                    pass
            chapter_wav.unlink()
        except Exception:
            pass

    print("✅ PIPELINE FINALIZADO")

if __name__ == "__main__":
    main()
