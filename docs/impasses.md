# Registre des impasses

> Savoir négatif tactique, capturé à chaud (skill `/impasses`). Une entrée = trois champs ;
> le champ « Valide tant que » rend la péremption décidable. Une impasse périmée n'est pas
> supprimée : elle est marquée comme telle et redevient une prémisse à re-vérifier (`/premisses`).
> Les contraintes permanentes (sans condition de validité) vont en ADR ou au CLAUDE.md, pas ici.

## ~~2026-07-02 — `hf download unsloth/Qwen3.6-35B-A3B-GGUF` échoue (*File not found in repository*)~~ — PÉRIMÉE le 2026-07-05

> Condition de péremption atteinte : fichiers re-listés via l'API HF le 2026-07-05.
> Verdict : seul le fichier unsloth avait changé (`Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`,
> infixe « UD ») ; les noms Voxtral (ggml-org) et bge-m3 (gpustack) étaient corrects.
> Le script `scripts/download-models.sh` est corrigé et saute désormais les fichiers présents.

- **Tenté** : télécharger `Qwen3.6-35B-A3B-Q4_K_M.gguf` depuis le dépôt unsloth via `scripts/download-models.sh`
- **Pourquoi c'est mort** : le nom de fichier a changé dans le dépôt HF ; les noms codés en dur dans le script ne correspondent plus (les 4 dépôts sont suspects, pas seulement unsloth)
- **Valide tant que** : les fichiers réels de chaque dépôt n'ont pas été re-listés (`hf download <repo> --include "*.gguf" --dry-run` ou API HF, quelques Ko)

## 2026-07-06 — borner `requires-python` ne déloge PAS numba 0.53.1 d'un lock existant

