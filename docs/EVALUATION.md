# Évaluer et remettre Atlas

## Pour le jury

Le [README](../README.md) contient les prérequis et les trois commandes de prise
en main : installation, configuration de la clé OpenAI, démarrage. Le dépôt et
l’archive utilisent le même parcours ; aucune clé de l’équipe n’est distribuée.
L’installation attend un environnement de développement avec accès Internet.

En cinq minutes après installation, le scénario **Premier essai** du README
permet d’observer la synthèse, une recherche avec ses sources, une proposition
d’engagement relue et la persistance après fermeture. La génération des notes et
les réponses dépendent du temps de traitement des fournisseurs.

Sans clé API, utiliser les tests automatiques et le parcours navigateur : ils
injectent des fournisseurs fictifs dans un serveur de test distinct. Ils vérifient
le fonctionnement du logiciel, sans démontrer la qualité des modèles réels.

## Dépannage

| Symptôme | Action |
| --- | --- |
| `uv`, `bun` ou `node` introuvable | Installer les prérequis du README, rouvrir le terminal et vérifier `--version`. |
| Page inaccessible | Garder `uv run --locked aparte` actif et ouvrir le port annoncé. |
| Interface absente ou ancienne | Exécuter `bun run --cwd frontend build`, puis redémarrer le serveur. |
| Port 8765 déjà occupé | Arrêter l’ancien processus ou utiliser `uv run --locked aparte --port 8766`. |
| Configuration invalide | Lancer `doctor`, comparer `.env` à `.env.example` et le JSON au schéma fourni. Ne pas envoyer les clés dans un rapport d’erreur. |
| IA indisponible | Vérifier la présence de `OPENAI_API_KEY`, les crédits et l’accès aux modèles. `doctor` ne valide pas les clés à distance. |
| Aucun microphone/audio partagé | Autoriser la capture dans un navigateur compatible sur localhost ; utiliser Texte pour tester le reste. |
| Atlas audible seulement sur son poste | Partager son onglet avec audio depuis l’appel et faire confirmer le signal de test par un participant. Voir [le guide audio](demo-video.md). |
| Tests navigateur impossibles | Installer Chromium via le groupe `browser` ; sur Linux ajouter `--with-deps`. Libérer le port 8878. |

## Vérifications et intégration continue

`uv run --locked python scripts/project.py check` exécute les contrôles du dépôt.
Le workflow [Quality](../.github/workflows/quality.yml) reprend ces contrôles et
le parcours Chromium sur Linux à chaque push et pull request, sans secret API.
Les versions des outils et les références des actions sont figées. Ce fichier
ne prouve pas qu’une exécution GitHub distante a déjà réussi.

Le navigateur teste les largeurs 320, 390, 768 et 1440 px, le consentement, les
engagements, les exports, l’annulation d’une recherche et la reconnexion en pause.
Les diagnostics `check_workspace_live.py`, `check_workspace_voice.py`,
`check_openai_voice.py`, `check_minutes_live.py` et `check_dust.py` sont facultatifs,
utilisent de vrais fournisseurs et peuvent consommer des crédits. Ils ne font
pas partie de `check` ni de la CI. Ils emploient des données fictives.

## Préparer la remise

```sh
uv run --locked python scripts/project.py check
uv run --locked --group browser python scripts/check_atlas_browser.py
uv run --locked python scripts/release.py
```

Le dernier appel crée `release/atlas-source.zip`, son empreinte `.sha256` et un
manifeste SHA-256 des fichiers à l’intérieur de l’archive. Le script refuse
d’écraser une archive existante : utiliser `--output release/atlas-source-v2.zip`
pour une nouvelle révision.

L’archive contient uniquement les sources, tests, configurations exemples,
verrous de dépendances et documentation. `.env`, `.Secrets`, `.data`, `.git`,
`tmp`, dépendances installées, builds et caches restent hors de la remise.
Les liens symboliques dans les sources et fichiers inattendus sont refusés.
Un contrôle cherche les clés locales connues et certaines signatures de secrets ;
il ne constitue pas un audit de sécurité exhaustif.

Le règlement fourni à l’équipe demande un **lien de dépôt avec les instructions
de test**, une description courte, les noms des membres et une vidéo de deux
minutes maximum. L’archive est une copie propre du code, pas un remplacement du
lien GitHub demandé. Aucun envoi ni publication n’est effectué par ces scripts.
Les auteurs sont conservés dans `pyproject.toml` et les attributions.

Déclarer le socle Atlas, son commit intégré, les ajouts locaux et les parties
préexistantes. [CONTRIBUTIONS-APARTE.md](CONTRIBUTIONS-APARTE.md) décrit les
différences de code ; ce document ne certifie pas leur date de réalisation.
[ATTRIBUTIONS.md](../ATTRIBUTIONS.md) précise aussi l’assistance IA et l’absence
de licence explicite trouvée dans le socle amont. Aucune licence de tiers n’a été
inventée pour cette remise.

## Nettoyage de cette version

Les anciens rapports de refonte, de synchronisation et de nettoyage ainsi que
le guide de démonstration redondant ont quitté le dépôt livrable. Le texte brut
du règlement fourni est conservé avec ces documents dans la sauvegarde locale
`tmp/backups/before-evaluation-handoff.zip`. Le guide présent, le guide vidéo et
les attributions gardent les informations nécessaires à l’évaluation.

Les exécutables portables et sauvegardes restent locaux pour préserver le poste
de travail. Les caches ne sont pas des sources et ne sont jamais remis au jury.

## Références techniques

La procédure suit les documentations officielles de
[uv pour GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/),
de [Bun pour les installations verrouillées](https://bun.sh/docs/pm/cli/install)
et de [Playwright en CI](https://playwright.dev/python/docs/ci).
