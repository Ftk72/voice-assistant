#!/usr/bin/env bash
# Banc de mesure de la latence technique « fin de parole → début de réponse
# audio » (critère produit : ≤ 2 s, docs/ACCEPTANCE.md).
#
# Chaîne mesurée : STT (whisper.cpp) → LLM jusqu'à la première phrase
# (llama.cpp, flux SSE) → TTS de cette phrase (Voice Forge). La synthèse du
# wav de question, elle, est HORS chrono : c'est la préparation du stimulus,
# pas une étape de la boucle voix→voix.
set -u

STT_URL="${STT_URL:-http://127.0.0.1:8002}"
LLM_URL="${LLM_URL:-http://127.0.0.1:8001}"
TTS_URL="${TTS_URL:-http://127.0.0.1:8100}"
VOIX="${VOIX:-VoixDeTest}"
QUESTION_WAV="${QUESTION_WAV:-/tmp/question.wav}"

echo "=== Préparation du stimulus (hors chrono) : synthèse de la question ==="
# Un stimulus déjà présent est réutilisé tel quel : permet de fournir un wav
# de meilleure qualité que la voix de test (ex. QUESTION_WAV=/tmp/question-claire.wav).
if [ -s "$QUESTION_WAV" ]; then
  echo "Stimulus existant réutilisé : $QUESTION_WAV"
else
curl -sf "$TTS_URL/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"tts-1\",\"input\":\"Quelle heure est-il ?\",\"voice\":\"${VOIX}\",\"response_format\":\"wav\"}" \
  -o "$QUESTION_WAV" \
  || { echo "ÉCHEC : le Voice Forge ($TTS_URL) ne répond pas à /v1/audio/speech — abandon."; exit 1; }
fi
[ -s "$QUESTION_WAV" ] || { echo "ÉCHEC : le wav de question est vide ($QUESTION_WAV) — abandon."; exit 1; }
echo "OK : $QUESTION_WAV prêt."

echo
echo "=== 1/3 STT : transcription de la question ($STT_URL) ==="
DEBUT_STT=$(date +%s.%N)
REPONSE_STT=$(curl -sf "$STT_URL/v1/audio/transcriptions" -F "file=@${QUESTION_WAV}")
STATUT=$?
FIN_STT=$(date +%s.%N)
[ $STATUT -eq 0 ] || { echo "ÉCHEC : le service STT ($STT_URL) ne répond pas — abandon."; exit 1; }

TEXTE=$(echo "$REPONSE_STT" | python3 -c "
import sys, json
try:
    donnees = json.load(sys.stdin)
except json.JSONDecodeError:
    print('ÉCHEC : réponse STT non-JSON', file=sys.stderr)
    sys.exit(1)
texte = donnees.get('text', '').strip()
if not texte:
    print('ÉCHEC : champ text absent ou vide dans la réponse STT', file=sys.stderr)
    sys.exit(1)
print(texte)
")
[ -n "$TEXTE" ] || { echo "ÉCHEC : impossible d'extraire le texte transcrit — abandon."; exit 1; }
DUREE_STT=$(python3 -c "print(f'{$FIN_STT - $DEBUT_STT:.3f}')")
echo "Texte transcrit : « $TEXTE »"
echo "Durée STT : ${DUREE_STT} s"

echo
echo "=== 2/3 LLM : premier token puis première phrase ($LLM_URL) ==="
CORPS_LLM=$(TEXTE_TRANSCRIT="$TEXTE" python3 -c "
import json, os
print(json.dumps({
    'model': 'q',
    'messages': [{'role': 'user', 'content': os.environ['TEXTE_TRANSCRIT']}],
    'max_tokens': 80,
    'stream': True,
}))
")

DEBUT_LLM=$(date +%s.%N)
RESULTAT_LLM=$(curl -sN "$LLM_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "$CORPS_LLM" | python3 -c "
import sys, json, time

debut = time.monotonic()
premier_token_t = None
premiere_phrase_t = None
contenu = ''

for ligne in sys.stdin:
    ligne = ligne.strip()
    if not ligne.startswith('data:'):
        continue
    charge = ligne[len('data:'):].strip()
    if charge == '[DONE]':
        break
    try:
        morceau = json.loads(charge)
    except json.JSONDecodeError:
        continue
    deltas = morceau.get('choices', [{}])
    if not deltas:
        continue
    delta = deltas[0].get('delta', {})
    fragment = delta.get('content') or ''
    if not fragment:
        continue
    if premier_token_t is None:
        premier_token_t = time.monotonic() - debut
    contenu += fragment
    if premiere_phrase_t is None and any(p in fragment for p in ('.', '!', '?')):
        premiere_phrase_t = time.monotonic() - debut
        break

if premier_token_t is None:
    print('ERREUR: aucun token de contenu reçu', file=sys.stderr)
    sys.exit(1)
if premiere_phrase_t is None:
    # Pas de ponctuation de fin de phrase dans les 80 tokens : on prend tout le contenu reçu.
    premiere_phrase_t = time.monotonic() - debut

# Première phrase = jusqu'au premier signe de ponctuation forte inclus.
import re
correspondance = re.search(r'^(.*?[.!?])', contenu, re.DOTALL)
premiere_phrase = correspondance.group(1).strip() if correspondance else contenu.strip()

print(json.dumps({
    'premier_token': premier_token_t,
    'premiere_phrase_duree': premiere_phrase_t,
    'premiere_phrase': premiere_phrase,
}))
")
STATUT_LLM=$?
FIN_LLM=$(date +%s.%N)

[ $STATUT_LLM -eq 0 ] && [ -n "$RESULTAT_LLM" ] || { echo "ÉCHEC : le service LLM ($LLM_URL) n'a pas produit de flux exploitable — abandon."; exit 1; }

DUREE_PREMIER_TOKEN=$(echo "$RESULTAT_LLM" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin)['premier_token']:.3f}\")")
DUREE_PREMIERE_PHRASE=$(echo "$RESULTAT_LLM" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin)['premiere_phrase_duree']:.3f}\")")
PREMIERE_PHRASE=$(echo "$RESULTAT_LLM" | python3 -c "import sys, json; print(json.load(sys.stdin)['premiere_phrase'])")

