"""Service TTS Pipecat adapté à voice-forge.

⚠️ Jamais exécuté bout-en-bout à ce jour — cf. CLAUDE.md. Ne pas présenter
comme fonctionnel tant qu'il n'a pas synthétisé dans un vrai run.

Sous-classe le `OpenAITTSService` de Pipecat, qui n'est **pas** un client
OpenAI-compat neutre, pour deux raisons vérifiées (cf. `docs/impasses.md`,
entrée 2026-07-09) :

1. Il **valide la voix côté client** contre l'énumération OpenAI (`VALID_VOICES`)
   et rejette « VoixDeTest » (et toute voix enrôlée) *avant* tout appel réseau.
   On retire cette validation : voice-forge accepte n'importe quelle voix.
2. Il traite la réponse comme du **PCM brut**, alors que voice-forge renvoie du
   **WAV** (en-tête 44 o + débit propre au modèle : `chatterbox.sr`, Qwen3…).
   On route donc les octets par `_stream_audio_frames_from_iterator(
   strip_wav_header=True)`, helper Pipecat qui retire l'en-tête, détecte le
   sample rate dedans (octets 24-28) et rééchantillonne vers `self.sample_rate`.

Le reste (POST `/audio/speech`, streaming, métriques) est réutilisé tel quel.

Import différé : ce module n'est chargé que depuis `executer_session`, sous
l'extra `pipecat` ; le reste du composant tourne sans lui.
"""

from collections.abc import AsyncGenerator

from pipecat.frames.frames import ErrorFrame, Frame
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.settings import assert_given
from pipecat.utils.tracing.service_decorators import traced_tts


class ServiceTTSVoiceForge(OpenAITTSService):
    """`OpenAITTSService` sans la validation de voix OpenAI et gérant le WAV."""

    @traced_tts
    async def run_tts(self, text: str, context_id: str) -> AsyncGenerator[Frame, None]:
        """Synthétise `text` via voice-forge. Voix passée telle quelle ; réponse
        WAV décodée par le helper Pipecat (strip en-tête + resample)."""
        voix = assert_given(self._settings.voice)
        if voix is None:
            yield ErrorFrame(error="Aucune voix TTS spécifiée")
            return

        # Pas de `response_format:"pcm"` : voice-forge ignore ce champ et renvoie
        # du WAV quoi qu'il arrive. La voix n'est PAS filtrée contre VALID_VOICES.
        create_params = {
            "input": text,
            "model": self._settings.model,
            "voice": voix,
        }
        if self._settings.speed:
            create_params["speed"] = self._settings.speed

        async with self._client.audio.speech.with_streaming_response.create(
            **create_params
        ) as reponse:
            if reponse.status_code != 200:
                erreur = await reponse.text()
                yield ErrorFrame(
                    error=f"Erreur TTS voice-forge (statut {reponse.status_code}) : {erreur}"
                )
                return

            await self.start_tts_usage_metrics(text)
            await self.stop_ttfb_metrics()

            async for frame in self._stream_audio_frames_from_iterator(
                reponse.iter_bytes(self.chunk_size),
                strip_wav_header=True,
                context_id=context_id,
            ):
                yield frame
