# Personas voice-first

Prompts systèmes chargés par le **Dialogue Forge** depuis ce dossier
(`DIALOGUE_FORGE_PERSONAS_DIR`, monté sur `/personas`) : un persona associe un
prompt à une voix par défaut (CONTEXT.md § Persona). Règle commune : les réponses
sont destinées à être **lues à voix haute** par le TTS — jamais de markdown, de
listes, de code ou d'URL.

| Fichier | Persona | Voix (`meta.tts.voice`) |
| --- | --- | --- |
| `assistant.md` | Assistant du quotidien, neutre | `Emma` (exemple) |
| `batman.md` | Batman, laconique et grave | `Batman` |

Le nom de la voix doit correspondre à un dossier `voices/NomVoix/` du Voice Forge.
