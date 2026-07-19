---
label: wayfinder:research
statut: clos
assigne: claude (session 2026-07-19, délégué opus)
bloque-par: []
carte: carte-cerp
---

# CERP — Observer la méthode (skills et mémoire agent)

## Question

Phase Observe, moitié « méta » : lire la couche que l'utilisateur a écrite
ou adoptée **pour piloter l'agent** — `~/.claude/skills` (grilling,
prémisses, impasses, newbie, delegate, wayfinder, handoff, tdd…), la mémoire
agent du projet (`~/.claude/projects/-home-ftk-voice-assistant/memory/`), et
les sections « méthode » de CLAUDE.md.

Produire `docs/cerp/observations-methode.md` : ce que chaque skill impose,
interdit ou ritualise ; ce que la mémoire retient et corrige ; les
observations séparées des interprétations. **Vigilance circularité** (actée
au grilling) : skills et mémoire sont déjà des condensés interprétés — les
consigner comme *déclarations* de l'utilisateur sur sa méthode, à confronter
plus tard à sa *pratique* (rapport du dépôt), jamais comme vérité établie.

AFK, délégable ; aucun téléchargement.

## Critère de clôture

Le rapport d'observation de la méthode existe, chaque déclaration sourcée
(fichier, ligne), les tensions pressenties entre déclaré et pratiqué notées
comme questions ouvertes — prêt à nourrir la reconstruction du CIR.

## Verdict (2026-07-19)

Livré : `docs/cerp/observations-methode.md` — 43 skills lus (4 sur mesure
francophones : delegate/impasses/newbie/premisses ; 5 adoptés via CLAUDE.md ;
~30 génériques dormants inventoriés), mémoire agent décortiquée (6 fichiers,
tous d'origine agent `type: feedback` — doublement interprétés, signalé),
sections méthode de CLAUDE.md. Circularité tenue : tout formulé en
*déclarations*. **8 questions ouvertes** en §6 à trancher contre le rapport
du dépôt — dont la croyance périmée « zéro fork OpenWebUI » encore en
mémoire malgré l'ADR 0009, et l'origine (utilisateur vs agent) des skills
sur mesure. Vérifié par l'agent principal : périmètre au `git status`,
relecture intégrale.
