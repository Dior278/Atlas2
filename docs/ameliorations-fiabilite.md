# Atlas : recherches contrôlables, réponses traçables et reprise après coupure

Contributions locales du 27 septembre 2026, après l’intégration du commit Atlas
`4e0823f`. Elles complètent le même moteur et les vues existantes.

## Besoins et sources consultées

Google indique que des problèmes de connexion peuvent contribuer à des notes
incomplètes ou absentes dans Meet. Cette observation motive la reprise de connexion
avec un état explicite, sans prétendre reconstruire les paroles non capturées.
[Aide officielle Google Meet](https://support.google.com/meet/answer/14754931?co=GENIE.Platform%3DDesktop&hl=en-CA).

Microsoft documente la dépendance des réponses à la transcription disponible et
des limites de latence sur les longues réunions. Rendre la demande d’origine et
les références consultables aide l’utilisateur à contrôler une restitution.
[FAQ officielle Copilot dans Teams](https://support.microsoft.com/en-us/teams/platform/frequently-asked-questions-about-copilot-in-microsoft-teams).

LiveKit distingue les étapes de latence et recommande de mesurer plutôt que de
juger uniquement à l’impression. Atlas affiche ici la durée d’une recherche ;
cette mesure n’est pas la latence de réponse vocale.
[Données et métriques LiveKit](https://docs.livekit.io/testing/observability/data/).
Les interruptions adaptatives restent une piste de travail, pas une capacité
ajoutée dans cette livraison : [réglage des tours de parole](https://docs.livekit.io/agents/logic/turns/tuning/).

Ces références ont servi à l’analyse des besoins. Aucun SDK, modèle ou fichier
de ces produits n’a été incorporé dans cette livraison. Les concepts de reprise,
d’annulation et de citations ne sont pas revendiqués comme des inventions.

## Changements utilisables

### Reconnexion et reprise contrôlée

Une fermeture WebSocket ordinaire déclenche une nouvelle connexion après 0,5 s,
puis 1, 2, 4, 8 et au plus 10 s entre les essais suivants. L’authentification locale
est renouvelée par le bootstrap. Un refus de connexion ne déclenche pas de boucle
automatique ; le bouton de nouvelle tentative reste disponible.

La coupure arrête capture, lecture et sous-titres. La vue et le brouillon non envoyé
restent en mémoire dans l’onglet. La session revient en pause et exige un accord
explicite avant reprise. Les données déjà sauvegardées restent consultables ;
l’audio de la coupure n’est ni conservé ni reconstitué, et les commandes ne sont pas
rejouées automatiquement. Le serveur sérialise la libération de l’ancien client
et l’admission du nouveau. L’identifiant de l’onglet reste stable pendant les essais :
il peut remplacer son ancienne connexion devenue injoignable, tandis qu’un autre
onglet reste refusé. La fermeture tardive de l’ancienne connexion ne peut pas mettre
la nouvelle en pause.

### Recherches annulables et bornées

Dans **Agents → Recherches**, le bouton **Arrêter cette recherche** interrompt une
mission en attente ou en cours. Les notes, la session et les autres missions restent
disponibles. Les restitutions vocales en attente liées à cette mission sont aussi
annulées, avec libération de leur synthèse audio.

`policy.mission_timeout_seconds` vaut **120 secondes** par défaut, réglable entre
1 et 600 dans la configuration existante. Il couvre l’attente, la sélection des
outils, leur exécution et la préparation de la restitution. L’annulation est
coopérative : le nettoyage peut dépasser le délai et une requête déjà reçue par
un fournisseur peut avoir été facturée. Aucun nouveau mécanisme d’écriture distante
n’a été ajouté.

Les erreurs du planificateur, les résultats d’outil non réussis et la limite
d’étapes produisent un état d’échec explicite. Une mission ne devient pas réussie
sans résultat. Les boucles répétant exactement le même outil ne multiplient pas
les appels identiques. Les résultats réutilisés dans la session conservent leurs
références et sont signalés comme déjà obtenus ; ce réemploi n’est pas une nouvelle
vérification de leur fraîcheur.

La mission garde l’identifiant et le texte de la demande qui l’a déclenchée, même
si elle a attendu pendant que d’autres sujets étaient discutés. Les tours suivants
restent disponibles pour interpréter une correction. Cela encadre le contexte du
modèle sans garantir son interprétation sémantique.

La durée affichée est mesurée côté serveur avec une horloge monotone. Elle inclut
l’attente de la mission et la préparation de sa réponse, jusqu’à son état terminal ;
elle exclut la lecture complète du son chez les participants.

### Origine des réponses

Dans **Conversation**, les réponses ayant des références proposent **Origine de
cette réponse** : paroles associées et liens renvoyés par la recherche. Les liens
sont dédupliqués ; les schémas non HTTP(S), les URL mal formées et celles contenant
des identifiants sont écartés. Une référence associée n’est pas une preuve que chaque
affirmation de la réponse est correcte. Les réponses sans référence n’en inventent pas.

Les commandes de recherche restent dans l’inspecteur existant. Son historique
technique est replié ; aucune rubrique principale supplémentaire n’est ajoutée.

## Vérification

**134 tests Python et 23 tests frontend réussis**, compilation TypeScript/Vite,
formatage et contrôle des secrets. L’avertissement de dépréciation Starlette/httpx
déjà présent reste sans échec associé.

- Tests de régression : délai dépassé, libération du fournisseur, annulation en
  attente et pendant l’exécution, suppression de la voix associée, panne de
  planification, résultat non réussi, réemploi des sources, limite de boucle et
  préservation de la demande dans une conversation qui évolue.
- Frontend : coupure, temporisation progressive, nouveau jeton, brouillon conservé,
  refus de connexion, absence de reprise automatique du microphone, sources et URL.
- Chromium : annuler une recherche bloquée puis réussir une autre recherche avec
  sa référence ; fermer la connexion et revenir en pause sans rechargement ni
  perte du brouillon ; accord obligatoire avant reprise. Parcours et affichage
  contrôlés à 320, 390, 768 et 1440 px, sans erreur JavaScript détectée.
- Partage audio : le signal réel de l’onglet Atlas a été capturé dans un second
  onglet Chromium, sans périphérique audio fictif. Aucune réunion externe n’a été
  utilisée pour ce contrôle.
- Fournisseurs réels : sur deux interventions fictives dans une base isolée,
  notes, proposition avec citation exacte, recherche web et réponse écrite liée
  à ses sources ont réussi. La recherche mesurée a duré **30,7 s** sur cet essai
  unique ; ce n’est ni un benchmark ni une garantie de délai.

Rapports locaux : `tmp/atlas-browser-validation.json`,
`tmp/atlas-tab-audio-validation.json`, `tmp/workspace-live-validation.json`.
Sauvegarde du code avant ces changements : `tmp/backups/before-atlas-reliability.zip`.
Le serveur a été redémarré sur `127.0.0.1:8765` après sauvegarde SQLite dans
`tmp/backups/before-atlas-reliability-restart.sqlite3`. Les routes de santé,
d’interface, de bootstrap et de contrat répondent en HTTP 200 ; la commande
d’annulation et la nouvelle interface sont présentes. Le contenu des sessions
sauvegardées est identique avant et après redémarrage, vérifié dans
`tmp/atlas-reliability-validation.json`.
Les appels réels ont consommé des crédits ; aucun microphone ni contenu des sessions
de l’utilisateur n’a été utilisé pour les tests.

La réception de la voix dans l’appel réel et le logiciel vidéo restent à essayer
avec un participant selon le [guide de démonstration](demo-video.md).
