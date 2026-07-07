from app.segmentation import SegmenteurPhrases


def _segmenter(texte: str) -> list[str]:
    segmenteur = SegmenteurPhrases()
    phrases = segmenteur.absorber(texte)
    phrases += segmenteur.terminer()
    return phrases


def test_decoupe_sur_les_terminateurs():
    assert _segmenter("Bonjour toi. Comment ça va ? Ça roule ! Fin.") == [
        "Bonjour toi.",
        "Comment ça va ?",
        "Ça roule !",
        "Fin.",
    ]


def test_les_points_de_suspension_ne_coupent_pas_les_nombres():
    # « 2,88 » : la virgule n'est jamais une fin de phrase.
    phrases = _segmenter("La latence voix à voix est de 2,88 s en moyenne.")
    assert phrases == ["La latence voix à voix est de 2,88 s en moyenne."]
    assert "2,88" in phrases[0]


def test_le_point_decimal_entre_chiffres_ne_coupe_pas():
    phrases = _segmenter("Pi vaut 3.14. Voilà.")
    assert phrases == ["Pi vaut 3.14.", "Voilà."]


def test_diffusion_incrementale_au_fil_des_fragments():
    segmenteur = SegmenteurPhrases()
    # La première phrase sort dès que sa fin (suivie d'une espace) est absorbée.
    assert segmenteur.absorber("Salut. ") == ["Salut."]
    assert segmenteur.absorber("Encore") == []
    assert segmenteur.terminer() == ["Encore"]
