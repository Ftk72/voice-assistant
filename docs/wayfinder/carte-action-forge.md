---
label: wayfinder:map
cree: 2026-07-18
---

# Carte — L'assistant qui agit (action-forge)

## Destination

L'assistant **agit dans son environnement**, en escalade sur trois paliers
validés au réel : **(1)** il exécute des tâches demandées à la voix dans un
**Atelier** — bac à sable jetable outillé (bash, Python, fichiers, réseau
contrôlé) — et restitue oralement ; **(2)** il tient une **boucle autonome**
observe-réfléchit-agit sur des tâches multi-étapes (paradigme CodeAct :
l'action est du code exécuté) ; **(3)** il obtient des **sorties contrôlées
vers le réel** (poste, services), sous garde-fous. La carte s'arrête quand le
palier 1 parle au réel et que la voie des paliers 2-3 est dégagée.

Cadrage acté au grilling du 2026-07-18 (recherche SOTA OpenHands /
microsandbox / CodeAct versée le même jour) : **forge maison** (`action-forge`,
pattern memory-forge — pas d'OpenHands embarqué) ; sandbox **Docker jetable
d'abord**, la micro-VM (microsandbox/libkrun) ne se qualifie qu'au palier 3 ;
cerveau : le LLM local (Qwen3.6-35B-A3B via llama.cpp OpenAI-compat), à
qualifier avant d'engager la boucle.

## Notes

- **Exécution incluse** : les tickets livrent la forge et ses paliers, pas
  seulement les décisions (override wayfinder, comme les deux autres cartes).
- Skills : `/premisses` en ouverture de chaque ticket ; `/impasses` avant tout
  diagnostic ; `/tdd` (ports/adaptateurs, factices d'abord) ; `/newbie` pour
  toute commande utilisateur ; `/delegate` pour les tickets AFK volumineux ;
  `/handoff` en fin de session.
- Constantes : tout en français ; jamais de `git commit` par l'agent ; aucun
  téléchargement lourd par l'agent (modèle dédié éventuel = commandes fournies,
  l'utilisateur lance) ; port **8800** (le 8500 pressenti était occupé par le
  Pont hôte — hors compose, donc invisible dans docker-compose.yml ; réfuté à
  l'audit des prémisses du 0031) ;
  conteneurisation maximale — la forge elle-même vit dans compose, l'Atelier
  est un conteneur jetable qu'elle pilote (socket Docker).
- Références SOTA versées au grilling :
  [OpenHands SDK](https://arxiv.org/abs/2511.03690) (architecture
  contrôleur + workspace),
  [panorama sandboxing 2026](https://dev.to/manveerchawla/how-to-sandbox-ai-agents-in-2026-firecracker-gvisor-runtimes-isolation-strategies-14pk)
  (Firecracker/gVisor/libkrun),
  [comparatif auto-hébergé](https://agentmarketcap.ai/blog/2026/04/10/sandboxed-code-execution-ai-agents-e2b-modal-daytona)
  (microsandbox : micro-VM libkrun, MCP natif).

## Décisions jusqu'ici

<!-- une ligne par ticket clos : gist + lien -->

- [Contrat de l'action-forge](tickets/0031-contrat-de-l-action-forge.md) —
  **tranché au grilling et rédigé le 2026-07-19** :
  [ADR 0013](../adr/0013-action-forge-codeact-atelier-jetable.md) (CodeAct,
  Atelier jetable, trois paliers), glossaire réécrit (« Action » = pas CodeAct,
  l'ancienne devient « Commande du catalogue »), port **8800**, dossier
  d'échange à sous-dossier par Tâche seul montage, accès sans token à surface
  bornée (l'API ne parle que de Tâches, jamais de Docker), REST async + SSE
  (`/taches`, `/taches/{id}/flux`) + 3 outils MCP (`confier_tache`,
  `etat_tache`, `annuler_tache`), UI `/atelier`, Tâches en mémoire au
  palier 1. Les tickets 0033-0035 s'ouvrent dessus sans re-discuter.

## Pas encore spécifié

- **Palier 2 — la boucle longue** : tâches-projets multi-étapes (« code-moi ce
  script et teste-le ») : budget d'itérations, reprise après échec, suivi
  d'avancement — se précisera une fois la boucle courte du palier 1 vécue.
- **Palier 3 — mains sur le réel** : quelles sorties de l'Atelier vers le
  poste (fichiers, services, périphériques), avec quels garde-fous
  (approbation vocale ? liste blanche ?) ; le host-bridge (ADR 0008) est le
  précédent. Micro-VM (microsandbox/libkrun sous WSL2, KVM imbriqué) à
  qualifier en research **à ce palier** (acté au grilling).
- **Politique réseau de l'Atelier** : sortie internet de la sandbox (utile
  pour « télécharge et convertis ») face à la connexion lente et à la
  souveraineté — à trancher quand le palier 1 la réclamera.
- **L'action nourrit-elle la mémoire ?** Les tâches accomplies comme faits
  memory-forge (« j'ai converti tes photos mardi ») — à regarder une fois le
  palier 1 en usage.

## Hors périmètre

- **Sandboxes managées cloud** (E2B, Modal, Daytona) : contraires à la
  souveraineté (ADR 0007) — la référence SOTA sert d'inspiration, pas de
  dépendance.
- **OpenHands embarqué** : écarté au grilling du 2026-07-18 au profit de la
  forge maison (conventions du dépôt, français, garde-fous maîtrisés) ; ses
  idées (boucle, workspace, CodeAct) restent la référence d'architecture.
- **GPU dans l'Atelier** : aucune tâche visée n'en a besoin ; le GPU est
  réservé à la stack voix/LLM (pagination = débit divisé par 10).
