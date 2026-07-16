---
label: wayfinder:task
statut: clos
assigne: subagent-opus (délégation du 2026-07-10, session carte)
bloque-par: []
---

# La voix du flux appliquée par tour

## Question

Combler le dernier trou du contrat ADR 0012 (décision 5) côté transport
(AFK, délégable, TDD sur adaptateurs factices) :

- **Constat (audit 2026-07-10)** : le Dialogue Forge annote déjà chaque
  phrase du NDJSON avec la voix courante (`dialogue.py` :
  `{"type": "phrase", …, "voix": persona.voix}`) et `/interrompre` est livré.
  Mais `transport-voix/app/transport/pipecat.py:100` fige la voix du TTS à
  `s.tts_voix_defaut` au montage du pipeline : la voix portée par le flux
  n'est **pas appliquée**, la dérogation de voix (effective au tour suivant,
  ADR 0012) ne peut pas fonctionner.
- **À livrer** : le transport lit la voix de chaque tour du flux `/tours` et
  la passe au TTS de ce tour (`ServiceTTSVoiceForge` — vérifier comment
  changer la voix par tour proprement dans Pipecat sans remonter le pipeline).
- Critère de clôture : test factice « deux tours, deux voix → le TTS reçoit
  chacune » vert ; tests et ruff verts dans transport-voix.

## Résolution (2026-07-10, vérifiée par l'agent principal)

Livré via le mécanisme Pipecat officiel `TTSUpdateSettingsFrame(delta=
TTSSettings(voice=…))` (groundé sur la roue 1.5.0, ControlFrame in-band donc
ordre préservé avant le `TextFrame`). Nouveau `app/transport/selecteur_voix.py`
(logique pure sans Pipecat, testable sans l'extra) ; `dialogue_processor.py`
émet l'update **avant** la phrase seulement quand la voix change ;
`pipecat.py` passe `voix_defaut=s.tts_voix_defaut`. Vérifié : 16 passed,
2 skipped (tests gatés pipecat), ruff propre, diff relu.

Réserve : le test d'intégration Pipecat réel est gaté (`importorskip`) et n'a
jamais tourné — la dérogation de voix en réel se confirmera au run bout-en-bout
(une fois une seconde voix enrôlée, ticket « Enrôlement de la vraie voix »).
