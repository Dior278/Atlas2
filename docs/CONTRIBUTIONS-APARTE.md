# Apports d’Aparté à Atlas — comparaison à partager

Comparaison réalisée le 27 septembre 2026 avec la branche `kpihx-ubuntu` au commit
[`4e0823f8f4350978d94a69d3e16fa06c2b3584fa`](https://github.com/KpihX/atlas/tree/4e0823f8f4350978d94a69d3e16fa06c2b3584fa).
Elle porte sur le code publié à cette référence, pas sur d’éventuels travaux non
publiés du collègue. Les fonctionnalités ci-dessous forment une seule application.

## Déjà présents dans Atlas : les attribuer au socle commun

- Moteur d’agents : Speaker, Worker, Notes, Board, Naming et routage sémantique TypeSafe/Jev.
- Mémoire structurée, synthèse, sujets, idées, décisions, engagements textuels et consolidation des cartes.
- Bibliothèque SQLite : créer, reprendre en pause, renommer, supprimer et exporter une session en Markdown.
- Recherche Exa, outils de voyage Jinko et registre d’outils.
- Capture micro/audio partagé, voix Gradium progressive, sous-titres et interruption par la parole.
- Interface Atlas, identité visuelle, graphe des agents et inspecteurs.
- Nouveautés de `4e0823f` : registres vocaux Gradium/OpenAI, adaptateurs OpenAI,
  repli de fournisseur, seuils d’interruption ajustés, sous-titres longs, meilleurs
  critères de routage, nettoyage des participants et cartes peu utiles, maintien
  des résultats demandés malgré les tours de conversation suivants.

La création de ces éléments n’est donc pas un apport spécifique d’Aparté.

## Apports locaux distincts conservés

| Apport | Différence concrète avec Atlas 4e0823f | Fichiers principaux |
|---|---|---|
| Engagements avec preuves et relecture | Une rubrique dédiée extrait décisions/actions/questions/risques, contrôle les citations exactes, permet confirmation ou rejet, responsable et échéance. Atlas conserve déjà des engagements dans ses notes, mais ne fournit pas ce circuit de validation. | `src/aparte/minutes.py`, `workspace/runtime.py`, `frontend/src/components/MinutesView.tsx` |
| Protection contre les engagements périmés | Un nouvel échange invalide la version précédente ; les relectures obsolètes et exports calendrier non valides sont bloqués. | `minutes.py`, `workspace/runtime.py` |
| Export calendrier | Fichiers `.ics` pour les actions confirmées, attribuées et datées ; aucune invitation distante n’est envoyée. L’export Markdown des sessions existait déjà. | `minutes.py` |
| Fournisseurs supplémentaires | Recherche web OpenAI avec preuves et synthèse séparées, météo Open-Meteo, recherche interne Dust, comparaison Pipelex ; Exa/Jinko restent ceux d’Atlas. | `providers.py`, `weather.py`, `pipelex_workflow.py`, `workspace/integrations.py` |
| Journal de session | Snapshot et événements sauvegardés dans une transaction SQLite, WAL, unicité des événements et suppression liée à la session. Atlas possède déjà SQLite ; l’apport est le journal et ces garanties, pas la persistance elle-même. | `workspace/adapters/sqlite.py` |
| Consentement et contrôle local | Accord explicite avant analyse et reprise, vérification des origines et accès API local, arrêt des tâches et de l’analyse pendant la pause. Atlas ouvrait déjà les sessions en pause. | `workspace/api/`, `workspace/runtime.py` |
| Compatibilité et corrections de mémoire | Conservation des sessions Aparté, migration en mémoire, transcription au-delà de 500 interventions, titre manuel protégé contre une réponse automatique tardive. Le journal n’est pas un moteur complet de reconstruction historique. | `workspace/core/models.py`, `workspace/core/engine.py`, `workspace/config.py` |
| Parcours et petits écrans | Accueil français, réglages secondaires regroupés, changements de vue au clic, graphe remplacé par des cartes sur mobile, contrôle des permissions audio tardives. L’identité et les vues fondamentales restent celles d’Atlas. | `frontend/src/components/`, `frontend/src/audio.ts`, `frontend/src/responsive.css` |

La présence d’un connecteur ne signifie pas qu’il a été vérifié avec un vrai compte
pour toutes ses opérations. Dust, Pipelex et Jinko restent à valider dans leur
configuration réelle avant de les mettre au centre d’une démonstration.

## Correctifs locaux ajoutés pendant cette synchronisation

| Problème | Correction locale | Vérification |
|---|---|---|
| La voix d’Atlas revient dans la transcription et relance le dialogue | Filtre textuel conservateur des réponses récemment jouées, avant routage et mémoire ; exclusion demandée de l’onglet courant lors du partage audio | Régressions écho/corrections/citations/saisie manuelle ; le matériel réel reste à essayer |
| Brouillons annulés affichés comme des paroles prononcées | Historique filtré, libellé pour les interruptions et les réponses écrites ; horodatage de début de lecture | Tests des états de réponse et parcours navigateur |
| Réponses de recherche trop générales | La projection vers la voix conserve le résumé vérifié, les URL et extraits ; les brouillons annulés ne comptent plus comme des réponses entendues | Tests de projection et essai réel de recherche |
| Correction humaine arrivant pendant la préparation d’un résultat | Nouvelle lecture du contexte une fois ; si la conversation change encore, pas de restitution orale de ce brouillon | Test de correction concurrente |
| Réglages vocaux anciens incompatibles | Migration en mémoire du fournisseur unique vers le registre, sans écraser le fichier ni ajouter automatiquement un fournisseur | Test de configuration historique |
| Replis vocaux incomplets | Autre fournisseur STT privilégié après échec, connexion bornée, conservation du texte lors de plusieurs replis TTS, erreurs expurgées | Tests de panne et de repli |
| Fragments PCM OpenAI coupés entre deux octets | Réassemblage des échantillons de 16 bits ; détection d’un échantillon tronqué | Tests de transport audio fragmenté |
| Les participants n’entendent pas la voix locale d’Atlas | Guide replié pour les deux sens audio, liens vers les réglages de réunion et signal de test sans API, accessible avant et pendant la session | Capture réelle du signal entre deux onglets Chromium ; réception dans l’appel à confirmer par un participant |

Le guide de partage audio utilise les capacités de la plateforme de réunion.
Ce n’est pas un connecteur automatique ni un bot qui rejoint l’appel.

Le filtre d’écho ne reconnaît pas les personnes et ne remplace pas l’annulation
d’écho acoustique. Il peut laisser passer une paraphrase ou être ambigu lorsqu’un
humain répète exactement une phrase d’Atlas juste après sa lecture.

## Formulation courte pour le collègue

Depuis la synchronisation, trois apports supplémentaires ont été réalisés :
reconnexion automatique avec reprise en pause et conservation du brouillon,
recherches annulables avec délai limite et erreurs explicites, et références
consultables sous les réponses d’Atlas. Les missions restent liées à leur demande
d’origine ; le réemploi des résultats et leur durée sont affichés. Voir
[les changements et leur validation](ameliorations-fiabilite.md).

> J’ai repris le socle Atlas et sa dernière mise à jour vocale. Mes apports locaux
> portent surtout sur les engagements vérifiables avec relecture et export calendrier,
> les connecteurs OpenAI Web/Dust/Pipelex/Open-Meteo, le journal SQLite, le consentement
> et les contrôles d’accès locaux, ainsi que le parcours français sur petits écrans.
> J’ai aussi ajouté des correctifs contre les retours de voix, les réponses annulées
> affichées comme prononcées et la perte de preuves dans les réponses de recherche.
> La version suivante ajoute la reconnexion contrôlée, l’annulation ciblée des
> recherches, leur délai maximal et l’origine consultable des réponses.
> Le moteur d’agents, les notes structurées, Exa/Jinko, l’identité Atlas et les
> nouveaux registres vocaux viennent du projet Atlas commun.

Les auteurs restent crédités dans [ATTRIBUTIONS.md](../ATTRIBUTIONS.md). Les tests
et le code ont été élaborés avec assistance IA. Cette comparaison établit la
provenance du code ; elle ne prétend pas que ces concepts sont des inventions nouvelles.
