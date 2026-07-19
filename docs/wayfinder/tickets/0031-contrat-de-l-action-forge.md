---
label: wayfinder:grilling
statut: clos
assigne:
bloque-par: []
carte: carte-action-forge
---

# Contrat de l'action-forge (ADR, glossaire, API)

## Question

Premier ticket de la carte : fixer le **contrat** de la nouvelle forge avant
d'en poser une ligne. Grilling + `/domain-modeling`, puis rédaction :

- **ADR** : une nouvelle décision d'architecture (forge maison CodeAct,
  sandbox Docker jetable, escalade trois paliers) — actée au grilling du
  2026-07-18, à formaliser dans `docs/adr/`.
- **Glossaire** (`CONTEXT.md`) : nommer le domaine — l'**Atelier** (le bac à
  sable jetable), la **Tâche** (ce qu'on confie à la voix), l'**Action**
  (un pas de la boucle : du code exécuté, paradigme CodeAct), le **Compte
  rendu** (ce que la voix restitue).
- **API et outils MCP** : quelles routes FastAPI et quels outils MCP orientés
  voix (« lance la tâche, restitue oralement le compte rendu — ne lis pas les
  logs ») ; port pressenti 8500 ; `env_prefix` ACTION_FORGE_.
- **Frontières** : ce que dialogue-forge délègue à l'action-forge (et comment
  la Tâche s'énonce), ce que l'Atelier peut monter (répertoire d'échange ?)
  et ce qu'il ne voit jamais (le dépôt, les secrets, le socket).

## Tranché au grilling du 2026-07-19 — CLOS

Prémisses auditées en ouverture : **8500 était occupé** (port par défaut du
Pont hôte, hors compose donc invisible dans docker-compose.yml) → port
**8800** ; et « Action » désignait déjà, dans CONTEXT.md phase 4, la commande
du catalogue fermé — collision de vocabulaire réconciliée ci-dessous.

- **Vocabulaire** : « Action » passe au sens CodeAct (un pas de boucle = du
  code exécuté dans l'Atelier, jamais sur l'hôte) ; l'ancienne devient
  « Commande du catalogue » (Pont hôte, liste blanche, ADR 0008 intact — voie
  du palier 3). La sûreté change de mécanisme sans disparaître : arbitraire
  EN sandbox, liste blanche SUR l'hôte.
- **Énoncé** : la Tâche est du français libre transmis tel que dit + bornes
  posées par la forge (budget de pas, durée) ; un seul cerveau — dialogue-forge
  ne planifie rien.
- **Échange** : un dossier hôte dédié hors dépôt, un sous-dossier par Tâche,
  seul montage de l'Atelier. Jamais montés : dépôt, secrets, socket.
- **Accès** : 127.0.0.1 sans token, comme toute la stack ; la garde est la
  surface du contrat (l'API ne parle que de Tâches, jamais de Docker ; socket
  réservé au cycle de vie des Ateliers, image fixe).
- **API/MCP** : REST async (`POST /taches` → 202, `GET /taches`,
  `GET /taches/{id}`, `POST /taches/{id}/annulation`) + **SSE**
  (`GET /taches/{id}/flux`) ; outils MCP `confier_tache`, `etat_tache`,
  `annuler_tache` (Compte rendu restitué oralement, journal jamais lu) ;
  module d'interface `/atelier` ; `env_prefix` ACTION_FORGE_.
- **Persistance** : Tâches en mémoire au palier 1 (Ateliers orphelins
  étiquetés, détruits au démarrage) ; la persistance graduera au palier 2.

Livré : [ADR 0013](../../adr/0013-action-forge-codeact-atelier-jetable.md),
glossaire CONTEXT.md réécrit (section « Agir »), carte corrigée (port 8800).

## Critère de clôture

ADR rédigé, glossaire enrichi, contrat d'API/MCP acté — les tickets
d'exécution (Atelier, boucle) peuvent s'ouvrir dessus sans re-discuter.
**Atteint le 2026-07-19.**
