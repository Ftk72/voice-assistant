from app.audio.base import AudioPlayer


class FakePlayer(AudioPlayer):
    """Lecteur factice : ne joue rien, garde les wav reçus — tests et dev sans enceintes."""

    def __init__(self) -> None:
        self.played: list[bytes] = []

    def play_wav(self, data: bytes) -> None:
        self.played.append(data)
