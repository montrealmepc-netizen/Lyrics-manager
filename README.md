# MEPC Montreal Lyrics V1.0.1 - OBS Studio Script

A comprehensive Python script for OBS Studio designed to manage and display worship song lyrics for live church services. This tool provides a powerful control panel to load, search, organize, edit, and display lyrics from a **FreeShow (`.show` file)** song library directly within OBS.

This script was developed by and for the production team at [MEPC Montreal](https://www.mepcmontreal.ca).

![Script Manager Screenshot](https://i.imgur.com/your-image-link-here.png)  ---

## ✨ Key Features

* **🎵 FreeShow Library Integration:** Automatically scans and loads your entire library of FreeShow `.show` files, organizing them by category based on your folder structure.
* **🗓️ Agenda / Playlist Management:** Build a service playlist ("Agenda") by adding songs from your library. You can reorder, remove, or clear the agenda on the fly. The agenda is saved automatically.
* **🔍 Smart Search:** A powerful search engine that finds songs by title, number, or lyrics content. It uses a scoring system to bring the most relevant results to the top.
* **✍️ Full Lyrics Editor:** Select any song and edit its lyrics directly within the manager. Changes can be saved back to the original `.show` file, making corrections simple and permanent.
* **📄 Page-by-Page Display:** Long song verses are automatically split into readable "pages" or "blocks" that you can navigate through one by one.
* ** seamlesslyOBS Integration:** The script controls a GDI+ text source in your scene and responds to configurable hotkeys for smooth operation during a live service.

## ✅ Prerequisites

1.  **OBS Studio:** Version 27 or newer is recommended.
2.  **Python 3:** A working Python installation that OBS Studio is configured to use.
3.  **FreeShow Song Library:** A folder containing your song library saved as `.show` files. You can organize songs into subfolders, which will be used as categories.
4.  **GDI+ Text Source:** You must have a "Text (GDI+)" source created in your OBS scene. This is the source the script will send the lyrics to.

## ⚙️ Installation & Setup

1.  **Download the Script:**
    * Download the `mepc_montreal_lyrics_v1.0.1.py` file from this repository.

2.  **Install the Script in OBS:**
    * In OBS Studio, go to **Tools > Scripts**.
    * Click the **"+"** button in the bottom left corner and select the downloaded Python script file.

3.  **Configure the Script:**
    * With the script selected, you will see its properties on the right.
