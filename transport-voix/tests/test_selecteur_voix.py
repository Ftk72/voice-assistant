"""Logique pure de choix de la voix TTS au fil du flux Dialogue Forge.

Ces tests tournent **sans l'extra `pipecat`** : `SelecteurVoix` ne dépend
d'aucune brique Pipecat. Ils vérifient la décision « quand faut-il changer la
voix du TTS ? » — c.-à-d. quand le transport doit émettre un
`TTSUpdateSettingsFrame` vers le service TTS (ADR 0012 décision 5).
"""

from app.transport.selecteur_voix import SelecteurVoix


def test_deux_tours_portant_deux_voix_le_tts_recoit_chacune():
    """Deux tours consécutifs, chacun avec sa propre voix : le sélecteur signale
    un changement pour chaque voix (donc le TTS reçoit successivement les deux).
    Une voix répétée au sein d'un tour ne redéclenche pas de changement."""
    selecteur = SelecteurVoix("VoixDefaut")

    # Tour 1 — deux phrases voix « Alice » : un seul changement à signaler.
    assert selecteur.changement("Alice") == "Alice"
    assert selecteur.changement("Alice") is None

    # Tour 2 — deux phrases voix « Bob » : un seul changement, la nouvelle voix.
    assert selecteur.changement("Bob") == "Bob"
    assert selecteur.changement("Bob") is None


def test_phrase_sans_voix_conserve_la_voix_par_defaut():
    """Une phrase sans voix (champ vide ou absent) ne change rien : la voix par
    défaut du pipeline reste en place — aucun `TTSUpdateSettingsFrame` émis."""
    selecteur = SelecteurVoix("VoixDefaut")

    assert selecteur.changement("") is None
    assert selecteur.changement(None) is None
    # Puis une vraie voix : le défaut n'ayant jamais bougé, « Alice » est bien
    # perçue comme un changement.
    assert selecteur.changement("Alice") == "Alice"


def test_premier_tour_a_la_voix_par_defaut_ne_declenche_rien():
    """Si le flux porte déjà la voix par défaut, inutile de la ré-appliquer :
    le TTS a été monté sur cette voix (s.tts_voix_defaut)."""
    selecteur = SelecteurVoix("VoixDefaut")

    assert selecteur.changement("VoixDefaut") is None


def test_retour_a_la_voix_par_defaut_est_un_changement():
    """Revenir à la voix par défaut après en avoir changé est bien un
    changement à signaler (le TTS était sur une autre voix)."""
    selecteur = SelecteurVoix("VoixDefaut")

    assert selecteur.changement("Alice") == "Alice"
    assert selecteur.changement("VoixDefaut") == "VoixDefaut"
