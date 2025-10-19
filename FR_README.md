# Gestionnaire de Paroles Live v2.0

Un script Python pour OBS Studio conçu pour gérer et afficher des paroles de chants à partir de fichiers `.show`. Il dispose d'une interface graphique moderne qui reste au premier plan, avec des capacités d'édition en direct, une gestion d'agenda et un panneau d'aperçu en temps réel.

Ce script vous permet de faire des corrections de texte instantanées depuis une fenêtre de contrôle dédiée et de les voir apparaître en direct sur votre source de texte OBS, sans avoir besoin de sauvegarder le fichier au préalable.

## Fonctionnalités

* **Édition Live :** Voyez instantanément les changements de l'éditeur dans votre source de texte OBS et dans le panneau d'aperçu.
* **Sauvegarde Manuelle :** Les modifications sont temporaires et conservées en mémoire. Elles ne sont **pas** sauvegardées en permanence dans votre fichier `.show` tant que vous n'appuyez pas manuellement sur le bouton "Sauvegarder les Modifications".
* **Agenda (Playlist) :** Construisez, gérez et réorganisez une liste de chants pour votre événement.
* **Aperçu Live :** Un panneau intégré vous montre exactement ce qui est envoyé à OBS, y compris un statut "CACHÉ".
* **Recherche Intelligente :** Trouvez rapidement des chants par titre, numéro ou paroles dans la catégorie sélectionnée.
* **Compatibilité :** Conçu pour lire, analyser et éditer des bibliothèques de fichiers `.show`.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants :

1.  **OBS Studio :** Une version récente d'OBS Studio (27.x ou plus).
2.  **Python :** Une version compatible de Python (ex: 3.6 à 3.11) installée sur votre système.
3.  **Configuration Python d'OBS :** Vous devez configurer OBS pour qu'il pointe vers votre installation Python.
    * Dans OBS, allez à **Outils -> Scripts**.
    * Cliquez sur l'onglet **Paramètres Python**.
    * Définissez le **Chemin d'installation Python** vers le dossier où Python est installé (ex: `C:/Python311/`).
4.  **Bibliothèque de Chants :** Vous devez avoir un dossier contenant votre bibliothèque de chants sous forme de fichiers `.show`. Les sous-dossiers seront traités comme des catégories.
5.  **Source de Texte OBS :** Vous devez avoir ajouté une source **Texte (GDI+)** à la scène où vous souhaitez que les paroles apparaissent.

## Installation

1.  Téléchargez le fichier `live_lyrics_manager.py` (ou le nom que vous lui avez donné) depuis ce dépôt.
2.  Ouvrez OBS Studio.
3.  Allez dans **Outils -> Scripts**.
4.  Cliquez sur le bouton **+** (Ajouter) en bas à gauche.
5.  Trouvez et sélectionnez le fichier `.py` que vous avez téléchargé.

## Configuration

Une fois le script ajouté, cliquez dessus dans la fenêtre des Scripts pour accéder à ses propriétés :

1.  **Bibliothèque de Chants (dossier .show) :** Cliquez sur `Parcourir` et sélectionnez le dossier principal qui contient tous vos fichiers de chants `.show`.
2.  **Source de Texte :** Sélectionnez la source **Texte (GDI+)** que vous avez créée dans le menu déroulant. C'est ici que les paroles seront affichées.
3.  **Lignes par Affichage :** (Défaut : 1) Définissez combien de lignes de texte afficher à la fois par diapositive.
4.  Cliquez sur `Fermer`. Le script est maintenant chargé et fonctionnel.

## Utilisation

1.  **Ouvrir le Gestionnaire :**
    * Allez dans **Outils -> Scripts**.
    * Cliquez sur le bouton **Ouvrir le Gestionnaire**.
    * *Alternativement*, configurez un raccourci clavier (voir étape 2).

2.  **Configurer les Raccourcis Clavier (Recommandé) :**
    * Allez dans **Fichier -> Paramètres -> Raccourcis clavier**.
    * Recherchez la section intitulée "Mepc_Lyrics".
    * Assignez des touches pour les fonctions essentielles comme :
        * `Mepc_Lyrics: Suivant` (Diapositive suivante)
        * `Mepc_Lyrics: Précédent` (Diapositive précédente)
        * `Mepc_Lyrics: Prochain Chant de l'Agenda`
        * `Mepc_Lyrics: Afficher/Cacher le Texte` (Toggle l'affichage)
        * `Mepc_Lyrics: Ouvrir/Fermer Gestionnaire`

3.  **Gérer un événement :**
    * Utilisez la **Recherche** et le menu déroulant **Catégorie** pour trouver des chants.
    * Double-cliquez sur un chant dans la "Liste des Chansons" pour l'ajouter à l'"Agenda".
    * Double-cliquez sur un chant dans l'**Agenda** pour le charger et l'afficher.
    * Utilisez vos raccourcis clavier ou les boutons `>` et `<` pour naviguer entre les diapositives.
    * Si vous voyez une faute de frappe, tapez simplement dans le panneau **"Éditeur de Texte"**. Le changement apparaîtra instantanément dans l'"Aperçu Live" et dans OBS.
    * Lorsque vous êtes prêt à rendre vos modifications permanentes, cliquez sur le bouton **`💾 Sauvegarder les Modifications`** en bas.

## Auteur

* Développé par l'équipe de production de MEPC Montreal.
* [www.mepcmontreal.ca](https://www.mepcmontreal.ca)
