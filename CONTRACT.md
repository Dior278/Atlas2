# Contrat de développement — Atlas2

Atlas accompagne une réunion depuis une seule application : capture audio ou saisie
texte, recherches, notes et engagements. Le dépôt et le package Python restent
nommés Aparté.
Projet du hackathon X-IA, Rise of Agents X.

## Développement

- Python 3.12 ou supérieur ; package `src/aparte`, commande `uv run aparte`.
- Dépendances gérées par `uv` et `uv.lock` ; pas de `pip` global.
- Contrôles : `uv run --locked python scripts/project.py check`. Tests seuls : `uv run pytest -p no:cacheprovider`. Style : `uv run ruff check src tests scripts` et
  `uv run ruff format --check src tests scripts`.
- Conserver les auteurs dans les métadonnées et documenter les inspirations.

## Architecture

- Un frontend React, une API FastAPI et un moteur `WorkspaceEngine` issu d’Atlas.
- Séparer transport, orchestration, recherche, fournisseurs et persistance.
- Le routage TypeSafe (avec repli sur le modèle configuré) oriente les
  interventions ; réponse et recherches peuvent travailler en parallèle.
- Vérifier la pertinence avant de parler ; respecter le tour humain,
  les interruptions et l'obsolescence des résultats.
- OpenAI : conversation, planification et recherche web ; Gradium : écoute et voix.
- Dust : recherche documentaire interne ; Pipelex : comparaison structurée.
- Les outils restent choisis selon le besoin, sans appel artificiel à un fournisseur.
- Les échecs d'API restent visibles ; aucun résultat simulé ne remplace une erreur
  dans une session réelle. Les données fictives sont réservées aux tests isolés.
- Les connecteurs Google Meet, Teams et Zoom ne sont pas encore implémentés.

## Données locales

- `.env` et `.Secrets` sont locaux, ignorés par Git et chargés par `AppSettings`.
- Seul `.env.example`, sans identifiants réels, est destiné à être versionné.
- Ne jamais exposer les clés au navigateur ou dans les journaux.
- Les transcriptions nécessaires sont transmises aux fournisseurs utilisés ;
  aucune vidéo n'est envoyée aux modèles. La transcription, les notes et les
  actions sont enregistrées dans SQLite ; aucun audio brut n'y est conservé.
- Contrôle avant publication : `uv run python scripts/check_secret_hygiene.py`.

Voir [l'architecture](ARCHITECTURE.md), les [limites de validation](docs/ameliorations-fiabilite.md)
et le [dossier hackathon](docs/EVALUATION.md).
