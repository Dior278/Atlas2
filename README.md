# Atlas2 — un coéquipier pour les réunions

Atlas2 écoute une conversation autorisée, organise les notes, recherche des informations et propose des engagements à relire avec leurs citations. Une application React, une API FastAPI et un moteur d’agents ; les sessions sont conservées localement dans SQLite.

Dépôt : [Dior278/Atlas2](https://github.com/Dior278/Atlas2). L’application est nommée **Atlas2** ; son compagnon vocal conserve le nom **Atlas**. Le package Python et la commande restent nommés `aparte` pour préserver la compatibilité. Le socle vient de [KpihX/atlas](https://github.com/KpihX/atlas), commit `4e0823f8f4350978d94a69d3e16fa06c2b3584fa`. Les [contributions locales](docs/CONTRIBUTIONS-APARTE.md) et les [attributions](ATTRIBUTIONS.md) distinguent le code repris et les ajouts.

## Installation et démarrage

Installer [uv](https://docs.astral.sh/uv/getting-started/installation/), [Bun](https://bun.sh/docs/installation) et [Node.js](https://nodejs.org/en/download). Versions utilisées pour la validation : **uv 0.12.19, Bun 1.4.2, Node 24.21.0, Python 3.12**. uv peut installer Python automatiquement ; Node est utilisé par les tests frontend. Une connexion Internet est nécessaire à la première installation.

Cloner le projet, sous Windows, macOS ou Linux :

```sh
git clone https://github.com/Dior278/Atlas2.git
cd Atlas2
```

Depuis ce dossier :

```sh
uv run --locked python scripts/project.py setup
```

Cette commande installe les dépendances verrouillées, compile l’interface et crée `.env` depuis `.env.example` si aucun fichier de clés n’existe. Elle préserve une configuration existante.

Renseigner **`OPENAI_API_KEY` dans `.env`** pour la conversation, les notes et la recherche. Ajouter `GRADIUM_API_KEY` pour le parcours vocal principal. Les intégrations Dust, Pipelex, Exa, Jinko et TypeSafe sont facultatives ; voir [.env.example](.env.example). Les appels aux fournisseurs nécessitent un accès API valide et consomment des crédits.

```sh
uv run --locked aparte
```

Ouvrir **http://127.0.0.1:8765/**. Garder le terminal ouvert ; `Ctrl+C` arrête le serveur. Sans clé IA, l’interface et la bibliothèque sont accessibles, mais aucune réponse IA n’est simulée. Le mode Texte avec une clé OpenAI suffit pour évaluer le parcours principal.

## Premier essai

1. Choisir **Texte**, attester l’accord des personnes concernées, puis démarrer.
2. Saisir : « Je préparerai le prototype pour la démonstration. Nous retenons une interface en français. » Consulter les **Notes** après leur actualisation.
3. Demander : « Atlas, recherche la documentation officielle de WebRTC et conserve la source. » Suivre la recherche dans **Agents** et ouvrir **Origine de cette réponse** dans la Conversation.
4. Dans **Engagements**, préparer les propositions, vérifier les citations, attribuer une action à Renard, choisir une date et confirmer. Télécharger le rappel calendrier.
5. Mettre en pause, terminer et rouvrir la session : les données restent disponibles et la capture reste arrêtée.

Pour un appel en ligne, il faut transmettre le son **dans les deux sens** : Atlas capture l’onglet de réunion ; la réunion partage l’onglet Atlas avec son audio. Le menu **••• → Faire entendre Atlas dans l’appel** propose un guide et un signal de test. Voir le [guide vidéo et audio](docs/demo-video.md).

## Vérifier et contribuer

```sh
uv run --locked python scripts/project.py doctor
uv run --locked python scripts/project.py check
```

`doctor` vérifie les outils, la configuration et l’interface compilée, sans afficher les clés ni appeler les fournisseurs. `check` exécute les tests Python et React, Ruff, Prettier, TypeScript, le build, le contrôle des sources et la cohérence du protocole généré. Il ne consomme pas de crédits API.

Pour le parcours Chromium, également sans API :

```sh
uv run --locked --group browser playwright install chromium
uv run --locked --group browser python scripts/check_atlas_browser.py
```

Sous Linux, utiliser `playwright install --with-deps chromium` si les bibliothèques système manquent. Le test utilise le port **8878**, des fournisseurs fictifs et une base isolée. Le test audio réel `--tab-audio` est facultatif et nécessite un navigateur visible et un environnement compatible.

En développement : lancer le backend comme ci-dessus, puis `bun run --cwd frontend dev` dans un second terminal et ouvrir http://127.0.0.1:5173/. Le frontend de développement relaie `/v1` vers le backend local.

## Repères pour l’évaluation

| Document | Contenu |
| --- | --- |
| [Guide d’évaluation](docs/EVALUATION.md) | Scénario, dépannage, préparation de la remise |
| [Architecture](ARCHITECTURE.md) | Modules, échanges, orchestration et mémoire |
| [Contributions](docs/CONTRIBUTIONS-APARTE.md) | Ajouts par rapport au commit Atlas intégré |
| [Attributions](ATTRIBUTIONS.md) | Auteurs, sources, réutilisation et assistance IA |
| [Fiabilité](docs/ameliorations-fiabilite.md) | Reconnexion, recherches, sources et limites des mesures |
| [Contrat de développement](CONTRACT.md) | Conventions à préserver lors des modifications |

## Données et limites

La base `.data/aparte.sqlite3` conserve les transcriptions, notes, cartes, résultats et engagements. Aucun audio brut n’y est enregistré. `APARTE_DATABASE_PATH` permet de choisir un autre emplacement. La configuration facultative `.data/config.json` suit [le schéma fourni](src/aparte/workspace/default_config.json) ; `APARTE_CONFIG_FILE` et `ATLAS_CONFIG` permettent de choisir un fichier. Les clés restent dans l’environnement, `.env` ou `.Secrets`, jamais dans la configuration JSON.

Les contextes nécessaires sont transmis aux fournisseurs activés. La base locale n’est pas chiffrée par l’application ; l’exclusion Git n’empêche pas la synchronisation par un logiciel de sauvegarde. Arrêter le serveur avant une copie manuelle de la base, ou utiliser l’API de sauvegarde SQLite.

Le prototype gère **une session active et un onglet de contrôle par serveur**, sans comptes d’entreprise ni bot natif Meet/Teams/Zoom. Les locuteurs externes ne sont pas identifiés automatiquement. Les citations exactes et les liens facilitent la relecture, sans garantir la justesse d’une interprétation. La capture audio dépend du navigateur et du système ; une répétition dans l’appel réel reste nécessaire.
