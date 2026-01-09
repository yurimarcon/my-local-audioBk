#!/usr/bin/env python3

import argparse
import sys
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


def main():
    parser = argparse.ArgumentParser(
        description="CLI simples para gerar áudio usando Piper TTS (PT-BR)"
    )

    parser.add_argument(
        "--text",
        type=str,
        help="Texto a ser convertido em áudio"
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Arquivo de texto (.txt) como entrada"
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Arquivo WAV de saída"
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=Path("Piper_Voicer/pt_BR-faber-medium.onnx"),
        help="Caminho para o modelo Piper (.onnx)"
    )

    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="Volume do áudio (1.0 = padrão)"
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.2,
        help="Velocidade da fala (1.0 = padrão, >1 mais rápido)"
    )

    args = parser.parse_args()

    # Validação de entrada
    if not args.text and not args.input:
        parser.error("Use --text ou --input")

    if args.text and args.input:
        parser.error("Use apenas --text OU --input")

    if args.input:
        text = args.input.read_text(encoding="utf-8")
    else:
        text = args.text

    # Carrega voz
    voice = PiperVoice.load(args.model)

    # Configuração de síntese
    syn_config = SynthesisConfig(
        volume=args.volume,
        length_scale=args.speed,
        noise_scale=1.0,
        noise_w_scale=1.0,
        normalize_audio=False,
    )

    # Geração do WAV
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(args.output), "wb") as wav_file:
        voice.synthesize_wav(
            text,
            wav_file,
            syn_config=syn_config
        )

    print(f"Áudio gerado com sucesso: {args.output}")


if __name__ == "__main__":
    main()
