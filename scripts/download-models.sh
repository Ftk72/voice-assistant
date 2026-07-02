#!/usr/bin/env bash
# Télécharge les trois modèles (~26 Go au total) — à lancer un jour de bonne connexion.
# Utilise le CLI Hugging Face via uvx (aucune installation permanente).
#
# ⚠️ Les noms de dépôts/fichiers sont à vérifier au moment du téléchargement
#    (quantifications GGUF publiées par la communauté, noms susceptibles de changer).
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p models/llm models/stt models/hf-cache

hf() { uvx --from 'huggingface_hub[cli]' hf "$@"; }

echo "=== 1/3 LLM : Qwen3.6-35B-A3B Q4_K_M (~20 Go) ==="
# Dépôt à vérifier : chercher « Qwen3.6-35B-A3B GGUF » sur huggingface.co
hf download unsloth/Qwen3.6-35B-A3B-GGUF \
  "Qwen3.6-35B-A3B-Q4_K_M.gguf" \
  --local-dir models/llm
mv -f models/llm/Qwen3.6-35B-A3B-Q4_K_M.gguf models/llm/qwen3.6-35b-a3b-q4_k_m.gguf

echo "=== 2/3 STT : Voxtral Mini GGUF + mmproj (~3 Go) ==="
# Dépôt à vérifier : ggml-org publie les GGUF officiels de Voxtral
hf download ggml-org/Voxtral-Mini-3B-2507-GGUF \
  "Voxtral-Mini-3B-2507-Q4_K_M.gguf" "mmproj-Voxtral-Mini-3B-2507-Q8_0.gguf" \
  --local-dir models/stt
mv -f models/stt/Voxtral-Mini-3B-2507-Q4_K_M.gguf models/stt/voxtral-mini-q4_k_m.gguf
mv -f models/stt/mmproj-Voxtral-Mini-3B-2507-Q8_0.gguf models/stt/voxtral-mini-mmproj.gguf

echo "=== 3/3 TTS : poids Chatterbox Multilingual (~3 Go, cache HF) ==="
HF_HOME="$PWD/models/hf-cache" hf download ResembleAI/chatterbox

echo "=== 4/4 Embeddings : bge-m3 GGUF (~600 Mo, mémoire phase 2) ==="
mkdir -p models/embedder
# Dépôt à vérifier : GGUF communautaires de bge-m3
hf download gpustack/bge-m3-GGUF "bge-m3-Q8_0.gguf" --local-dir models/embedder
mv -f models/embedder/bge-m3-Q8_0.gguf models/embedder/bge-m3-q8_0.gguf

echo "Terminé. Lancer ensuite : docker compose up -d --build"
