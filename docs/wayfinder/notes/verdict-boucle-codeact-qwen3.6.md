# Verdict — le cerveau tient-il la boucle ? (Qwen3.6-35B-A3B, CodeAct)

Date : 2026-07-20 · Statut : sonde exécutée sur la stack réelle (llama.cpp
8001, `--reasoning off`) · Répond au ticket wayfinder 0032.

## Méthode

Sonde jetable (`sonde_boucle.py`, non versionnée — script de recherche, pas
du code de forge) : 5 tâches type palier 1 (créer/relire un fichier,
convertir CSV→JSON, script Python + exécution, calcul en plusieurs pas,
lire→calculer→écrire), chacune jouée dans **deux modes** contre le même
modèle :

- **Natif** : tool-calling OpenAI-compat de llama.cpp, 5 outils simulés
  (`ecrire_fichier`, `lire_fichier`, `calculer`, `executer_python`,
  `terminer`), système en français, boucle jusqu'à 8 pas.
- **CodeAct** : le modèle répond par un unique bloc ```python``` exécuté dans
  un bac à sable local qui expose seulement `ecrire_fichier`/`lire_fichier`/
  `print` ; la sortie standard est réinjectée comme observation ; fin sur
  `print('TERMINÉ: ...')`.

Outils **simulés** (système de fichiers factice en mémoire, aucune
exécution réelle, aucun Atelier) : le but est de qualifier le modèle pour la
boucle, pas de faire tourner l'action-forge. Prémisses vérifiées avant
sonde : stack Docker up, `--reasoning off` actif (sinon `content` vide —
impasse 2026-07-06), tool-calling natif fonctionne en un tour, 8,5 Go de
VRAM libres sur le 5080 (16,3 Go, 35B déjà chargé ~7,5 Go utilisés).

## Résultats

| Tâche | Mode natif | Mode CodeAct |
|---|---|---|
| T1 créer + relire | ✅ 3 pas, 5,5 s | ✅ 1 pas, 4,6 s |
| T2 CSV → JSON | ✅ 3 pas, 10,3 s | ✅ 1 pas, 6,3 s |
| T3 script + somme(1..100) | ✅ 2 pas, 4,0 s | ✅ 1 pas, 3,7 s |
| T4 calcul en 3 étapes | ⚠️ 5 pas, 9,8 s — *voir correction* | ✅ 1 pas, 4,5 s |
| T5 lire → calculer → écrire | ✅ 4 pas, 7,5 s | ✅ 1 pas, 15,5 s |

**Correction sur T4/natif** : le harness l'a d'abord compté en échec
(« outil halluciné »), mais la relecture du transcript montre que c'est un
artefact de la sonde, pas du modèle — le 3ᵉ appel `calculer("round(18.0,
1)")` a heurté un `eval` sandboxé sans `round` (limite de mon outil factice,
pas un outil inventé). **Le modèle a détecté l'échec de l'outil et basculé
seul vers `executer_python` pour obtenir le même résultat**, puis a conclu
correctement (« La réponse finale est 18,0 », calcul exact). C'est un signal
positif de robustesse (récupération autonome après erreur d'outil), pas un
échec de boucle. **Verdict réel : 5/5 en mode natif.**

**Sur la dérive anglaise** : l'heuristique a flagué 3 essais CodeAct (T2,
T3, T5), mais en relisant le code produit, ce sont des tokens Python
génériques (`csv_data`, `# Parse the CSV data`, `threshold`) — normal pour
du code, qui est rarement rédigé en français idiomatique. **Le français
tenu là où ça compte** : les messages `print('TERMINÉ: ...')` et les
résumés finaux sont systématiquement en français correct, dans les 10
essais. Aucune dérive anglaise dans le canal destiné à la voix.

**Aucune boucle infinie, aucune vraie hallucination d'outil**, dans les 10
essais (5 tâches × 2 modes).

## Comparaison des modes d'action

- **Natif** : chaque étape est un aller-retour LLM ↔ outil observable
  séparément (journal clair, un pas = une action tracée) — plus verbeux
  (2 à 5 pas), latence cumulée plus longue pour les tâches à plusieurs
  outils (T5 : 7,5 s vs 15,5 s CodeAct — voir nuance ci-dessous).
