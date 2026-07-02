# ADR 0001 — llama.cpp (et non vLLM) pour servir le LLM et Voxtral Mini

Date : 2026-07-02 · Statut : accepté

## Contexte

La spec initiale prévoyait vLLM pour servir Voxtral. La contrainte matérielle est une RTX 5080 (16 Go VRAM) devant héberger simultanément : un LLM (Qwen 3.6 quantifié), le STT (Voxtral Mini) et un moteur TTS avec clonage de voix. vLLM pré-alloue la quasi-totalité de la VRAM disponible (`gpu_memory_utilization`), ce qui rend la cohabitation de trois modèles fragile et rigide.

## Décision

Servir le LLM (Qwen 3.6 quantifié GGUF) **et** Voxtral Mini (GGUF) via **llama.cpp** (`llama-server`), chacun dans son conteneur, exposant l'API compatible OpenAI (`/v1/chat/completions`, `/v1/audio/transcriptions`) qu'OpenWebUI consomme nativement.

## Conséquences

- Allocation VRAM précise et prévisible par modèle (quantification + `n_gpu_layers`).
- Aucun composant custom pour le STT : OpenWebUI (moteur STT « openai ») pointe directement sur le conteneur llama.cpp de Voxtral.
- On renonce au batching haute-performance de vLLM — sans objet pour un usage mono-utilisateur.
- Réversible en échangeant un conteneur dans docker-compose si vLLM redevient pertinent (multi-utilisateurs).

## Alternatives écartées

- **vLLM** : pré-allocation VRAM incompatible avec la cohabitation de 3 modèles sur 16 Go.
- **faster-whisper large-v3-turbo** (natif OpenWebUI, ~1,5 Go) : écarté au profit de Voxtral Mini, choix assumé de l'utilisateur pour la compréhension audio native ; reste le plan B documenté si la VRAM devient trop juste.
