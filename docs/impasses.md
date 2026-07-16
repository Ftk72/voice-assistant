# Registre des impasses

> Savoir négatif tactique, capturé à chaud (skill `/impasses`). Une entrée = trois champs ;
> le champ « Valide tant que » rend la péremption décidable. Une impasse périmée n'est pas
> supprimée : elle est marquée comme telle et redevient une prémisse à re-vérifier (`/premisses`).
> Les contraintes permanentes (sans condition de validité) vont en ADR ou au CLAUDE.md, pas ici.

## ~~2026-07-09 — Pipecat `OpenAITTSService` rejette les voix hors énumération OpenAI~~ — LEVÉE EN CODE le 2026-07-09 (sous-classe `ServiceTTSVoiceForge`)

> Condition de la « valide tant que » atteinte : on n'utilise plus `OpenAITTSService` tel quel. `transport-voix/app/transport/tts_voiceforge.py` (`ServiceTTSVoiceForge`) override `run_tts` — voix passée telle quelle (pas de check `VALID_VOICES`) et réponse routée par le helper Pipecat `_stream_audio_frames_from_iterator(strip_wav_header=True)`, qui retire l'en-tête WAV, **détecte le sample rate dedans** (octets 24-28) et rééchantillonne vers `self.sample_rate`. Prémisse « format voice-forge » tranchée : voice-forge renvoie du **WAV** (`media_type="audio/wav"`), **pas** du PCM comme le supposait `OpenAITTSService` — d'où l'usage du strip WAV plutôt qu'un simple retrait du check. 2 tests factices verts (voix hors énum acceptée + PCM reconstitué à l'identique après strip). **Jamais exécuté bout-en-bout** : reste à confirmer au premier run réel (annonce d'accueil audible via WebRTC). Vigilance jumelle `OpenAISTTService` (whisper.cpp) **tranchée par inspection** : PAS de rigidité type-TTS (aucun rejet client avant réseau ; `verbose_json` gaté derrière `_include_prob_metrics=False`, donc requête `json` simple → `{"text":…}` lu correctement). Un seul défaut latent trouvé et corrigé : le STT était construit **sans langue** → défaut `Language.EN` sur un assistant 100 % français ; câblé sur `Language(s.langue)` (= FR) dans `pipecat.py`.

- **Tenté** : brancher le TTS voice-forge (OpenAI-compat, voix « VoixDeTest ») dans le pipeline Pipecat via `OpenAITTSService(base_url=voice-forge)`.
- **Pourquoi c'est mort** : `OpenAITTSService.run_tts` **valide la voix côté client** contre `VALID_VOICES` (alloy, ash, … verse) et lève un `ErrorFrame` **avant tout appel réseau** (0.000 s) → « VoixDeTest » refusée. Ce n'est donc PAS un client OpenAI-compat neutre. Il POSTe aussi `response_format:"pcm"` et traite la réponse comme du **PCM brut à `self.sample_rate`, mono** — or voice-forge renvoie du **WAV**, donc retirer le seul check `VALID_VOICES` n'aurait pas suffi (en-tête WAV joué comme du bruit, rate faux).
- **Valide tant que** : on utilise `OpenAITTSService` tel quel pour voice-forge. **Tombée** par la sous-classe `ServiceTTSVoiceForge` (cf. note ci-dessus).

## ~~2026-07-08 — WebRTC : la media (RTP) ne traverse pas WSL2 (NAT) ↔ navigateur Windows~~ — RÉSOLUE le 2026-07-09 (co-localisation Windows)

> Condition de la « valide tant que » atteinte : transport (Pipecat) ET client (coquille Tauri/WebView2) exécutés **tous deux en natif Windows** → media WebRTC en **localhost Windows** (`Connection state changed to: connected`, pipeline jusqu'au TTS). Le pont WebView2↔Pipecat (risque n°1, ADR 0012) est **validé**. coturn devient inutile pour ce chemin (laissé dormant). Les forges restent en WSL2/Docker, jointes en HTTP via mirrored.

- **Tenté** : brancher le prototype voix A2 (Pipecat SmallWebRTC servi dans WSL2, port 8700) depuis un navigateur **Windows** via `http://127.0.0.1:8700/prototype` (getUserMedia + WebRTC) ; premier bout-en-bout du pont WebView2↔Pipecat (ADR 0012, risque n°1).
- **Pourquoi c'est mort** : deux topologies testées, deux pannes distinctes (le client navigateur tourne côté **Windows**, Pipecat dans **WSL2**) :
  - **Mode NAT** (défaut, `eth0` en 172.22.x) : signaling `/offer` OK (forwarding localhost **TCP**), ICE atteint `connected`/`completed`, **mais la media UDP (RTP) ne traverse pas le NAT** → `read_audio_frame: No audio frame received` + TTS de sortie inaudible. Le `connected` est **trompeur** (checks STUN passent, pas le flux media).
  - **Mode `mirrored`** (`.wslconfig` `networkingMode=mirrored`, `eth1` en 10.178.x partagé) : **régression** — l'ICE ne connecte **plus du tout**, `Timeout establishing the connection to the remote peer. Closing.` après ~60 s. Désobfuscation mDNS du navigateur (`edge://flags` « Anonymize local IPs… » → Disabled) **testée, sans effet** → mDNS écarté. Suspect restant : **pare-feu Hyper-V** de WSL (actif par défaut en mirrored, bloque l'UDP entrant vers le process WSL).
  - **TURN local (coturn en Docker)** ajouté et **fonctionnel** (les `ALLOCATE` réussissent, auth OK). Mais en réseau **bridge**, coturn attribue ses relais sur l'IP interne du conteneur (`172.19.0.12`) → injoignable des deux pairs, ICE échoue quand même. Passage en `network_mode: host` tenté comme remède (relais = vraies adresses hôte). **Non concluant dans le temps investi** → arbitrage : on arrête de bricoler le réseau.
- **Valide tant que** : le pont WebRTC brut **navigateur-Windows ↔ Pipecat-WSL2** n'est pas validé *bout-en-bout*. Décision (2026-07-08) : la validation media est **différée** jusqu'à ce que client et transport soient **co-localisés** — soit la coquille A3 (dont la topologie de déploiement tranchera), soit un client lancé côté WSL. Le code A2 est, lui, validé (API Pipecat, signaling `/offer`, allocation TURN). coturn reste en place, réutilisable. Ne PAS re-payer les pistes NAT / mirrored+mDNS / mirrored+firewall / coturn-bridge : déjà explorées ici.

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

## 2026-07-16 — Pipecat 1.5 : `vad_analyzer=` dans `TransportParams` est ignoré en silence, le VAD ne tourne jamais

- **Tenté** : pipeline voix réel avec le VAD déclaré à la mode pré-1.5 (`TransportParams(..., vad_analyzer=SileroVADAnalyzer())`) — au run réel, l'accueil TTS sort, le micro arrive bien au transport (aucun « No audio frame received »), mais la parole n'est **jamais** détectée : zéro événement VAD/STT pendant 5 min, puis « Idle timeout detected » et le pipeline s'annule.
- **Pourquoi c'est mort** : en 1.5, `TransportParams` (pydantic, `extra` par défaut = ignoré) **n'a plus de champ `vad_analyzer`** — le kwarg est avalé sans erreur ni warning. Piège aggravant : `SileroVADAnalyzer()` se construit quand même, donc le log affiche « Loading Silero VAD model… / Loaded Silero VAD », ce qui fait croire le VAD actif alors qu'il n'est branché sur rien. En 1.5 le VAD est un **processeur de pipeline explicite** : `VADProcessor(vad_analyzer=…)` (pipecat/processors/audio/vad_processor.py), à insérer entre `transport.input()` et le STT — il émet les `VADUserStarted/StoppedSpeakingFrame` que le STT segmenté (`SegmentedSTTService`, base d'`OpenAISTTService`) attend (stt_service.py:414-418). Fausses pistes écartées en route (payées) : périphérique micro Windows (jauge OK), permission WebView2 (getUserMedia réussi sinon pas de `/offer`), niveau capté (mesuré 0,2-1,0 en devtools), réseau localhost (la boucle de lecture aurait averti toutes les 2 s).
- **Valide tant que** : le pipeline inclut le `VADProcessor` explicite (retirer ce processeur réarme l'impasse) et que Pipecat reste en 1.5.x. Vérif en 10 s au run : dire un mot → le log doit montrer « User started speaking » (log DEBUG du VADProcessor).
