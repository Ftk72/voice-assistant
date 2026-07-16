"""Service TTS Pipecat adapté à voice-forge.

Synthèse exécutée en réel pour la première fois le 2026-07-10 (annonce
d'accueil audible). Sous-classe le `OpenAITTSService` de Pipecat, qui n'est
**pas** un client OpenAI-compat neutre, pour trois raisons vérifiées (cf.
`docs/impasses.md`, entrée 2026-07-09, et le premier run réel) :

1. Il **valide la voix côté client** contre l'énumération OpenAI (`VALID_VOICES`)
   et rejette « VoixDeTest » (et toute voix enrôlée) *avant* tout appel réseau.
   On retire cette validation : voice-forge accepte n'importe quelle voix.
2. Il traite la réponse comme du **PCM brut**, alors que voice-forge renvoie du
   **WAV**. On route donc les octets par `_stream_audio_frames_from_iterator(
   strip_wav_header=True)`, helper Pipecat qui retire l'en-tête, y détecte le
   sample rate (octets 24-28) et rééchantillonne vers `self.sample_rate`.
3. Ce helper suppose un en-tête de **44 octets** et du **PCM 16 bits** — or le
   WAV Chatterbox est en **float32** avec ses données à l'offset 80 (grésillement
   constaté au premier run). Le flux passe donc d'abord par
   `NormaliseurWavPCM16`, qui réécrit en-tête canonique + échantillons int16.

Le reste (POST `/audio/speech`, streaming, métriques) est réutilisé tel quel.

Import différé : ce module n'est chargé que depuis `executer_session`, sous
l'extra `pipecat` ; le reste du composant tourne sans lui.
"""

from collections.abc import AsyncGenerator

from pipecat.frames.frames import ErrorFrame, Frame
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.settings import assert_given
from pipecat.utils.tracing.service_decorators import traced_tts

from app.transport.normaliseur_wav import NormaliseurWavPCM16


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

            normaliseur = NormaliseurWavPCM16()

            async def flux_normalise():
                async for morceau in reponse.iter_bytes(self.chunk_size):
                    normalise = normaliseur.avaler(morceau)
                    if normalise:
                        yield normalise
                reste = normaliseur.clore()
                if reste:
                    yield reste

            async for frame in self._stream_audio_frames_from_iterator(
                flux_normalise(),
                strip_wav_header=True,
                context_id=context_id,
            ):
                yield frame