- **CodeAct** : le modèle enchaîne souvent lecture + calcul + écriture en un
  seul bloc de code puisque l'exécution locale ne nécessite pas de
  réinjecter chaque résultat intermédiaire — d'où le « 1 pas » quasi
  systématique. **Nuance importante** : cette rapidité tient en partie à ce
  que les outils simulés sont déterministes et sans latence propre ; un
  Atelier réel (sous-processus, réseau, erreurs imprévisibles) forcerait
  probablement plus de tours d'observation, donc l'écart mode natif/CodeAct
  mesuré ici est optimiste pour CodeAct.
- Le seul cas où CodeAct a été *plus lent en durée totale* (T5, 15,5 s pour
  1 pas) montre que le nombre de pas n'est pas un bon proxy de latence : un
  seul appel LLM peut coûter cher en tokens de génération (code plus long).

## Verdict

**Le modèle tient la boucle courte du palier 1, dans les deux modes
d'action, sur les 5 tâches types testées.** Aucune dérive française à
signaler dans le canal voix, aucune boucle infinie, une seule erreur — et
c'était l'outil factice, pas le modèle, qui a d'ailleurs su la contourner
seul. CodeAct converge en moins de pas ; le mode natif produit un journal
plus fin (utile pour le Compte rendu détaillé de l'ADR 0013 si besoin de
tracer chaque Action). Rien n'empêche d'ouvrir le ticket 0033 (l'Atelier
sandbox jetable) sur ce cerveau.

## Plan B — non engagé, dimensionné pour mémoire

Le verdict étant positif, **aucune bascule n'est nécessaire aujourd'hui**.
Si un futur palier (2, boucle longue ; ou des tâches réelles plus ambiguës
que ces 5 sondes) révèle des dérives que Qwen3.6-35B-A3B ne tient pas,
candidats pour un second modèle dédié à l'agir, en GGUF llama.cpp,
dimensionnés face aux **8,5 Go de VRAM libres** mesurés (35B déjà chargé) :

- **Qwen2.5-Coder-7B-Instruct** (GGUF, Q4_K_M ~4,5 Go) — généraliste code +
  tool-calling correct, déjà dans la même famille de templates que le 35B en
  place (moindre risque de surprise côté llama.cpp).
- **Hermes-3-Llama-3.1-8B** (GGUF, Q4_K_M ~4,9 Go) — spécifiquement
  fine-tuné function-calling/agentique, réputation établie sur les
  benchmarks de tool-use.
- **xLAM-7b-fc-r (Salesforce)** (GGUF si disponible, sinon à convertir) —
  spécialiste function-calling pur, à évaluer si le besoin se limite à des
  appels d'outils très fiables plutôt qu'à du code général.

Tous tiennent dans les ~8,5 Go libres à côté du 35B déjà chargé (pas de
déchargement nécessaire), sous réserve de vérifier au réel la compatibilité
sm_120 (RTX 5080) comme pour tout binaire CUDA — aucune de ces pistes n'a
été testée, aucun poids n'a été téléchargé. Bascule à la demande
envisageable (charger le petit modèle seulement pour la boucle agentique,
le 35B restant pour le dialogue) mais l'arbitrage routage/coexistence est à
trancher **si et quand** ce Plan B s'engage — hors périmètre de ce ticket.

## Écarts par rapport au brief

- 5 tâches (borne basse de la fourchette « 3 à 5 » demandée) : les 5
  premières ont suffi à obtenir un signal net (5/5 dans les deux modes) ;
  pas de tâche supplémentaire jugée nécessaire pour trancher.
- Outils simulés déterministes (pas de latence réseau, pas d'erreurs
  aléatoires) : bon pour qualifier le raisonnement multi-pas et le respect
  du français, insuffisant pour mesurer la résilience à des outils lents ou
  qui échouent de façon imprévisible — à revérifier une fois l'Atelier réel
  du ticket 0033 posé (outils réels, pas simulés).
- Le script de sonde n'est pas versionné (jetable, hors convention forge) ;
  transcripts complets disponibles dans la session si besoin de relecture
  fine.
