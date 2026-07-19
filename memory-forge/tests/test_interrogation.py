"""Le canal question → requête → réponse sourcée (ticket wayfinder 0028) :
service, route `POST /interroger` et outil MCP `interroger_memoire`, tout en
factice — zéro LLM, zéro Neo4j."""

import pytest

from app.graph.fake import InMemoryGraph
from app.insight.fake import GenerateurInsightFactice
from app.interrogation import interroger
from app.interrogation.executeur import ExecuteurCypherFactice
from app.interrogation.fake import TraducteurQuestionFactice
from app.mcp_server import build_mcp
from app.schemas import EpisodeIn, InterrogationIn, RequeteCypher


@pytest.fixture
async def graph():
    graph = InMemoryGraph()
    # « Judo » capitalisé : le graphe factice ne voit comme entités que les
    # mots capitalisés — il faut que « Judo » soit un vrai nœud pour la vue.
    await graph.add_episode(
        EpisodeIn(
            content="Léa pratique le Judo.", source="conversation", name="appel du 2026-07-01"
        )
    )
    return graph


RESULTATS_JUDO = [{"fait": "Léa pratique le Judo.", "source": "Léa", "cible": "Judo"}]


async def test_une_question_produit_requete_reponse_et_monologue(graph):
    executeur = ExecuteurCypherFactice(resultats=RESULTATS_JUDO)
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), executeur,
        InterrogationIn(question="Que sait-on de Léa ?"),
    )
    # La mention s'est résolue contre le vrai nom du nœud, la requête est partie
    # avec le nom résolu, la réponse s'appuie sur les résultats vérité-terrain.
    assert reponse.monologue.resolues[0].noeud == "Léa"
    assert executeur.requetes[0].parametres["entite"] == "Léa"
    assert reponse.monologue.requete is not None
    assert reponse.monologue.resultats == RESULTATS_JUDO
    assert reponse.reponse and "1" in reponse.reponse


async def test_la_resolution_est_floue(graph):
    executeur = ExecuteurCypherFactice(resultats=RESULTATS_JUDO)
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), executeur,
        InterrogationIn(question="Que sait-on de Lea ?"),
    )
    assert executeur.requetes[0].parametres["entite"] == "Léa"
    assert reponse.monologue.non_resolues == []


async def test_une_entite_inconnue_bloque_la_requete_et_le_dit(graph):
    executeur = ExecuteurCypherFactice()
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), executeur,
        InterrogationIn(question="Que sait-on de Zorglub ?"),
    )
    assert reponse.monologue.non_resolues == ["Zorglub"]
    assert reponse.monologue.requete is None
    assert executeur.requetes == []
    assert "Zorglub" in reponse.reponse


async def test_sans_resultat_la_reponse_le_dit_franchement(graph):
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), ExecuteurCypherFactice(resultats=[]),
        InterrogationIn(question="Que sait-on de Léa ?"),
    )
    assert "rien" in reponse.reponse.lower()


async def test_la_vue_surligne_les_noeuds_cites_dans_les_resultats(graph):
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), ExecuteurCypherFactice(resultats=RESULTATS_JUDO),
        InterrogationIn(question="Que sait-on de Léa ?"),
    )
    assert "Léa" in reponse.vue.surligner
    assert "Judo" in reponse.vue.surligner
    assert reponse.vue.focus == "Léa"


async def test_le_contexte_leger_est_rendu_pour_la_question_suivante(graph):
    reponse = await interroger(
        graph, TraducteurQuestionFactice(), ExecuteurCypherFactice(resultats=RESULTATS_JUDO),
        InterrogationIn(question="Que sait-on de Léa ?"),
    )
    assert reponse.contexte.question_precedente == "Que sait-on de Léa ?"
    assert reponse.contexte.entites == ["Léa"]


async def test_le_rejeu_d_une_requete_ne_touche_pas_le_llm(graph):
    traducteur = TraducteurQuestionFactice()
    executeur = ExecuteurCypherFactice(resultats=RESULTATS_JUDO)
    reponse = await interroger(
        graph, traducteur, executeur,
        InterrogationIn(requete=RequeteCypher(cypher="MATCH (n:Entity) RETURN n.name LIMIT 5")),
    )
    assert traducteur.appels == 0
    assert reponse.reponse is None
    assert reponse.monologue.aiguillage is None
    assert reponse.monologue.resultats == RESULTATS_JUDO


async def test_le_rejeu_reste_soumis_aux_garde_fous(graph):
    from app.interrogation.garde_fous import RequeteInterdite

    with pytest.raises(RequeteInterdite):
        await interroger(
            graph, TraducteurQuestionFactice(), ExecuteurCypherFactice(),
            InterrogationIn(requete=RequeteCypher(cypher="MATCH (n) DELETE n")),
        )


async def test_le_cypher_libre_de_l_aiguillage_recoit_un_limit(graph):
    executeur = ExecuteurCypherFactice()
    await interroger(
        graph,
        TraducteurQuestionFactice(
            cypher_libre="MATCH (n:Entity) RETURN n.name"
        ),
        executeur,
        InterrogationIn(question="Une question hors gabarits ?"),
    )
    assert "LIMIT" in executeur.requetes[0].cypher


# --- Route POST /interroger ---


def test_la_route_interroger_repond(client):
    reponse = client.post("/interroger", json={"question": "Que sait-on de Léa ?"})
    assert reponse.status_code == 200
    corps = reponse.json()
    assert "monologue" in corps and "vue" in corps


def test_la_route_refuse_une_requete_d_ecriture(client):
    reponse = client.post(
        "/interroger", json={"requete": {"cypher": "MATCH (n) DELETE n", "parametres": {}}}
    )
    assert reponse.status_code == 400


def test_la_route_exige_question_ou_requete(client):
    assert client.post("/interroger", json={}).status_code == 422


# --- Outil MCP interroger_memoire ---


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_l_outil_mcp_source_sa_reponse(graph):
    mcp = build_mcp(
        graph, GenerateurInsightFactice(),
        TraducteurQuestionFactice(), ExecuteurCypherFactice(resultats=RESULTATS_JUDO),
    )
    answer = await call_tool(mcp, "interroger_memoire", {"question": "Que sait-on de Léa ?"})
    assert "1 fait" in answer  # sourcing léger : « d'après N fait(s) du graphe »


async def test_l_outil_mcp_dit_franchement_quand_il_ne_trouve_rien(graph):
    mcp = build_mcp(
        graph, GenerateurInsightFactice(),
        TraducteurQuestionFactice(), ExecuteurCypherFactice(resultats=[]),
    )
    answer = await call_tool(mcp, "interroger_memoire", {"question": "Que sait-on de Léa ?"})
    assert "rien" in answer.lower()
