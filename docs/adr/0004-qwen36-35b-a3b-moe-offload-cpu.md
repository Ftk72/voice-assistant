# ADR 0004 — Qwen3.6-35B-A3B (MoE) avec experts déchargés en RAM

Date : 2026-07-02 · Statut : accepté

## Contexte

16 Go de VRAM (RTX 5080) doivent héberger LLM + STT (Voxtral Mini) + TTS (Chatterbox). La gamme Qwen 3.6 : 27B dense (~16,8 Go en Q4_K_M, impossible en cohabitation) et 35B-A3B, MoE à 3B de paramètres actifs. La machine dispose de 64 Go de RAM.

## Décision

**Qwen3.6-35B-A3B en Q4_K_M** via llama.cpp, avec déchargement des experts MoE vers la RAM CPU (`--n-cpu-moe`) : ~6 Go de VRAM, ~30 tok/s attendus — suffisant pour la conversation vocale temps réel.

## Budget VRAM résultant (~16 Go)

| Service | VRAM |
| --- | --- |
| Qwen3.6-35B-A3B Q4 (experts en RAM) | ~6 Go |
| Voxtral Mini GGUF (llama.cpp) | ~3 Go |
| Chatterbox Multilingual | ~3 Go |
| Marge (contexte, pics, desktop) | ~4 Go |

## Alternatives écartées

- **27B dense en Q2/Q3** : dégradation de qualité due à la quantification agressive et budget VRAM insuffisant pour le STT/TTS.
- **Modèle 8-14B tout-VRAM** : latence légèrement meilleure mais nettement moins capable ; le MoE est déjà assez rapide pour le vocal. Peut s'ajouter plus tard comme second modèle dans OpenWebUI.
