# Live Lyrics Manager v2.0

A Python script for OBS Studio designed to manage and display song lyrics from `.show` files. It features a modern, stay-on-top GUI with live-editing capabilities, agenda management, and a real-time preview panel.

This script allows you to make instant text corrections from a dedicated control window and have them appear live on your OBS text source, without needing to save the file first.

## Features

* **Live Editing:** Instantly see changes from the editor in your OBS text source and the preview panel.
* **Manual Save:** Edits are temporary and held in memory. They are **not** permanently saved to your `.show` file until you manually press the "Save Modifications" button.
* **Agenda (Playlist):** Build, manage, and reorder a setlist for your event.
* **Live Preview:** A built-in panel shows you exactly what is being sent to OBS, including a "HIDDEN" status.
* **Smart Search:** Quickly find songs by title, number, or lyrics within the selected category.
* **Compatibility:** Designed to read, parse, and edit `.show` file libraries.

## Prerequisites

Before you begin, ensure you have the following set up:

1.  **OBS Studio:** A recent version of OBS Studio (27.x or newer).
2.  **Python:** A compatible version of Python (e.g., 3.6 to 3.11) installed on your system.
3.  **OBS Python Configuration:** You must configure OBS to point to your Python installation.
    * In OBS, go to **Tools -> Scripts**.
    * Click the **Python Settings** tab.
    * Set the **Python Installation Path** to the directory where your Python is installed (e.g., `C:/Python311/` or `/usr/bin/python3`).
4.  **Song Library:** You must have a folder containing your song library as `.show` files. Subfolders will be treated as categories.
5.  **OBS Text Source:** You must have a **Text (GDI+)** source added to the scene where you want lyrics to appear.

## Installation

1.  Download the `live_lyrics_manager.py` file (or the name you've given it) from this repository.
2.  Open OBS Studio.
3.  Go to **Tools -> Scripts**.
4.  Click the **+** (Add) button in the bottom left.
5.  Find and select the `.py` file you downloaded.

## Configuration

Once the script is added, click on it in the Scripts window to access its properties:

1.  **Bibliothèque de Chants (dossier .show):** Click `Browse` and select the main folder that contains all your `.show` song files.
2.  **Source de Texte:** Select the **Text (GDI+)** source you created from the dropdown menu. This is where the lyrics will be displayed.
3.  **Lignes par Affichage:** (Default: 1) Set how many lines of text to show at once per slide.
4.  Click `Close`. The script is now loaded and running.

## Usage

1.  **Open the Manager:**
    * Go to **Tools -> Scripts**.
    * Click the **Ouvrir le Gestionnaire** (Open Manager) button.
    * *Alternatively*, set a hotkey (see step 2).

2.  **Set Hotkeys (Recommended):**
    * Go to **File -> Settings -> Hotkeys**.
    * Search for the section labeled "Mepc_Lyrics".
    * Set keys for essential functions like:
        * `Mepc_Lyrics: Suivant` (Next Slide)
        * `Mepc_Lyrics: Précédent` (Previous Slide)
        * `Mepc_Lyrics: Prochain Chant de l'Agenda` (Next Agenda Song)
        * `Mepc_Lyrics: Afficher/Cacher le Texte` (Toggle Display)
        * `Mepc_Lyrics: Ouvrir/Fermer Gestionnaire` (Open/Close Manager)

3.  **Running an Event:**
    * Use the **Search** and **Category** dropdowns to find songs.
    * Double-click a song in the "Liste des Chansons" to add it to the "Agenda".
    * Double-click a song in the **Agenda** to load it for display.
    * Use your hotkeys or the `>` and `<` buttons to navigate slides.
    * If you see a typo, simply type in the **"Éditeur de Texte"** panel. The change will appear instantly in the "Aperçu Live" and in OBS.
    * When you are ready to make your changes permanent, click the **`💾 Sauvegarder les Modifications`** button at the bottom.

## Author

* Developed by the MEPC Montreal production team.
* [www.mepcmontreal.ca](https://www.mepcmontreal.ca)