- **Tenté** : corriger l'échec de build `voice-forge` (`uv sync --extra chatterbox` → `llvmlite 0.36.0` refuse Python ≥ 3.10) en bornant `requires-python = ">=3.12,<3.13"` dans le pyproject, puis `uv lock`
- **Pourquoi c'est mort** : `uv lock` **préfère la version déjà verrouillée** tant qu'elle satisfait les contraintes, et le plafond `python < 3.10` de numba 0.53.1 est **dynamique dans son `setup.py`** — donc invisible au résolveur (il n'apparaît qu'à la compilation, d'où l'échec au build et non à la résolution). Un lock *frais* (sans incumbent) prend bien numba 0.66.0, mais un re-lock sur un lock existant garde 0.53.1. Le bornage seul ne suffit jamais pour un paquet sdist-only à métadonnée dynamique
- **Valide tant que** : `voice-forge/pyproject.toml` garde `[tool.uv] constraint-dependencies = ["numba>=0.60", "llvmlite>=0.43"]` (la borne explicite qui exclut l'incumbent et force les roues cp312). Retirer cette contrainte réarme l'impasse

## 2026-07-06 — servir Qwen3.6 sans désactiver le raisonnement rend `content` vide

- **Tenté** : smoke-test LLM (`scripts/smoke-llm.sh`) avec la config compose d'origine (`--jinja` seul) : complétion à `max_tokens=64` et extraction JSON à `max_tokens=1024`
- **Pourquoi c'est mort** : Qwen3.6 émet un `reasoning_content` avant la réponse ; le budget de tokens part intégralement dans le raisonnement (`finish_reason: length`), `content` reste vide et le JSON n'est jamais produit ; même quand ça aboutit, la latence (~15 s) explose le critère produit ≤ 2 s. Avec le raisonnement coupé (`chat_template_kwargs.enable_thinking=false`, testé) : réponse simple 0,7 s, extraction JSON valide 8,3 s
- **Valide tant que** : le service `llm` du compose garde `--reasoning off` (retirer ce flag réarme l'impasse) et que le modèle reste un Qwen3.6 à template « thinking »

## 2026-07-06 — démarrer OpenWebUI sans config RAG déclenche ~1 Go de téléchargements HuggingFace

- **Tenté** : premier `docker compose up` avec le service openwebui sans variables `RAG_*` ni `OFFLINE_MODE`
- **Pourquoi c'est mort** : OpenWebUI télécharge ses modèles d'embedding RAG par défaut (`sentence-transformers/all-MiniLM-L6-v2` puis `TaylorAI/bge-micro-v2`, tous formats : onnx, openvino…) — 1 067 Mo constatés dans le volume, en violation du principe souverain/connexion lente, alors que l'embedder bge-m3 local existe pour ça
- **Valide tant que** : le service openwebui du compose garde `RAG_EMBEDDING_ENGINE=openai` (pointé sur `http://embedder:8080/v1`) et `OFFLINE_MODE=true` (qui force `HF_HUB_OFFLINE=1`)

## 2026-07-06 — connexion MCP OpenWebUI muette : trois pièges de formulaire empilés, tous silencieux

- **Tenté** : brancher les outils `recall`/`forget` du Memory Forge dans OpenWebUI v0.10.2 (Admin Settings → Tools, type MCP) — la connexion se créait mais aucun appel n'atteignait jamais le serveur, sans aucune erreur visible
- **Pourquoi c'est mort** : trois réglages du formulaire échouent en silence. (1) **Auth « Bearer » avec clé vide** : OpenWebUI envoie un en-tête `Authorization: Bearer` suivi d'une espace sans valeur (illégal), httpx refuse d'émettre la requête (`LocalProtocolError`), avalée en `log.debug` (« unhandled errors in a TaskGroup ») — visible uniquement avec `GLOBAL_LOG_LEVEL=DEBUG`. (2) Le champ **Function Name Filter** est une liste blanche (`endswith`) : y mettre un libellé descriptif (« memoire ») écarte tous les outils. (3) Les `toolIds` d'un modèle ne sont transmis que par le **frontend** à l'ouverture d'un chat neuf — le backend ne les applique pas de lui-même, et un chat existant ne les récupère pas
- **Valide tant que** : les connexions MCP du panneau admin gardent auth `none` (ou une clé non vide) et un champ de filtre vide ; piège re-vérifiable en 30 s via l'API avec `tool_ids` explicites et les logs du serveur MCP visé

## ~~2026-07-06 — Chatterbox inutilisable sur RTX 5080 : torch 2.6.0/cu124 sans noyaux sm_120~~ — PÉRIMÉE le 2026-07-06

> Condition de péremption atteinte le jour même : `override-dependencies = ["torch>=2.8,<2.9", "torchaudio>=2.8,<2.9"]`
> dans `voice-forge/pyproject.toml` (roues PyPI cu128, noyaux sm_120 inclus). Synthèse validée en réel :
> 41 s au premier appel (chargement du modèle), **1,94 s en régime**, VRAM 14,6/16,3 Go avec le LLM chargé.
> L'API chatterbox n'a pas souffert du saut 2.6 → 2.8.

- **Tenté** : première synthèse TTS réelle (`_RealChatterboxEngine`, voix de test enrôlée, `scripts/smoke-tts.sh`) — le chargement du modèle passait, la synthèse était le vrai test (prémisse différée des handoffs 0007/0008)
- **Pourquoi c'est mort** : `RuntimeError: CUDA error: no kernel image is available for execution on the device` dès le `.to("cuda")` du voice encoder (RNN/cuDNN, `torch._cudnn_rnn_flatten_weight`). torch 2.6.0 (épinglé par `chatterbox-tts`, roues cu124) n'embarque aucun noyau compilé pour Blackwell **sm_120** ; le support arrive avec torch ≥ 2.7 / CUDA 12.8. Ce n'est pas un bug de notre code
- **Valide tant que** : voice-forge reste sur torch 2.6.0/cu124. Pistes pour la lever (à instruire, gros téléchargements → accord utilisateur) : forcer torch ≥ 2.7 cu128 malgré l'épinglage de chatterbox (cf. technique `constraint-dependencies`/`override-dependencies` de l'impasse numba du 2026-07-06 ; risque d'incompatibilité API à tester), ou repli CPU (`device="cpu"`, latence à mesurer), ou attendre un chatterbox-tts compatible

## 2026-07-06 — servir Voxtral (STT) sans `-c` : llama-server alloue le KV au contexte max → VRAM saturée, toute la stack GPU s'effondre

- **Tenté** : mode appel au micro avec le service `stt` du compose d'origine (`-ngl 999` sans `-c` ni `--parallel`) pendant que LLM et Chatterbox étaient chargés
- **Pourquoi c'est mort** : sans `-c`, llama-server dimensionne le cache KV au contexte d'entraînement du modèle (`n_ctx_slot = 92 928` × 4 slots pour Voxtral Mini) ; dès que le mode appel envoie plusieurs transcriptions, la VRAM déborde (15,7/16,3 Go constatés) et le pilote WSL2 bascule en RAM partagée : STT à 0,08 tok/s (transcriptions de 9 à 21 min), LLM à 0,7-1,5 tok/s, TTS à 17-21 s — symptôme vécu « le LLM ne répond pas ». Le GPU affiche alors 100 % d'utilisation à ~69 W (borné mémoire, pas calcul), signature du débordement
- **Valide tant que** : le service `stt` du compose garde `-c 16384 --parallel 2` (retirer ces flags réarme l'impasse) et que les trois modèles GPU (LLM ~6 Go, STT, Chatterbox ~3 Go) cohabitent sur 16 Go. Vérif en 10 s : `docker compose logs stt | grep n_ctx_slot` (attendu : 8192 par slot) et `nvidia-smi` (attendu : ~13 Go utilisés, util ~0 % au repos)

## 2026-07-06 — le GGUF `ggml-org/Voxtral-Mini-3B-2507-GGUF` embarque le chat template de Devstral : le STT « refuse » de transcrire

- **Tenté** : transcription réelle via `/v1/audio/transcriptions` de llama.cpp (builds b9870 puis b9294, GPU puis CPU, wav/mp3, tous prompts) — le modèle répondait toujours en assistant texte (« I'm unable to transcribe audio »), donnant l'illusion d'un pipeline audio cassé
- **Pourquoi c'est mort** : le template jinja embarqué dans le GGUF est celui de **Devstral/OpenHands** (~1100 tokens de système prompt orienté code, visible via `GET /props`) — un artefact de conversion. llama.cpp construit la requête de transcription comme un simple message chat (« Transcribe audio to text », `common_chat_get_asr_prompt`, aucun support du mode `[TRANSCRIBE]` de Mistral) rendu à travers ce template : le modèle, persuadé d'être un assistant de code, « refuse ». L'audio, lui, arrive intact (le modèle identifiait la langue). Fausses pistes coûteuses : régression llama.cpp (b9294 échoue pareil), corruption des fichiers (sha256 identiques à HF), encodeur GPU sm_120 (CPU pareil)
- **Valide tant que** : le service `stt` garde `--chat-template-file /etc/llama/template-transcription.jinja` (template « greffier », audio avant consigne, français) et `--temp 0` ; re-vérifiable en 10 s : `curl -s http://127.0.0.1:8002/props | grep -c Devstral` (attendu : 0). Si le GGUF est retéléchargé un jour, re-vérifier son template embarqué

## 2026-07-06 — coercer Voxtral Mini en transcripteur via template chat llama.cpp : non fiable, il « répond » à la parole

- **Tenté** : après le déblocage du template Devstral (impasse précédente), cadrer le modèle en greffier ASR via `--chat-template-file` (système strict, audio avant consigne, préremplissage « Phrase prononcée : », `--temp 0`) — testé sur corpus de 4 enregistrements micro réels + 1 audio de synthèse
- **Pourquoi c'est mort** : le mode transcription natif de Voxtral (token spécial `[TRANSCRIBE]` de mistral-common) n'est pas implémenté dans llama.cpp (`common_chat_get_asr_prompt` n'a un preset que pour LFM2) ; en mode chat, Voxtral traite la parole entendue comme une instruction qui lui est adressée et y répond ou la paraphrase — parfait sur audio de synthèse limpide, non fiable sur vraie voix au micro (vérité terrain utilisateur : phrases déformées, réponses au lieu de transcriptions)
- **Valide tant que** : llama.cpp n'implémente pas le mode `[TRANSCRIBE]` (suivre les issues #20914/#21852 de ggml-org/llama.cpp) et que le STT reste Voxtral servi par llama.cpp

## 2026-07-07 — `docker build` de whisper.cpp avec `cmake --build -j` sans limite : OOM de la VM WSL, « WSL server » figé, PC à redémarrer

- **Tenté** : compiler l'image sm_120 de whisper.cpp (`stt/Dockerfile`) via `docker compose build`/`up` pendant que la stack tournait — WSL perdait la connexion, `wsl --shutdown` restait bloqué, seul un arrêt complet du PC réarmait (vécu 3 fois, erreurs « WSL server » dans les journaux)
- **Pourquoi c'est mort** : `-j` sans argument lance un nvcc par cœur (16) × ~2 Go chacun, plus la stack résidente, sur une VM WSL de 30 Go sans `.wslconfig` — la VM part en OOM et vmmem se fige (le SIGKILL 137 observé sur des commandes tierces en est la signature). Piège aggravant : `docker compose up -d stt` **reconstruit silencieusement** l'image si elle n'existe pas — chaque « simple démarrage » relançait la compilation tueuse
- **Valide tant que** : `stt/Dockerfile` garde `cmake --build -j 4` (retirer la limite réarme l'impasse) et que la VM WSL reste ~30 Go sans réserve dédiée au build
