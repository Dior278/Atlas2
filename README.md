# Atlas2

Un assistant de réunion qui prend des notes, effectue des recherches sourcées et transforme les échanges en actions à valider.

## Démarrer

Prérequis : [uv](https://docs.astral.sh/uv/getting-started/installation/), [Bun](https://bun.sh/docs/installation) et [Node.js 24](https://nodejs.org/en/download). uv installe Python si nécessaire.

```sh
git clone https://github.com/Dior278/Atlas2.git
cd Atlas2
uv run --locked python scripts/project.py setup
```

Dans le fichier `.env` créé, renseigner `OPENAI_API_KEY`. Ajouter `GRADIUM_API_KEY` pour la voix. Les autres intégrations sont facultatives : voir [.env.example](.env.example).

```sh
uv run --locked aparte
```

Ouvrir **http://127.0.0.1:8765/**, choisir Texte ou Microphone et démarrer après accord des participants.

Pendant la réunion : consulter les notes, demander une recherche à Atlas, puis relire et confirmer les engagements. Les sessions sont sauvegardées localement ; les exports Markdown et calendrier restent disponibles.

Pour faire entendre Atlas dans un appel, suivre le [guide audio](docs/demo-video.md).

## Vérifier

```sh
uv run --locked python scripts/project.py doctor
uv run --locked python scripts/project.py check
```

`doctor` vérifie la configuration ; `check` lance les tests et la compilation sans clé API. L’utilisation réelle de l’IA nécessite des crédits chez les fournisseurs configurés.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Contribuer](CONTRACT.md)
- [Évaluer le projet](docs/EVALUATION.md)
- [Sources et auteurs](ATTRIBUTIONS.md)
