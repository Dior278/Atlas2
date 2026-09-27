# Fiabilité

| Situation | Comportement |
| --- | --- |
| Connexion interrompue | Reconnexion automatique, brouillon conservé et session en pause jusqu’à confirmation |
| Recherche devenue inutile | Annulation depuis **Agents → Recherches**, avec arrêt des restitutions associées |
| Recherche trop longue | Délai de 120 secondes par défaut, réglable avec `policy.mission_timeout_seconds` |
| Outil en échec | État d’erreur visible ; une mission ne réussit pas sans résultat |
| Résultat déjà disponible | Réemploi signalé avec conservation des sources ; sa fraîcheur n’est pas revérifiée |
| Réponse issue d’une recherche | Demande d’origine et liens consultables dans **Origine de cette réponse** |
| Voix interrompue | Distinction entre réponse lue, interrompue et écrite ; filtrage des répétitions récentes |

Les paroles échangées pendant une coupure ne sont pas reconstituées. Une citation facilite la vérification sans garantir l’interprétation du modèle. L’annulation peut survenir après la facturation d’un appel fournisseur.

Les tests couvrent les pannes, délais, annulations, sources, reconnexions et parcours aux largeurs 320, 390, 768 et 1440 px. Voir [les commandes de vérification](EVALUATION.md) et le [test audio en appel](demo-video.md).
