# Feuille de route — code-route

Ce fichier est lu par une machine : `validate-app.sh` refuse de déployer s'il manque ou s'il ne
contient aucun lot au format ci-dessous, et `app-test.sh` lit la commande de test. Garder les titres
tels quels.

App livrée avant l'obligation de feuille de route : le Lot 1 résume l'existant. Les lots suivants
viennent de l'analyse du 2026-10-31 ; la vue d'ensemble est dans `to_do_global.md`, à la racine du
dépôt du lab. Légende : [C] constaté, [D] déduit.

## Commande de test
python manage.py test

## Lot 1 — Existant : fiches, quiz, bilan, génération de questions   ·   statut : livré
**Objectif :** apprentissage du code de la route : fiches, quiz par thème, bilan personnel,
génération de questions par Mistral (worker Celery et Redis).
**Tâches :**
- [x] Fonctionnalités en service ; correctifs du chantier tests (corrections lisibles pendant un quiz, double réponse, entrées mal formées)
- [x] Reprise du quiz à la première question sans réponse (`10374c6`)
**Tests à passer avant de clore le lot :**
- [x] ≈ 90 tests backend (`backend/api/tests/`) ; `cloisonnement.spec.ts` identique au gabarit
**Vérifié le :** 2026-10-31 — relevé par lecture (version en service = `10374c6`), tests non rejoués.

## Lot 2 — Vérification en navigateur du correctif du quiz   ·   statut : à faire
**Objectif :** prouver `10374c6`. Le rapport le dit « non vérifié en navigateur, ni par un build ».
**Tâches :**
- [ ] Jouer dans `lab-runner`, avec `e2e_member`, les scénarios du troisième tour de `chantiers/tests/rapports/route-robot.md`
**Tests à passer avant de clore le lot :**
- [ ] Les scénarios passent ; un quiz interrompu reprend à la première question sans réponse ; une erreur d'API s'affiche
**Vérifié le :**

## Lot 3 — Sessions abandonnées dans le bilan   ·   statut : à faire
**Objectif :** Ⓟ à décider. Une session non terminée compte aujourd'hui comme des échecs dans « Mon bilan ».
**Tâches :**
- [ ] Ⓟ Exclure les sessions non terminées, ou les afficher à part
**Tests à passer avant de clore le lot :**
- [ ] Test `MonBilan` sur une session ouverte, conforme à la règle retenue
**Vérifié le :**

## Lot 4 — Gabarit front, documentation et chemin à portes   ·   statut : à faire
**Objectif :** même comportement que le gabarit corrigé (T3), un README, un déploiement par le moteur (T1).
**Tâches :**
- [ ] Polices en chemin relatif (`styles.scss:3-11`) ; `tokenBases()` ; PKCE. Le `redirectUri` est déjà sur la page courante.
- [ ] Retirer `version: "3.9"`, obsolète, du compose
- [ ] `README.md` : contenu, génération IA (clé, coût), tests
**Tests à passer avant de clore le lot :**
- [ ] WOFF2 en 200 derrière `/code-route/` ; `validate-app.sh code-route --quality-only` vert ; cloisonnement `ok` par le moteur
**Vérifié le :**
