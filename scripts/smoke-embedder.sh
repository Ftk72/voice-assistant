#!/usr/bin/env bash
# Smoke-test du service embedder (llama.cpp + bge-m3) — à lancer après
# `docker compose up -d embedder`.
#
# 3 étapes : santé → embedding d'une phrase française → cohérence sémantique
# (deux phrases proches doivent être plus similaires que deux phrases éloignées).
set -euo pipefail

EMBEDDER_URL="${EMBEDDER_URL:-http://127.0.0.1:8003}"

echo "=== 1/3 Santé du serveur ($EMBEDDER_URL/health) ==="
curl -sf "$EMBEDDER_URL/health" || { echo "ÉCHEC : le serveur ne répond pas — le service embedder tourne-t-il ? (docker compose up -d embedder)"; exit 1; }
echo " OK"

echo
echo "=== 2/3 Embedding d'une phrase française ==="
REPONSE=$(curl -sf "$EMBEDDER_URL/v1/embeddings" -H "Content-Type: application/json" -d '{
  "input": "Le rendez-vous chez le dentiste est mardi.",
  "model": "bge-m3"
}')
DIMENSION=$(echo "$REPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data'][0]['embedding']))")
echo "Dimension du vecteur : $DIMENSION (attendu : 1024 pour bge-m3)"
[ "$DIMENSION" = "1024" ] || { echo "AVERTISSEMENT : dimension inattendue."; }

echo
echo "=== 3/3 Cohérence sémantique (similarité cosinus) ==="
curl -sf "$EMBEDDER_URL/v1/embeddings" -H "Content-Type: application/json" -d '{
  "input": [
    "Léa va chez le dentiste mardi.",
    "Le rendez-vous dentaire de Léa est prévu mardi.",
    "La recette de la tarte aux pommes demande trois œufs."
  ],
  "model": "bge-m3"
}' | python3 - <<'PY'
import json
import math
import sys

donnees = json.load(sys.stdin)["data"]
vecteurs = [d["embedding"] for d in sorted(donnees, key=lambda d: d["index"])]


def cosinus(a: list[float], b: list[float]) -> float:
    produit = sum(x * y for x, y in zip(a, b))
    return produit / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b)))


proche = cosinus(vecteurs[0], vecteurs[1])    # deux phrases sur le même rendez-vous
eloigne = cosinus(vecteurs[0], vecteurs[2])   # dentiste vs tarte aux pommes
print(f"Similarité phrases proches   : {proche:.3f}")
print(f"Similarité phrases éloignées : {eloigne:.3f}")
if proche <= eloigne:
    print("ÉCHEC : les phrases proches ne sont pas plus similaires que les éloignées.")
    sys.exit(1)
print("OK : l'ordre sémantique est respecté (proche > éloigné).")
PY

echo
echo "Smoke-test embedder terminé."
