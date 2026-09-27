# Sources, réutilisations et contributions

## Socle retenu : Atlas

Cette version réutilise directement [KpihX/atlas](https://github.com/KpihX/atlas), branche `kpihx-ubuntu`, commit [`4e0823f8f4350978d94a69d3e16fa06c2b3584fa`](https://github.com/KpihX/atlas/tree/4e0823f8f4350978d94a69d3e16fa06c2b3584fa), consulté le 27 septembre 2026. Il s’agit d’une reprise de code et d’interface, pas seulement d’une inspiration.

Éléments repris et adaptés : moteur d’agents, routage catégoriel, notes structurées, consolidation du tableau, prompts, client LLM par rôles, adaptateurs de services, contrat WebSocket vocal, capture/lecture audio progressive, composants de tableau/notes/agents/sous-titres, identité visuelle sombre, SVG Atlas et favicon.

Le chemin `src/aparte/workspace` résulte d’une adaptation des imports. Le moteur unique est `WorkspaceEngine(AtlasEngine)` ; les fichiers du clone de référence ne sont jamais importés directement. Les attributions s’appliquent aussi aux tests repris d’Atlas et adaptés à ce dépôt.

Aucun fichier de licence explicite n’a été trouvé dans ce commit du dépôt Atlas. L’utilisateur a indiqué que les auteurs collaborent et a autorisé la réutilisation dans leur projet commun. Cette déclaration n’équivaut pas à une licence générale de redistribution. Conserver l’accord de l’équipe et clarifier les droits lors d’une diffusion hors de ce cadre ; ne pas attribuer une licence fictive au code amont.

La synchronisation du 27 septembre reprend également les registres vocaux,
les adaptateurs OpenAI, les ajustements de routage, de notes, de tableau, de
sous-titres et d’interruption de ce commit. Le diagnostic `check_openai_voice.py`
est adapté du script amont `backend/scripts/openai-voice-smoke.py`.
Ces éléments sont des contributions d’Atlas, conservées avec leur attribution.

La comparaison détaillée des apports locaux est dans
[CONTRIBUTIONS-APARTE.md](docs/CONTRIBUTIONS-APARTE.md).

## Contributions intégrées depuis Aparté

- Recherche web sourcée, contexte de recherche, météo Open-Meteo, connecteur Dust et workflow Pipelex.
- Extraction de propositions avec contrôle des citations exactes, relecture humaine, responsables/échéances, invalidation après nouveaux échanges et export iCalendar.
- Journal SQLite, sauvegarde transactionnelle et compatibilité des sessions existantes.
- Consentement explicite, accès local, arrêt des travaux à la pause, ouverture des sessions sans reprise automatique du microphone.
- Nouveau parcours d’accueil en français, réglages secondaires regroupés, adaptation du graphe aux petits écrans, restructuration du frontend, sources consultables et tests de parcours.
- Filtre conservateur des retours de voix, historique distinguant réponses annulées/interrompues/écrites, préservation des preuves dans le contexte vocal et relecture du contexte après correction humaine.
- Adaptation des anciennes configurations vocales et durcissement des replis STT/TTS, des délais de connexion et de l’alignement PCM.
- Correctifs sur la troncature de transcription, les titres manuels, les permissions audio tardives et les réponses écrites en mode silencieux.
- Guide des deux sens audio pour l’appel et signal de contrôle Web Audio ; les réglages de partage renvoient aux documentations officielles des plateformes, sans prétendre fournir un connecteur de réunion automatique.
- Reconnexion progressive avec reprise en pause, annulation ciblée et délai des missions, correction du réemploi des résultats, rattachement à la demande d’origine et références sous les réponses. Les documentations Google Meet, Microsoft Teams et LiveKit consultées pour l’analyse sont citées dans [les améliorations de fiabilité](docs/ameliorations-fiabilite.md) ; aucun code de ces produits n’a été incorporé.

Les résumés de réunions, agents spécialisés, citations et relectures humaines sont des concepts existants. L’équipe présente sa réalisation commune et ses améliorations ; elle ne revendique pas l’invention de ces concepts.

## Auteurs et assistance

Les auteurs déclarés dans `pyproject.toml` sont conservés : KAMDEM POUOKAM Ivann Harold, Dehayem Kenfouo Sylvain et Wadoh Tchinda Pavel. Conserver également l’historique et l’identité des contributeurs du dépôt Atlas ; cette liste locale ne remplace pas la liste des contributeurs amont.

La réalisation a bénéficié de l’assistance d’un agent de génération de code. Pour le hackathon, distinguer le travail préexistant, les apports réalisés pendant la compétition et les vérifications effectuées. Citer une source rend la réutilisation transparente, sans garantir à elle seule l’éligibilité au règlement ou les droits sur tous les contenus.

## Références historiques

La version précédente utilisait [Meeting Sidecar](https://github.com/KpihX/meeting-sidecar), commit `f083b7d7b3b70f390cebd21bc622fc7a537151fa`. Cette référence est conservée pour la traçabilité ; le socle courant est Atlas.

Le registre de recherche antérieur cite [Salesforce VoiceAgentRAG](https://github.com/SalesforceAIResearch/VoiceAgentRAG), [thoughtful-agents](https://github.com/xybruceliu/thoughtful-agents) et [Speaking Meeting Bot](https://github.com/Meeting-Baas/speaking-meeting-bot) pour la séparation réponse/recherche et le tour de parole. Aucun nouveau fichier de ces trois dépôts n’a été incorporé lors de cette reprise. Les sources du travail produit antérieur restent dans [la recherche sur les besoins](docs/recherche-besoins-reunions.md).

## Dépendances et services

Les versions sont fixées dans `uv.lock` et `frontend/bun.lock`. Conserver les licences et notices fournies par les distributions, y compris leurs dépendances transitives. Les principales bibliothèques sont FastAPI, Pydantic, httpx, uvicorn, websockets, aiosqlite, PyYAML, python-dotenv, pipelex-sdk, React, Lucide React, react-markdown et remark-gfm. Vite, TypeScript, Vitest, Testing Library, jsdom, Prettier, pytest, Ruff et Playwright servent au développement ou aux tests.

Services utilisés selon configuration : OpenAI, Gradium, TypeSafe/Jev, Exa, Jinko, Dust, Pipelex et Open-Meteo. Leurs marques servent à les identifier, sans prétendre à un soutien ou une recommandation de leur part. L’export iCalendar suit la [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545). Les icônes d’interface viennent de Lucide ; les SVG de marque viennent du dépôt Atlas indiqué ci-dessus.

Les données fictives des tests restent isolées. Aucun témoignage web, texte de réunion tiers ou capture d’écran d’un concurrent n’a été intégré comme contenu de démonstration dans le produit.
