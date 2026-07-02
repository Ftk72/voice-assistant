# ADR 0002 — Chatterbox Multilingual comme provider TTS par défaut

Date : 2026-07-02 · Statut : accepté

## Contexte

Le Voice Forge expose une couche `BaseTTSProvider` interchangeable. Il faut choisir le moteur implémenté et livré en premier, avec ~3-4 Go de VRAM disponibles après le LLM (Qwen 3.6 quantifié, llama.cpp) et le STT (Voxtral Mini, llama.cpp). Le clonage de voix en français est l'exigence centrale.

## Décision

Implémenter **Chatterbox Multilingual (Resemble AI)** comme premier provider et défaut du système.

## Justification

- Licence **MIT** (seul candidat de tête sans restriction d'usage).
- Clonage zero-shot éprouvé, français supporté, ~2-4 Go VRAM — tient dans le budget.
- 65 % de préférence humaine face à ElevenLabs en test aveugle ; écosystème mûr (wrappers API OpenAI existants).

## Alternatives écartées

- **Voxtral TTS 4B** (Mistral, mars 2026) : qualité française supérieure (68 % vs ElevenLabs) mais licence CC BY-NC, stack officielle vLLM-Omni exigeant ~16 Go seule, tooling jeune. Candidat naturel pour un **second provider** quand les quantifications se stabiliseront.
- **F5-TTS** : poids CC BY-NC, pas de vrai streaming, communauté en déclin relatif.
- **Kokoro-82M** : pas de clonage, français limité — pertinent seulement comme futur provider « vitesse ».
- **XTTS-v2** : licence CPML restrictive, projet Coqui abandonné.
