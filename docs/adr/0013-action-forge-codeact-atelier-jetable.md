# ADR 0013 — Action-forge : agir par le code (CodeAct) dans un Atelier jetable

Date : 2026-07-19 · Statut : accepté · Précise la phase 4 (le « catalogue
d'actions » de l'ADR 0008 reste la voie des sorties vers l'hôte, palier 3)

## Contexte

L'assistant parle, se souvient, consulte le monde — mais n'agit pas. La
phase 4 imaginait l'action comme une **liste blanche fermée** exécutée par le
Pont hôte (« jamais une commande arbitraire »). Ce modèle protège l'hôte mais
plafonne bas : chaque tâche nouvelle exige d'écrire une entrée de catalogue à
la main. La littérature 2025-2026 (CodeAct, OpenHands) montre qu'un LLM agit
mieux en **écrivant du code exécuté** qu'en piochant dans des outils figés — à
condition que ce code tourne dans un bac à sable qu'on peut perdre sans
regret. Recherche SOTA versée au grilling du 2026-07-18 (OpenHands SDK,
panorama sandboxing Firecracker/gVisor/libkrun, comparatif auto-hébergé) ;
les sandboxes managées cloud (E2B, Modal, Daytona) sont contraires à la
souveraineté (ADR 0007).

## Décision

Une nouvelle forge maison, **action-forge** (pattern memory-forge, port
**8800**, `env_prefix ACTION_FORGE_`), qui agit en **escalade sur trois
paliers validés au réel** :

1. **Palier 1 — la Tâche en Atelier** : une Tâche énoncée en français libre
   est confiée à la forge ; sa boucle CodeAct (observe-réfléchit-agit, LLM
   local) la décompose en **Actions** — du code exécuté dans un **Atelier**,
   conteneur Docker **jetable** : un par Tâche, borné (CPU/RAM/temps/budget de
   pas), détruit après le **Compte rendu**.
2. **Palier 2 — la boucle longue** : tâches-projets multi-étapes (reprise,
   suivi, persistance) — ne s'engage qu'une fois le palier 1 vécu.
3. **Palier 3 — les mains sur le réel** : sorties de l'Atelier vers l'hôte,
   sous garde-fous — c'est là que vivent les **Commandes du catalogue**
   (ex-« actions » de phase 4, ADR 0008 inchangé) et que la micro-VM
   (microsandbox/libkrun) se qualifiera.

Le contrat du palier 1, acté au grilling du 2026-07-19 :

- **La sûreté change de mécanisme sans disparaître** : l'arbitraire est
  permis **en sandbox**, la liste blanche demeure **sur l'hôte**. L'Atelier ne
  voit jamais le dépôt, les secrets, ni le socket Docker ; son seul montage
  est le sous-dossier de sa Tâche dans un **dossier d'échange** hôte dédié
  hors dépôt.
- **La garde est dans la surface de l'API, pas dans une auth** : la forge
  écoute sur 127.0.0.1 comme toute la stack, sans token ; son API ne parle
  que de Tâches — aucune route n'expose d'opération Docker. Le socket (monté
  dans la forge seule) ne sert qu'au cycle de vie des Ateliers, sur une image
  fixe ; une Tâche non autorisée retombe donc dans la même sandbox qu'une
  légitime.
- **Un seul cerveau** : dialogue-forge transmet l'énoncé tel que dit et ne
  planifie rien ; la décomposition en Actions appartient à l'action-forge.
- **API** : REST asynchrone (`POST /taches` → 202 ; `GET /taches`,
  `GET /taches/{id}` — statut, compte rendu, journal des Actions ;
  `POST /taches/{id}/annulation` ; `GET /taches/{id}/flux` en SSE pour le
  suivi temps réel), module d'interface `/atelier`, `/health`, `/mcp` avec
  trois outils orientés voix : `confier_tache`, `etat_tache`,
  `annuler_tache` — le Compte rendu se restitue oralement, le journal ne se
  lit jamais.
- **Éphémère au palier 1** : Tâches en mémoire process (un redémarrage les
  perd) ; les Ateliers sont étiquetés et les orphelins détruits au démarrage.
  La persistance graduera au palier 2.

## Conséquences

- `CONTEXT.md` est réécrit : **Action** prend le sens CodeAct (un pas de la
  boucle, du code exécuté en Atelier — jamais sur l'hôte) ; l'ancienne
  « Action » de phase 4 devient **Commande du catalogue**. Précédent : la
  réécriture du glossaire à l'ADR 0009.
- Le port pressenti 8500 de la carte action-forge était **occupé** (Pont
  hôte, hors compose donc invisible dans `docker-compose.yml`) — l'action-forge
  prend 8800, la topologie du CLAUDE.md doit l'ajouter.
- La forge tient le socket Docker : un pouvoir root de fait sur l'hôte,
  assumé et borné par contrat (surface API, image fixe, aucun montage
  sensible). Le smoke test du premier Atelier réel (ticket 0033) validera que
  le pilotage de conteneurs frères depuis compose fonctionne.
- Le GPU reste hors de l'Atelier ; aucune sandbox managée cloud, jamais.

## Alternatives écartées

- **OpenHands embarqué** : conventions du dépôt (français, TDD,
  ports/adaptateurs) et garde-fous maîtrisés valent plus que la boucle toute
  faite ; ses idées (contrôleur + workspace, CodeAct) restent la référence.
- **Étendre le catalogue du Pont hôte** : garder « jamais une commande
  arbitraire » partout condamne à écrire chaque tâche à la main — le
  catalogue reste la bonne réponse pour l'hôte, pas pour le travail en
  sandbox.
- **Micro-VM dès le palier 1** (microsandbox/libkrun) : isolation supérieure,
  mais KVM imbriqué sous WSL2 à qualifier — reportée au palier 3, où le
  besoin la justifiera.
- **Token d'API (pattern host-bridge)** : défense en profondeur jugée sans
  objet sur un localhost mono-utilisateur dont la surface d'attaque est déjà
  la sandbox ; aurait imposé la plomberie token au client MCP de
  dialogue-forge.
- **Plan structuré par dialogue-forge** : deux cerveaux qui planifient — le
  ticket 0032 qualifie justement le modèle pour la boucle côté forge.
