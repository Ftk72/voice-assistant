#!/usr/bin/env bash
# Smoke-test du Voice Forge (Chatterbox français, pipeline anglais + T3 Thomcles) —
# à lancer après `docker compose up -d --build voice-forge`.
#
# Prérequis : une voix enrôlée (clonage zero-shot : il faut un wav de référence).
# S'il n'y en a aucune, le script l'explique et sort — enrôler via
# http://127.0.0.1:8100/admin (nom + échantillon wav de quelques secondes).
#
# 3 étapes : santé → voix disponibles → synthèse d'une phrase française en wav.
set -euo pipefail

VOICE_FORGE_URL="${VOICE_FORGE_URL:-http://127.0.0.1:8100}"
SORTIE="${SORTIE:-/tmp/smoke-tts.wav}"

echo "=== 1/3 Santé du serveur ($VOICE_FORGE_URL/health) ==="
curl -sf "$VOICE_FORGE_URL/health" || { echo "ÉCHEC : le serveur ne répond pas — le service voice-forge tourne-t-il ? (docker compose up -d --build voice-forge)"; exit 1; }
echo " OK"

echo
echo "=== 2/3 Voix disponibles ==="
VOIX=$(curl -sf "$VOICE_FORGE_URL/audio/voices" | python3 -c "
import json, sys
voix = json.load(sys.stdin)['voices']
print(voix[0]['id'] if voix else '')
")
if [ -z "$VOIX" ]; then
  echo "Aucune voix enrôlée : en créer une sur $VOICE_FORGE_URL/admin"
  echo "(nom + échantillon wav de quelques secondes), puis relancer ce script."
  exit 2
fi
echo "Voix utilisée : $VOIX"

echo
echo "=== 3/3 Synthèse française (première requête = chargement du modèle, ~1 min) ==="
DEBUT=$(date +%s.%N)
curl -sf "$VOICE_FORGE_URL/audio/speech" -H "Content-Type: application/json" -o "$SORTIE" -d "{
  \"model\": \"tts-1\",
  \"input\": \"Bonjour ! Le minuteur des pâtes est terminé, tu peux passer à table.\",
  \"voice\": \"$VOIX\"
}"
FIN=$(date +%s.%N)
python3 - "$SORTIE" <<'PY'
import pathlib
import sys

fichier = pathlib.Path(sys.argv[1])
octets = fichier.read_bytes()
if octets[:4] != b"RIFF" or len(octets) < 10_000:
    print(f"ÉCHEC : {fichier} n'est pas un wav plausible ({len(octets)} octets, en-tête {octets[:4]!r})")
    sys.exit(1)
print(f"OK : wav de {len(octets) // 1024} Ko produit → {fichier}")
PY
python3 -c "print(f'Latence synthèse : {$FIN - $DEBUT:.2f} s (relancer pour la latence en régime, modèle chaud)')"

echo
echo "Verdict final à l'oreille : lire $SORTIE — la voix est-elle naturelle, le français correct ?"
