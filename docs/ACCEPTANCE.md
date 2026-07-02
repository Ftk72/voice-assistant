# Critères d'acceptation — Assistant vocal local

Issus de la session de grilling du 2026-07-02. C'est contre ces scénarios que la v1 est jugée terminée.

## Scénario principal (mode appel)

1. Dans OpenWebUI, je sélectionne le persona « Batman » et je clique sur le bouton d'appel.
2. Je pose une question en français, naturellement.
3. La réponse audio démarre en **≤ 2 s** après ma fin de phrase, avec la voix clonée « Batman ».
4. La réponse est orale par nature : pas de markdown lu à voix haute, pas d'énumérations mécaniques.
5. Au casque (preset « interruption activée »), je peux couper la parole à l'assistant et il s'arrête.

## Scénario voix

1. Je dépose un dossier `voices/Emma/` avec un `speaker.wav` de quelques secondes (ou je l'importe via la mini-page d'admin).
2. Sans redémarrer quoi que ce soit, « Emma » apparaît dans le sélecteur de voix d'OpenWebUI (Settings → Audio) et dans les choix de voix par persona.
3. Un aperçu est écoutable depuis la mini-page d'admin.

## Exigences transverses

- **Latence** : ≤ 2 s fin de parole → début de réponse audio (mesurée à l'étape docker-compose ; optimisation si dépassé).
- **Presets audio documentés** : casque (interruption activée) et haut-parleurs (interruption désactivée) — réglage natif OpenWebUI, un clic.
- **Périmètre v1** : démarrage de l'appel au clic. Mot d'éveil = phase 2 éventuelle, hors v1.
- **100 % local** : aucun appel réseau sortant à l'exécution (hors téléchargement initial des modèles).
- **Sécurité** : tous les services techniques (llama.cpp LLM/STT, Voice Forge) liés à `127.0.0.1` uniquement ; seul OpenWebUI est exposé.
- **Éthique** : voix clonées de personnes réelles réservées à un usage strictement personnel ; aucune diffusion publique des sorties audio.
- **VRAM** : les trois modèles coexistent dans 16 Go avec ~4 Go de marge (voir ADR 0004).
