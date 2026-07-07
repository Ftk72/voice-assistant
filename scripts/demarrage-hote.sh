#!/usr/bin/env bash
# Démarrage/réparation de la stack après un boot Windows (lancé par la tâche
# de session Windows — voir scripts/installer-demarrage.md).
#
# Répare les deux pièges connus du boot (docs/impasses.md) :
#   1. voice-forge démarré avant que le partage de fichiers Docker Desktop soit
#      prêt → montage ./voices vu VIDE → TTS en 400 « Voix inconnue ».
#   2. le LLM se fait paginer en RAM partagée par les autres charges GPU →
#      il doit (re)démarrer EN DERNIER.
# Puis lance le Pont hôte (hors Docker, ADR 0008) s'il ne tourne pas.
set -u
cd "$(dirname "$0")/.."
JOURNAL="$HOME/.demarrage-hote.log"
exec >>"$JOURNAL" 2>&1
echo "=== $(date '+%F %T') démarrage-hôte ==="

# --- 0. Docker : démarrer Docker Desktop si besoin, attendre le démon (10 min max)
if ! docker info >/dev/null 2>&1; then
  "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" &
fi
for _ in $(seq 1 120); do docker info >/dev/null 2>&1 && break; sleep 5; done
docker info >/dev/null 2>&1 || { echo "docker injoignable, abandon"; exit 1; }

# --- 1. Stack debout
docker compose up -d
for _ in $(seq 1 60); do
  [ -z "$(docker compose ps --format '{{.Health}}' | grep -v healthy)" ] && break
  sleep 5
done

# --- 2. Piège du montage voices vide (redémarrage PC)
if [ -n "$(ls -A voices/ 2>/dev/null)" ] && \
   [ -z "$(docker compose exec -T voice-forge ls -A /data/voices/ 2>/dev/null)" ]; then
  echo "montage voices vide → recréation de voice-forge"
  docker compose up -d --force-recreate voice-forge
  for _ in $(seq 1 30); do
    [ "$(docker compose ps --format '{{.Health}}' voice-forge)" = healthy ] && break
    sleep 5
  done
fi

# --- 3. Le LLM redémarre en dernier (poids paginés sinon)
docker compose restart llm
for _ in $(seq 1 40); do
  [ "$(docker compose ps --format '{{.Health}}' llm)" = healthy ] && break
  sleep 5
done

# --- 4. Pont hôte (hors Docker) : enceintes + actions liste blanche
if ! curl -sf http://127.0.0.1:8500/health >/dev/null 2>&1; then
  echo "lancement du Pont hôte"
  TOKEN=$(grep -oP '^HOST_BRIDGE_TOKEN=\K.*' .env 2>/dev/null || true)
  cd host-bridge
  [ -f catalog.toml ] || cp catalog.example.toml catalog.toml
  HOST_BRIDGE_HOST=0.0.0.0 \
  HOST_BRIDGE_PLAYER=auto \
  HOST_BRIDGE_TOKEN="${TOKEN:-}" \
    nohup uv run python -m app >>"$HOME/.pont-hote.log" 2>&1 &
  cd ..
  for _ in $(seq 1 12); do curl -sf http://127.0.0.1:8500/health >/dev/null 2>&1 && break; sleep 5; done
fi

echo "état final :"
docker compose ps --format '{{.Service}}: {{.Health}}'
curl -sf http://127.0.0.1:8500/health >/dev/null 2>&1 && echo "pont-hôte: ok" || echo "pont-hôte: KO"
