# my-local-audioBk

Projeto para converter um texto (livro) em audiolivro, dividindo em capítulos e gerando áudio por chunk.

Funcionalidades principais:
- Detecta títulos prováveis e separa o texto em capítulos.
- Fatia o texto em chunks para TTS com limite configurável.
- Suporta dois backends de TTS: Piper (rápido, local, performático) e CoquiTTS (possui modelos de alta qualidade e clonagem de voz).
- Concatena os WAVs por capítulo e converte para MP3.

Estrutura do repositório:
- pipeline.py — pipeline principal (chama o backend selecionado)
- config.py — arquivo de configuração com variáveis ajustáveis
- Piper_Voicer/ — script e modelos do Piper
- ModelVoices/ — exemplo de arquivos de voz para clonagem (Coqui)
- split_chapters.py — (utilitário auxiliar)

Requisitos
- Python 3.8+
- ffmpeg instalado e disponível no PATH
- Dependências em `requirements.txt` (rodar `pip install -r requirements.txt`)

Instalação
1. Crie/ative um virtualenv (recomendado):
   python -m venv .venv && source .venv/bin/activate
2. Instale dependências:
   pip install -r requirements.txt

Como rodar
- Usando o backend padrão (configurável em `config.py`):
  python pipeline.py

- Forçar uso do Piper (mais rápido / performático):
  python pipeline.py --backend piper

- Usar CoquiTTS (melhor qualidade, clonagem de voz):
  python pipeline.py --backend coqui --model-name tts_models/pt/cv/vits --language pt --speaker-wav ModelVoices/Yuval_Harari.wav

Piper vs CoquiTTS — Qual escolher?
- Piper (performático):
  - Roda muito rápido em CPU e tem baixa latência.
  - Ideal para gerar audiolivros grandes localmente sem GPU.
  - Uso: `--backend piper` (o script `Piper_Voicer/piper_voicer.py` é chamado por chunk).

- CoquiTTS (qualidade / clonagem de voz):
  - Oferece modelos de alta qualidade e suporte a clonagem de voz via `speaker_wav`.
  - Requer mais recursos: inicialização e inferência são mais lentas, consumo de memória maior.
  - Se puder, use GPU (device apropriado) para acelerar.
  - Uso: `--backend coqui` e passe `--speaker-wav` se quiser clonar uma voz.

Dicas para performance
- Se estiver usando CoquiTTS sem GPU, considere dividir o trabalho em múltiplas máquinas/processos ou usar batch menor.
- Para Piper, mantenha o script `Piper_Voicer/piper_voicer.py` otimizado e evite re-inicializações desnecessárias.
- Use `--backend piper` para produção quando priorizar velocidade; use `--backend coqui` apenas quando desejar qualidade e clonagem.

Configurações
- Ajuste `config.py` para apontar `INPUT_TXT`, `OUTPUT_DIR` e parâmetros de chunk (`CHUNK_SIZE`, `MP3_SPEED`).
- Exemplos de modelos Coqui estão comentados em `config.py`.

Licença
- Verifique licenças dos modelos e ferramentas utilizadas antes de distribuição.

Contribuições
- Pull requests são bem-vindos.
