import os
import re
from pathlib import Path
from typing import List, Dict

# =========================
# CONFIGURAÇÕES
# =========================

INPUT_TXT = "Nexus.txt"
OUTPUT_DIR = "output"
CHAPTER_DIR = os.path.join(OUTPUT_DIR, "chapters")

MIN_CHAPTER_CHARS = 2000
MAX_TITLE_WORDS = 8

# =========================
# UTILIDADES
# =========================

def normalize_text(text: str) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.split("\n")


def is_probable_title(line: str) -> float:
    line = line.strip()

    if not line:
        return 0.0

    score = 0.0
    words = line.split()

    # -------------------------
    # Numeração explícita
    # -------------------------
    if re.match(r"^\d+\.", line):
        score += 0.5

    if re.match(r"^(?:\d+|[IVXLCDM]+)[\.\s]+", line):
        score += 0.4

    # -------------------------
    # Dois-pontos ou subtítulo
    # -------------------------
    if ":" in line:
        left, right = line.split(":", 1)

        if 2 <= len(left.split()) <= 6:
            score += 0.3

        if len(right.split()) <= 8:
            score += 0.2

    # -------------------------
    # Capitalização
    # -------------------------
    cap_ratio = sum(1 for w in words if w[:1].isupper()) / max(len(words), 1)
    if cap_ratio >= 0.5:
        score += 0.2

    # -------------------------
    # Comprimento tolerante
    # -------------------------
    if 3 <= len(words) <= 14:
        score += 0.2

    # Penalidades leves
    if line.endswith((".", ",", ";")):
        score -= 0.2

    return min(max(score, 0.0), 1.0)



def safe_filename(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text.strip("_")[:60]


# =========================
# SPLIT POR CAPÍTULOS
# =========================

def split_chapters(lines: List[str]) -> List[Dict]:
    candidates = []

    for i, line in enumerate(lines):
        confidence = is_probable_title(line)
        if confidence >= 0.6:
            candidates.append((i, line.strip(), confidence))

    if not candidates:
        return [{
            "index": 1,
            "title": "Introdução",
            "confidence": 0.3,
            "text": "\n".join(lines)
        }]

    chapters = []
    for idx, (line_idx, title, conf) in enumerate(candidates):
        start = line_idx + 1
        end = candidates[idx + 1][0] if idx + 1 < len(candidates) else len(lines)
        text = "\n".join(lines[start:end]).strip()

        chapters.append({
            "index": idx + 1,
            "title": title,
            "confidence": conf,
            "text": text
        })

    # Ajuste de introdução
    if candidates[0][0] > 10:
        intro_text = "\n".join(lines[:candidates[0][0]])
        chapters.insert(0, {
            "index": 0,
            "title": "Introdução",
            "confidence": 0.4,
            "text": intro_text
        })

    # Validação de tamanho mínimo
    validated = []
    for ch in chapters:
        if len(ch["text"]) < MIN_CHAPTER_CHARS and validated:
            validated[-1]["text"] += "\n\n" + ch["text"]
        else:
            validated.append(ch)

    # Reindexa
    for i, ch in enumerate(validated, 1):
        ch["index"] = i

    return validated


# =========================
# SALVAMENTO
# =========================

def save_output(chapters: List[Dict]):
    os.makedirs(CHAPTER_DIR, exist_ok=True)

    preview_lines = []

    for ch in chapters:
        fname = f"{ch['index']:02d}_{safe_filename(ch['title'])}.txt"
        path = os.path.join(CHAPTER_DIR, fname)

        with open(path, "w", encoding="utf-8") as f:
            f.write(ch["text"].strip())

        preview_lines.append(
            f"[{ch['index']:02d}] "
            f"Confiança: {ch['confidence']:.2f} | "
            f"Tamanho: {len(ch['text'])} chars | "
            f"Título: {ch['title']}"
        )

    preview_path = os.path.join(OUTPUT_DIR, "chapters_preview.txt")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write("\n".join(preview_lines))


# =========================
# MAIN
# =========================

def main():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    with open(INPUT_TXT, "r", encoding="utf-8") as f:
        lines = normalize_text(f.read())

    chapters = split_chapters(lines)
    save_output(chapters)

    print(f"✔ {len(chapters)} capítulos gerados")
    print(f"📄 Preview: {OUTPUT_DIR}/chapters_preview.txt")
    print(f"📂 Capítulos: {CHAPTER_DIR}/")


if __name__ == "__main__":
    main()