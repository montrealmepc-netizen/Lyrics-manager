# Obs-Lyrics-for-church
lyrics manager for OBS designed for worship teams and live church services. It allows you to import, organize, edit, and display FreeShow (.show) files quickly and efficiently. With a built-in editor and agenda/playlist to prepare sessions, it gives full control over lyrics display, page by page, directly in OBS.
Installation

Install OBS Studio (version 27 or higher recommended).

Download the script mepc_montreal_lyrics.py.

Open OBS → Go to Tools → Scripts → Click + → Select the downloaded script.

Add a Text Source in OBS:

Either Text (GDI+) or Text (FreeType 2).

This is where the lyrics will be displayed.

Configure the script in OBS Scripts panel:

Library Folder: set the folder containing your .show FreeShow files.

Text Source: select the OBS text source you just created.

Lines per Display: choose how many lines should appear per page.

Optional: set text and background colors and background opacity.

Usage

Open the Lyrics Editor from the script interface in OBS.

Search & Filter Songs:

Use the search bar to filter by title, number, or lyrics content.

Use the category dropdown to filter by song categories.

Manage Your Agenda (Playlist):

Double-click a song in the list or click “➕ Add to Agenda” to add it.

Reorder songs with the ⬆️ / ⬇️ buttons.

Remove songs with the ❌ button.

Load a Song:

Select a song in the agenda or song list to load it.

The lyrics are automatically split into pages for display in OBS.

Navigate Lyrics in OBS:

Use hotkeys (Next / Previous / First / Last) to control the text display.

Edit Lyrics:

Modify the full lyrics in the editor panel.

Click “💾 Save Changes” to update the .show file.

The agenda will automatically update to reflect changes.
