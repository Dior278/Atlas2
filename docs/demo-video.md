# Préparer la démonstration vidéo

Version locale synchronisée avec Atlas `4e0823f`. Le scénario ci-dessous sert de
répétition ; les réponses restent calculées par les fournisseurs et ne sont pas
préenregistrées ni injectées dans le produit.

## Installation pour l’enregistrement

Ouvrir http://127.0.0.1:8765/ dans Chrome ou Edge, avec un seul onglet Atlas actif.
Prévoir quelques secondes de délai pour les recherches. Gradium reste le fournisseur
vocal actif par défaut ; les registres permettent un repli vers OpenAI si configuré.

## Faire entendre Atlas à tous les participants

La voix sort de l’onglet Atlas. Écouter l’appel dans Atlas ne transmet pas
automatiquement sa voix aux autres personnes : il faut configurer les deux sens.
Pour la démonstration, privilégier une réunion dans un onglet Chrome et un casque.

1. Rejoindre normalement la réunion avec le microphone habituel. Ouvrir Atlas dans
   un autre onglet du même navigateur. Informer les participants de l’analyse et
   de l’enregistrement ; la voix d’Atlas est une voix synthétique.
2. **Dans Atlas**, choisir **Microphone + audio partagé**, donner son accord et
   démarrer. Dans le sélecteur du navigateur, choisir **l’onglet de la réunion**
   et activer son audio. Atlas reçoit ainsi votre micro et les autres participants.
3. **Dans la réunion**, lancer le partage de contenu. Choisir cette fois
   **l’onglet Atlas**, avec l’audio de cet onglet. Les participants reçoivent alors
   la sortie sonore et l’image d’Atlas. Garder le microphone normal dans la réunion.
4. Dans Atlas, ouvrir **••• → Faire entendre Atlas dans l’appel → Jouer le son de
   test**. Demander à un participant de confirmer qu’il entend les deux notes.
   Le message local indique seulement que le signal a été joué ; Atlas ne peut pas
   vérifier le partage configuré dans une autre application.
5. Faire parler un participant : sa phrase doit apparaître dans Conversation.
   Demander une courte réponse à Atlas, puis confirmer sa réception à distance.
   Vérifier que cette réponse ne revient pas comme une intervention humaine.

| Plateforme | Réglage de sortie dans la réunion |
|---|---|
| Google Meet | **Présenter maintenant → Un onglet → Atlas**, avec **Partager aussi l’audio de l’onglet**. Rejoindre l’appel avant de présenter pour garder le microphone normal. [Guide officiel](https://support.google.com/meet/answer/9308856?hl=fr). |
| Teams sur le web | **Partager → Écran, fenêtre ou onglet → Atlas**, avec le partage de l’audio de l’onglet. Ce mode isole le son de l’onglet. [Guide officiel](https://support.microsoft.com/en-us/teams/meetings/share-sound-from-your-computer-in-microsoft-teams-meetings-or-live-events). |
| Zoom installé | **Partager l’écran → fenêtre Atlas → Partager le son** ; **Avancé → Audio de l’ordinateur** permet le son seul. Ce partage peut transmettre d’autres sons du poste : faire l’essai avec les participants. [Guide officiel](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0063608). |

Pour l’entrée d’Atlas, sélectionner le son de la réunion, pas l’audio de tout le
poste qui comprend déjà sa voix. Si une application installée ne permet pas cette
isolation, préférer sa version web pour la démonstration. Le casque limite le retour
acoustique ; le filtre textuel d’écho ne remplace pas un bon routage audio. En cas de
boucle, mettre Atlas en pause puis vérifier les deux sources avant de reprendre.

Le logiciel vidéo doit enregistrer votre microphone et la sortie sonore qui
contient l’appel et Atlas. Vérifier aussi le fichier enregistré : la confirmation
d’un participant ne valide pas à elle seule les pistes du logiciel vidéo.

Pour une présentation en solo, **Microphone** suffit ; le casque et la vérification
du microphone et du son de l’ordinateur dans l’enregistrement restent utiles.

## Parcours de répétition (environ trois minutes)

1. Créer une session après avoir confirmé l’information et l’accord des personnes.
2. Dire : « Nous préparons une démonstration. Renard préparera le prototype et Hibou
   relira la présentation. Nous retenons une interface en français. » Ouvrir Notes.
3. Dire : « Atlas, recherche la documentation officielle de WebRTC et indique la
   source. » Montrer l’avancement dans Agents, puis les résultats et références.
   Laisser la recherche se terminer avant de poser la question suivante.
4. Dire : « Correction : le prototype sera présenté lundi, pas vendredi. » Vérifier
   que la correction apparaît une seule fois dans Conversation. Une réponse d’Atlas
   ne doit pas réapparaître comme une nouvelle voix humaine.
5. Dans Engagements, préparer les propositions, relire l’extrait cité, puis confirmer
   une action et renseigner explicitement responsable/date. Télécharger son `.ics`.
   Une date relative prononcée n’est pas convertie automatiquement.
6. Mettre en pause, exporter en Markdown, terminer puis rouvrir la session : la
   lecture de la mémoire doit rester possible sans reprise automatique du micro.

Les voix d’un appel ne sont pas identifiées automatiquement. Les noms prononcés
peuvent être cités dans les notes ; attribuer une action à son responsable exige
une relecture. Si une API est indisponible, utiliser Pause et consulter les résultats
existants ; le mode Texte permet de poursuivre seulement si les fournisseurs
nécessaires restent disponibles. Aucun mode ne fabrique des résultats de secours.

## Essai matériel à faire avant la prise

Enregistrer 30 à 60 secondes avec le montage retenu : salutation, réponse d’Atlas,
interruption, nouvelle question. Réécouter le fichier pour vérifier les deux voix,
le volume, les sous-titres et l’absence de boucle. Les contrôles automatisés et les
appels API isolés ne valident pas le microphone physique, le routage du logiciel
vidéo, l’écho de la pièce ni la disponibilité future des fournisseurs. Un contrôle
local supplémentaire a capturé le véritable signal sonore de l’onglet Atlas dans
un second onglet Chromium, sans faux périphérique audio ; il ne remplace pas
l’essai de réception dans la réunion réelle.

Le détail des apports présentables est dans
[CONTRIBUTIONS-APARTE.md](CONTRIBUTIONS-APARTE.md).

## Montrer les nouveaux contrôles

Après une recherche, ouvrir **Conversation → Origine de cette réponse** pour
montrer la demande et les liens réellement renvoyés. Pendant une recherche, ouvrir
**Agents → Recherches → Arrêter cette recherche** pour changer de direction ; la
conversation et les notes restent disponibles.

En cas de coupure, laisser la reconnexion se faire. Le brouillon reste présent et
la session revient en pause ; confirmer l’accord avant de reprendre. Les paroles
échangées pendant la coupure ne sont pas reconstituées. Ces comportements sont
documentés dans [les améliorations de fiabilité](ameliorations-fiabilite.md).
