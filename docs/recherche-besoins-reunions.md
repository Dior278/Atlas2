# Recherche produit : ce qui manque aux assistants de réunion

Consultation web le **26 septembre 2026** ; correspondances produit actualisées pour Atlas le 27 septembre. Recherche exploratoire, sans enquête représentative ni classement comparatif des fournisseurs. Les témoignages publics signalent des pistes ; les documents primaires ci-dessous étayent les exigences. Aucun taux global d’erreur ou gain de productivité n’est déduit de ces pages.

| Problème observé | Source et portée | Réponse intégrée dans Atlas | Limite restante |
|---|---|---|---|
| Un récapitulatif plausible peut être erroné | [Microsoft, Recap a Teams meeting](https://support.microsoft.com/en-gb/teams/meetings-events/recap-a-teams-meeting) demande de vérifier les résultats produits par IA | Références identifiées, vérification des extraits, contexte intégral consultable, validation explicite | Une citation exacte ne prouve pas la bonne interprétation |
| Prise de notes sans accord clair ; autocensure et informations sensibles | [Harvard, AI Assistant Guidelines](https://www.huit.harvard.edu/ai-assistant-guidelines) décrit les enjeux de consentement, confidentialité et liberté de participation | Attestation d’information et d’accord avant analyse ; pause et arrêt de la capture ; appel externe indépendant | Pas d’identité vérifiée, pas de retrait rétroactif chez les fournisseurs |
| Actions attribuées trop vite ou engagements ambigus | [Témoignages de managers](https://www.reddit.com/r/managers/comments/1n2f8m2/do_people_actually_use_ai_in_their_meetings/) : besoin de relire les actions et de retrouver les passages sources ; témoignages anecdotiques | Proposition distincte de validation, responsable choisi, échéance relative laissée à confirmer | La classification action/suggestion reste une tâche de modèle et de relecture |
| Les retardataires perdent le contexte et les points ouverts | [Microsoft, récapituler une réunion](https://support.microsoft.com/en-gb/teams/meetings-events/recap-a-teams-meeting) présente les questions sur ce qui a été manqué | Notes et carnet relisibles par l’opérateur, décisions/actions/questions/risques et passages sources | Actualisation à la demande ; pas de mémoire inter-réunions |
| La discussion change après la synthèse | Exigence de conception déduite de l’exigence de vérification, et des corrections déjà gérées dans Aparté | Révision du carnet, marquage périmé et refus serveur de validation/export après de nouveaux propos | Invalidation conservatrice de tout le carnet ; les validations sont à refaire |
| Les notes restent un document sans suite | [Microsoft, Recap in Teams](https://support.microsoft.com/en-us/teams/meetings/recap-in-microsoft-teams) décrit résumés et tâches de suivi, capacité déjà existante ailleurs | Export portable Markdown et rappels iCalendar pour actions validées, datées et attribuées | Téléchargement manuel ; pas de synchronisation avec des comptes externes |
| Manque de visibilité sur ce qui est conservé | [Harvard, AI Assistant Guidelines](https://www.huit.harvard.edu/ai-assistant-guidelines) et [Law Society of Alberta, Managing AI in Meetings](https://www.lawsociety.ab.ca/resource-centre/key-resources/practice-management/managing-ai-in-meetings/) | Informations sur les flux fournisseurs, la mémoire locale persistante et la capture audio | Les fournisseurs appliquent leurs propres conditions de traitement |

La documentation [Zoom sur les résumés IA](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0057960) décrit déjà des réglages d’activation et de partage. Nous ne prétendons pas que les concurrents n’ont aucun contrôle, aucune source ou aucune tâche. Le choix produit est d’en faire un parcours cohérent et explicite dans notre prototype.

## Ce que le jury peut vérifier

Dans Atlas, l’opérateur atteste l’accord des personnes puis démarre une session. Renard annonce une action « vendredi ». L’opérateur prépare les propositions, consulte les paroles, confirme une date et valide. Un rappel agenda se télécharge. Une nouvelle correction bloque l’export de l’ancien carnet ; la pause interrompt la capture et l’analyse.

Le point distinctif à défendre est cette continuité : **écouter avec accord, contribuer avec des sources, puis rendre les engagements vérifiables et révisables**. Ce positionnement est une proposition de valeur à tester auprès des équipes ; il ne constitue pas une preuve de supériorité commerciale ou une promesse de victoire au concours.

## Choix de périmètre

Les demandes d’invitations automatiques, de CRM, de synchronisation de calendriers, de reconnaissance d’émotions et de connexion à chaque plateforme élargiraient fortement le périmètre. Cette itération livre un parcours complet autour des preuves et engagements en utilisant les fournisseurs déjà intégrés. Le format agenda suit la [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545) ; aucune donnée n’est envoyée à Google Calendar ou Outlook par ce bouton.

Les instructions d’extraction sont propres au projet. La documentation [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) a été utilisée pour le contrat de sortie, et non comme garantie de justesse sémantique. Les attributions de l’ensemble du projet se trouvent dans [ATTRIBUTIONS.md](../ATTRIBUTIONS.md).
