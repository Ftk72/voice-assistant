"""Extraction en français — remplace le point d'extension documenté de graphiti-core.

`get_extraction_language_instruction` (graphiti_core.llm_client.client) est ajoutée au
message système de chaque appel d'extraction ; sa docstring invite explicitement à la
remplacer (« Override this function to customize language extraction »). L'instruction
par défaut (« restitue dans la langue d'origine, sinon en anglais ») a échoué en réel
avec Qwen3.6 le 2026-07-06 : entrée française, faits extraits en anglais.

Ce n'est pas un fork : remplacement à l'exécution du point d'extension prévu, dans
notre adaptateur uniquement."""

INSTRUCTION_EXTRACTION_FR = (
    "\n\nToute information extraite (faits, résumés, noms de relations, attributs) doit "
    "être rédigée en français, quelle que soit la langue du texte source. Les noms "
    "propres (personnes, lieux, organisations, titres d'œuvres) restent tels quels."
)


def _instruction_francaise(group_id: str | None = None) -> str:
    """Signature identique à l'originale (group_id ignoré : un seul graphe, une langue)."""
    return INSTRUCTION_EXTRACTION_FR


def forcer_extraction_en_francais() -> None:
    """Remplace le symbole à la source ET dans les modules clients : chacun fait
    `from .client import get_extraction_language_instruction`, donc le nom est lié
    à l'import — patcher la source seule ne changerait rien pour eux."""
    from graphiti_core.llm_client import client, openai_base_client, openai_generic_client

    for module in (client, openai_base_client, openai_generic_client):
        module.get_extraction_language_instruction = _instruction_francaise
