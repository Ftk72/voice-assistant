#!/usr/bin/env bash
# Télécharge les modèles manquants — chaque section saute si le fichier est déjà là.
# À lancer un jour de bonne connexion. CLI Hugging Face via uvx (aucune installation).
#
# Noms de dépôts/fichiers re-listés via l'API HF le 2026-07-05 (voir docs/impasses.md).
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p models/llm models/stt models/chatterbox models/embedder

hf() { uvx --from 'huggingface_hub[cli]' hf "$@"; }

echo "=== 1/4 LLM : Qwen3.6-35B-A3B Q4_K_M (~20 Go) ==="
# NB : le fichier en place est la variante Uncensored-HauhauCS-Aggressive choisie
# par l'utilisateur (handoff 0006), pas le Qwen officiel unsloth ci-dessous.
if [ -f models/llm/qwen3.6-35b-a3b-q4_k_m.gguf ]; then
  echo "déjà présent — sauté"
else
  # Nom vérifié le 2026-07-05 : infixe « UD » ajouté par unsloth
  hf download unsloth/Qwen3.6-35B-A3B-GGUF \
    "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf" \
    --local-dir models/llm
  mv -f models/llm/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf models/llm/qwen3.6-35b-a3b-q4_k_m.gguf
fi

echo "=== 2/4 STT : Whisper large-v3-turbo Q5_0 (~570 Mo) ==="
# Remplace Voxtral (2026-07-07, écart à l'ADR 0001 — voir docs/impasses.md :
# le mode [TRANSCRIBE] n'existe pas dans llama.cpp, le modèle « répondait »
# à la parole). Servi par whisper.cpp compilé sm_120 (stt/Dockerfile).
if [ -f models/stt/ggml-large-v3-turbo-q5_0.bin ]; then
  echo "déjà présent — sauté"
else
  # Dépôt vérifié le 2026-07-07 : ggerganov/whisper.cpp (pas ggml-org)
  hf download ggerganov/whisper.cpp "ggml-large-v3-turbo-q5_0.bin" --local-dir models/stt
fi

echo "=== 3/4 TTS : poids Chatterbox pour le pipeline anglais (~1,1 Go) ==="
# ⚠️ t3_cfg.safetensors est le fine-tune FRANÇAIS Thomcles/Chatterbox-TTS-French
#    (même nom de fichier que l'anglais) : ne jamais l'écraser depuis ResembleAI.
if [ ! -f models/chatterbox/t3_cfg.safetensors ]; then
  hf download Thomcles/Chatterbox-TTS-French "t3_cfg.safetensors" --local-dir models/chatterbox
fi
for fichier in ve.safetensors s3gen.safetensors tokenizer.json conds.pt; do
  if [ -f "models/chatterbox/$fichier" ]; then
    echo "$fichier déjà présent — sauté"
  else
    hf download ResembleAI/chatterbox "$fichier" --local-dir models/chatterbox
  fi
done

echo "=== 4/4 Embeddings : bge-m3 GGUF (~600 Mo, mémoire phase 2) ==="
if [ -f models/embedder/bge-m3-q8_0.gguf ]; then
  echo "déjà présent — sauté"
else
  hf download gpustack/bge-m3-GGUF "bge-m3-Q8_0.gguf" --local-dir models/embedder
  mv -f models/embedder/bge-m3-Q8_0.gguf models/embedder/bge-m3-q8_0.gguf
fi

echo "Terminé. Lancer ensuite : docker compose up -d --build"
