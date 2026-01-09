# Arquivo de configuração para pipeline.py
# Preencha/ajuste essas variáveis conforme necessário.

# Caminho para o arquivo de texto de entrada
INPUT_TXT = "/Volumes/PortableSSD/Audiolivos/Um_Grande_Projeto_Nacional_1994/livro.txt"

# Diretório de saída onde serão gravados os capítulos
OUTPUT_DIR = "/Volumes/PortableSSD/Audiolivos/Um_Grande_Projeto_Nacional_1994"

# Chunking / TTS
CHUNK_SIZE = 150
MP3_SPEED = 1.0

# Backend padrão: 'piper' ou 'coqui'
# DEFAULT_BACKEND = "piper"
DEFAULT_BACKEND = "coqui"

# Defaults para CoquiTTS (só usados quando backend == 'coqui')
# Exemplos de modelos CoquiTTS (descomente e use em DEFAULT_MODEL_NAME para testar):
# "tts_models/multilingual/multi-dataset/xtts_v2"  # modelo multilíngue
# "tts_models/pt/cv/vits"  # modelo português (VITS)
# "tts_models/en/ljspeech/tacotron2-DDC"  # modelo inglês Tacotron2
DEFAULT_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
DEFAULT_LANGUAGE = "pt"
DEFAULT_SPEAKER_WAV = "ModelVoices/Yuval_Harari.wav"  # caminho para wav de speaker

# Opcional: adicione outras configurações aqui
