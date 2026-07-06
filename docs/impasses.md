# Registre des impasses

> Savoir négatif tactique, capturé à chaud (skill `/impasses`). Une entrée = trois champs ;
> le champ « Valide tant que » rend la péremption décidable. Une impasse périmée n'est pas
> supprimée : elle est marquée comme telle et redevient une prémisse à re-vérifier (`/premisses`).
> Les contraintes permanentes (sans condition de validité) vont en ADR ou au CLAUDE.md, pas ici.

## ~~2026-07-02 — `hf download unsloth/Qwen3.6-35B-A3B-GGUF` échoue (*File not found in repository*)~~ — PÉRIMÉE le 2026-07-05

> Condition de péremption atteinte : fichiers re-listés via l'API HF le 2026-07-05.
> Verdict : seul le fichier unsloth avait changé (`Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`,
> infixe « UD ») ; les noms Voxtral (ggml-org) et bge-m3 (gpustack) étaient corrects.
> Le script `scripts/download-models.sh` est corrigé et saute désormais les fichiers présents.

- **Tenté** : télécharger `Qwen3.6-35B-A3B-Q4_K_M.gguf` depuis le dépôt unsloth via `scripts/download-models.sh`
- **Pourquoi c'est mort** : le nom de fichier a changé dans le dépôt HF ; les noms codés en dur dans le script ne correspondent plus (les 4 dépôts sont suspects, pas seulement unsloth)
- **Valide tant que** : les fichiers réels de chaque dépôt n'ont pas été re-listés (`hf download <repo> --include "*.gguf" --dry-run` ou API HF, quelques Ko)

## 2026-07-06 — borner `requires-python` ne déloge PAS numba 0.53.1 d'un lock existant

- **Tenté** : corriger l'échec de build `voice-forge` (`uv sync --extra chatterbox` → `llvmlite 0.36.0` refuse Python ≥ 3.10) en bornant `requires-python = ">=3.12,<3.13"` dans le pyproject, puis `uv lock`
- **Pourquoi c'est mort** : `uv lock` **préfère la version déjà verrouillée** tant qu'elle satisfait les contraintes, et le plafond `python < 3.10` de numba 0.53.1 est **dynamique dans son `setup.py`** — donc invisible au résolveur (il n'apparaît qu'à la compilation, d'où l'échec au build et non à la résolution). Un lock *frais* (sans incumbent) prend bien numba 0.66.0, mais un re-lock sur un lock existant garde 0.53.1. Le bornage seul ne suffit jamais pour un paquet sdist-only à métadonnée dynamique
- **Valide tant que** : `voice-forge/pyproject.toml` garde `[tool.uv] constraint-dependencies = ["numba>=0.60", "llvmlite>=0.43"]` (la borne explicite qui exclut l'incumbent et force les roues cp312). Retirer cette contrainte réarme l'impasse
