---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: []
carte: carte.md
---

# Le Dialogue Forge survit à une forge d'outils absente

## Question

Constaté au réel le 2026-07-20 (validation du ticket
[L'action à la voix](0035-l-action-a-la-voix.md)) : le Dialogue Forge
**meurt au démarrage, puis boucle en `Restarting`**, parce qu'**une seule**
de ses forges MCP ne répondait pas — ici `action`, repartie sur une image
périmée sans route `/mcp`. L'assistant perd la **parole entière** parce qu'il
a perdu **un outil**.

Mécanique : `OutilsMCP.lister_outils` (`dialogue-forge/app/outils/mcp.py`)
itère sur `mcp_urls` sans aucune tolérance à l'échec — un `McpError` remonte
jusqu'au lifespan, `Application startup failed`, et la politique
`restart: unless-stopped` transforme l'échec en boucle. Le
`depends_on: condition: service_healthy` ne protège de rien : `/health`
répond `ok` sur une image périmée.

Le seuil du CIR est franchi — ce n'est plus une complexité défensive
spéculative, **le problème s'est constaté**, et son coût est maximal (mutisme
total) pour une cause mineure (un outil sur quatre). Détail et diagnostic dans
`docs/impasses.md` (entrée du 2026-07-20).

À trancher en codant :

- **La dégradation** : une forge injoignable au démarrage retire ses outils du
  catalogue et laisse le Dialogue Forge parler — mais l'assistant doit-il le
  *savoir* (le dire s'il ne peut pas faire) ou l'ignorer ?
- **La reprise** : le catalogue est chargé une fois au démarrage. Une forge
  revenue après coup reste-t-elle invisible jusqu'au prochain redémarrage, ou
  se retente-t-elle (au premier appel ? périodiquement) ?
- **Le point d'audit** : où se voit une forge tombée — logs, `/health`
  enrichi, module de réglage ? Sans lui, la dégradation devient un mode
  silencieux, et on aura remplacé une panne bruyante par une panne muette.

## Critère de clôture

Stack démarrée avec une forge d'outils volontairement éteinte : le Dialogue
Forge répond, parle, et utilise les outils des forges restantes ; la forge
absente est constatable sans lire un traceback.

## Résolution

Les trois points tranchés : **dégradation silencieuse** côté LLM (les outils
d'une forge injoignable disparaissent du catalogue, rien n'est injecté dans
le prompt — le préfixe reste stable pour le cache de contexte de llama.cpp) ;
**reprise à chaud avec palier** (`mcp_palier_reprise_s`, 60 s par défaut),
retentée uniquement en tout début de tour, sans tâche de fond ; **point
d'audit** via un log `WARNING`/`INFO` par forge et `/health` enrichi d'une
clé `forges_outils` quand le moteur l'expose.

Fichiers touchés : `app/outils/base.py` (méthode concrète `rafraichir`),
`app/outils/mcp.py` (tolérance dans `lister_outils`, reprise dans
`rafraichir`, audit dans `etat_forges`), `app/outils/fake.py` (doublure de
`rafraichir` pour les tests), `app/config.py` (`mcp_palier_reprise_s`),
`app/main.py` (câblage du palier), `app/dialogue.py` (`jouer_tour` appelle
`rafraichir` avant l'injection mémoire), `app/routes/api.py` (`/health`
enrichi, `{"status": "ok"}` inchangé avec le backend factice). Tests dans
`tests/test_tolerance_forges_outils.py`, dont un test de non-régression qui
démarre l'app avec le backend `mcp` et une URL en échec permanent.

**Reste à valider au réel** (le ticket reste `ouvert` : son critère de clôture
est une stack démarrée avec une forge volontairement éteinte, pas une suite de
tests verte). Limite connue et assumée hors périmètre : une forge qui meurt
**après** le démarrage garde ses outils au catalogue, et l'appel lèvera au
moment où le LLM les demandera — seul le démarrage est couvert ici.
