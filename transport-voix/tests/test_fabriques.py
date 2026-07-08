from app.config import Settings
from app.dialogue.fake import ClientDialogueFactice
from app.main import create_app
from app.stt.fake import STTFactice
from app.transport.fake import TransportFactice
from app.tts.fake import TTSFactice


def test_par_defaut_lapplication_porte_des_adaptateurs_factices():
    app = create_app(Settings())

    assert isinstance(app.state.stt, STTFactice)
    assert isinstance(app.state.tts, TTSFactice)
    assert isinstance(app.state.dialogue, ClientDialogueFactice)
    assert isinstance(app.state.transport, TransportFactice)