echo "Première phrase du LLM : « $PREMIERE_PHRASE »"
echo "Durée LLM (premier token) : ${DUREE_PREMIER_TOKEN} s"
echo "Durée LLM (première phrase) : ${DUREE_PREMIERE_PHRASE} s"

echo
echo "=== 3/3 TTS : synthèse de la première phrase ($TTS_URL) ==="
CORPS_TTS=$(PHRASE_TTS="$PREMIERE_PHRASE" VOIX_TTS="$VOIX" python3 -c "
import json, os
print(json.dumps({
    'model': 'tts-1',
    'input': os.environ['PHRASE_TTS'],
    'voice': os.environ['VOIX_TTS'],
    'response_format': 'wav',
}))
")
REPONSE_TTS="/tmp/reponse-latence.wav"
DEBUT_TTS=$(date +%s.%N)
curl -sf "$TTS_URL/v1/audio/speech" -H "Content-Type: application/json" -d "$CORPS_TTS" -o "$REPONSE_TTS"
STATUT_TTS=$?
FIN_TTS=$(date +%s.%N)
[ $STATUT_TTS -eq 0 ] && [ -s "$REPONSE_TTS" ] || { echo "ÉCHEC : le Voice Forge n'a pas synthétisé la réponse — abandon."; exit 1; }
DUREE_TTS=$(python3 -c "print(f'{$FIN_TTS - $DEBUT_TTS:.3f}')")
echo "Durée TTS : ${DUREE_TTS} s"
if python3 -c "exit(0 if $DUREE_TTS < 0.3 else 1)"; then
  echo "(cache possible : durée TTS < 0,3 s)"
fi

echo
echo "=== Bilan ==="
TOTAL=$(python3 -c "print(f'{$DUREE_STT + $DUREE_PREMIERE_PHRASE + $DUREE_TTS:.3f}')")
printf '%-35s %8s s\n' "STT" "$DUREE_STT"
printf '%-35s %8s s\n' "LLM (premier token)" "$DUREE_PREMIER_TOKEN"
printf '%-35s %8s s\n' "LLM (première phrase)" "$DUREE_PREMIERE_PHRASE"
printf '%-35s %8s s\n' "TTS" "$DUREE_TTS"
printf '%-35s %8s s\n' "TOTAL (STT + LLM phrase + TTS)" "$TOTAL"

if python3 -c "exit(0 if $TOTAL <= 2.0 else 1)"; then
  echo
  echo "VERT : latence totale ${TOTAL} s ≤ 2,0 s (critère produit ACCEPTANCE.md)."
  exit 0
else
  echo
  echo "ROUGE : latence totale ${TOTAL} s > 2,0 s (critère produit ACCEPTANCE.md)."
  exit 1
fi
