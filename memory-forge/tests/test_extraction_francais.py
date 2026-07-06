"""La bascule d'extraction en français remplace le point d'extension documenté de
graphiti-core (`get_extraction_language_instruction`). Subtilité : chaque client fait
`from .client import get_extraction_language_instruction` — le nom est lié à l'import,
il faut donc remplacer le symbole dans chaque module consommateur, pas seulement à la
source. graphiti-core n'étant pas installé en dev (extra), on injecte des faux modules."""

import sys
import types

import pytest


def _instruction_anglaise_par_defaut(group_id=None):
    return "Otherwise, output English."


@pytest.fixture
def faux_modules_graphiti(monkeypatch):
    """Reproduit la topologie graphiti_core.llm_client.{client,openai_base_client,
    openai_generic_client}, chacun portant le symbole importé par nom."""
    paquet_racine = types.ModuleType("graphiti_core")
    paquet_llm = types.ModuleType("graphiti_core.llm_client")
    modules = {}
    for nom in ("client", "openai_base_client", "openai_generic_client"):
        module = types.ModuleType(f"graphiti_core.llm_client.{nom}")
        module.get_extraction_language_instruction = _instruction_anglaise_par_defaut
        setattr(paquet_llm, nom, module)
        monkeypatch.setitem(sys.modules, f"graphiti_core.llm_client.{nom}", module)
        modules[nom] = module
    paquet_racine.llm_client = paquet_llm
    monkeypatch.setitem(sys.modules, "graphiti_core", paquet_racine)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client", paquet_llm)
    return modules


def test_la_bascule_remplace_le_symbole_dans_chaque_module_consommateur(faux_modules_graphiti):
    from app.graph.francais import forcer_extraction_en_francais

    forcer_extraction_en_francais()

    for nom, module in faux_modules_graphiti.items():
        instruction = module.get_extraction_language_instruction("groupe-quelconque")
        assert instruction is not _instruction_anglaise_par_defaut(None), nom
        assert "français" in instruction, f"instruction non française dans {nom}"
        assert "English" not in instruction, f"consigne anglaise résiduelle dans {nom}"


def test_l_instruction_preserve_les_noms_propres():
    from app.graph.francais import INSTRUCTION_EXTRACTION_FR

    assert "noms propres" in INSTRUCTION_EXTRACTION_FR
