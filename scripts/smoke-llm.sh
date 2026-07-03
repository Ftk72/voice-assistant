#!/usr/bin/env bash
# Smoke-test du service LLM (llama.cpp + Qwen3.6-35B) — à lancer après `docker compose up -d llm`.
#
# Paye la prémisse différée du handoff 0006 : « le 35B Uncensored produit-il du JSON
# structuré exploitable pour l'extraction Graphiti ? » (risque identifié au grilling).
#
# 3 étapes : santé → latence d'une complétion française → extraction JSON contrainte.
set -euo pipefail

LLM_URL="${LLM_URL:-http://127.0.0.1:8001}"

echo "=== 1/3 Santé du serveur ($LLM_URL/health) ==="
curl -sf "$LLM_URL/health" || { echo "ÉCHEC : le serveur ne répond pas — le service llm tourne-t-il ? (docker compose up -d llm ; chargement ~2 min)"; exit 1; }
echo " OK"

echo
echo "=== 2/3 Complétion française + latence (critère produit : réponse vocale ≤ 2 s) ==="
DEBUT=$(date +%s.%N)
REPONSE=$(curl -sf "$LLM_URL/v1/chat/completions" -H "Content-Type: application/json" -d '{
  "messages": [
    {"role": "system", "content": "Tu es un assistant vocal. Réponds en une seule phrase courte, en français."},
    {"role": "user", "content": "Quelle est la capitale de la France ?"}
  ],
  "max_tokens": 64
}')
FIN=$(date +%s.%N)
echo "$REPONSE" | python3 -c "import sys, json; print('Réponse :', json.load(sys.stdin)['choices'][0]['message']['content'].strip())"
LATENCE=$(python3 -c "print(f'{$FIN - $DEBUT:.2f}')")
echo "Latence complétion : ${LATENCE} s (première requête = prompt froid ; relancer pour la latence en régime)"

echo
echo "=== 3/3 Extraction JSON contrainte (type Graphiti : entités + relations) ==="
# Schéma imposé via json_schema : llama.cpp force la sortie à s'y conformer (grammaire).
# Le vrai test est sémantique : les entités/relations extraites sont-elles les bonnes ?
EXTRACTION=$(curl -sf "$LLM_URL/v1/chat/completions" -H "Content-Type: application/json" -d '{
  "messages": [
    {"role": "system", "content": "Tu extrais les entités (personnes, lieux, organisations, objets) et leurs relations depuis un texte de conversation. Réponds uniquement en JSON."},
    {"role": "user", "content": "Léa a un rendez-vous chez le dentiste mardi à Lyon. Son frère Tom lui prête sa voiture."}
  ],
  "max_tokens": 512,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "extraction",
      "schema": {
        "type": "object",
        "properties": {
          "entites": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "nom": {"type": "string"},
                "type": {"type": "string"}
              },
              "required": ["nom", "type"]
            }
          },
          "relations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "source": {"type": "string"},
                "relation": {"type": "string"},
                "cible": {"type": "string"}
              },
              "required": ["source", "relation", "cible"]
            }
          }
        },
        "required": ["entites", "relations"]
      }
    }
  }
}')

echo "$EXTRACTION" | python3 - <<'PY'
import json
import sys

reponse = json.load(sys.stdin)
contenu = reponse["choices"][0]["message"]["content"]

# Le JSON parse-t-il ? (la grammaire de llama.cpp doit le garantir — sinon c'est rouge)
try:
    extraction = json.loads(contenu)
except json.JSONDecodeError as erreur:
    print(f"ÉCHEC : la sortie n'est pas du JSON valide — {erreur}")
    print(f"Sortie brute : {contenu[:500]}")
    sys.exit(1)

print(json.dumps(extraction, ensure_ascii=False, indent=2))

# Contrôles sémantiques minimaux : les entités attendues sont-elles là ?
noms = {entite["nom"].lower() for entite in extraction.get("entites", [])}
attendus = {"léa", "tom"}
manquants = {nom for nom in attendus if not any(nom in trouve for trouve in noms)}
if manquants:
    print(f"\nAVERTISSEMENT : entités attendues absentes : {manquants} — juger la qualité à l'œil.")
    sys.exit(2)
if not extraction.get("relations"):
    print("\nAVERTISSEMENT : aucune relation extraite — juger la qualité à l'œil.")
    sys.exit(2)
print("\nOK : JSON valide, entités clés présentes, relations non vides.")
print("Verdict final à l'œil : les relations ont-elles du sens ? (prêt de voiture, rendez-vous à Lyon…)")
PY

echo
echo "Smoke-test terminé. Si l'étape 3 déçoit : re-grillinger le choix du moteur (handoff 0006, prémisses différées)."
