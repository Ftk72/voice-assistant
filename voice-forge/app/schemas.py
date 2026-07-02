from pydantic import BaseModel


class Voice(BaseModel):
    id: str
    name: str


class VoicesResponse(BaseModel):
    voices: list[Voice]


class SpeechRequest(BaseModel):
    """Payload OpenAI de POST /audio/speech, tel qu'envoyé par OpenWebUI."""

    model: str
    input: str
    voice: str
