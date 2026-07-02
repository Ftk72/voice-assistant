# Personas voice-first

Prompts systèmes à coller dans **Workspace → Models → + → System Prompt** (voir `docs/OPENWEBUI.md`). Règle commune : les réponses sont destinées à être **lues à voix haute** par le TTS — jamais de markdown, de listes, de code ou d'URL.

| Fichier | Persona | Voix (`meta.tts.voice`) |
| --- | --- | --- |
| `assistant.md` | Assistant du quotidien, neutre | `Emma` (exemple) |
| `batman.md` | Batman, laconique et grave | `Batman` |

Le nom de la voix doit correspondre à un dossier `voices/NomVoix/` du Voice Forge.
