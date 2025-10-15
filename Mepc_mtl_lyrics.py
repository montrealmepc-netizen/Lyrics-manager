# CODE V1.0.0 - MEPC MONTREAL LYRICS (VERSION FINALE)

import obspython as obs
import tkinter as tk
from tkinter import font
import os
import json
import time
import copy 

# --- Global variables ---
library_folder_path = ""
text_source_name = ""
full_song_library = []
# lyrics_blocks contient des dictionnaires (les "pages" segmentées)
lyrics_blocks = [] 
current_index = -1
current_song_data = {}
lines_per_display = 2
editor_window = None

# Variables pour la gestion des catégories et de l'agenda
current_category = "" 
song_agenda = [] 

# --- OBS Script Functions ---

def script_description():
    return """
    <h2>MEPC MONTREAL LYRICS (Gestionnaire de Paroles)</h2>
    <p>Gérez et modifiez votre bibliothèque de chants FreeShow (.show) avec un éditeur moderne qui reste au-dessus d'OBS.</p>
    <p>Ce script est open source (disponible sur GitHub) et a été développé par l'équipe de production de louange de <a href='https://www.mepcmontreal.ca'>www.mepcmontreal.ca</a>. Version : 1.0.0</p>
    """

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_path(props, "library_folder", "Bibliothèque de Chants (dossier .show)", obs.OBS_PATH_DIRECTORY, "", None)
    
    source_list = obs.obs_properties_add_list(props, "text_source", "Source de Texte", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(source_list, name, name)
    obs.source_list_release(sources)

    obs.obs_properties_add_int(props, "lines_to_show", "Lignes par Affichage", 1, 10, 1)
    obs.obs_properties_add_color(props, "text_color", "Couleur du Texte")
    obs.obs_properties_add_color(props, "bg_color", "Couleur du Fond")
    obs.obs_properties_add_int(props, "bg_opacity", "Opacité du Fond (%)", 0, 100, 1)
    obs.obs_properties_add_button(props, "editor_button", "Ouvrir le Gestionnaire", open_editor_callback)
    return props

def script_load(settings):
    global text_source_name, library_folder_path, lines_per_display
    text_source_name = obs.obs_data_get_string(settings, "text_source")
    library_folder_path = obs.obs_data_get_string(settings, "library_folder")
    lines_per_display = obs.obs_data_get_int(settings, "lines_to_show")
    setup_hotkeys()
    scan_freeshow_library(settings)
    reset_current_song_state()
    print("MEPC MONTREAL LYRICS (V1.0.0) chargé.")

def script_update(settings):
    global library_folder_path, text_source_name, lines_per_display, current_song_data
    
    new_lines_per_display = obs.obs_data_get_int(settings, "lines_to_show")
    lines_changed = new_lines_per_display != lines_per_display
    lines_per_display = new_lines_per_display
    
    new_folder_path = obs.obs_data_get_string(settings, "library_folder")
    if new_folder_path != library_folder_path:
        library_folder_path = new_folder_path
        scan_freeshow_library(settings)
    
    text_source_name = obs.obs_data_get_string(settings, "text_source")
    apply_source_settings(settings)
    
    # Si les lignes ont changé ET qu'une chanson est chargée, on la recharge pour reségmenter
    if lines_changed and current_song_data:
        load_song(current_song_data)
    else:
        update_obs_text()

def script_unload():
    global editor_window
    if editor_window and editor_window.winfo_exists(): editor_window.destroy()
    print("MEPC MONTREAL LYRICS (V1.0.0) déchargé.")

def reset_current_song_state():
    """Réinitialise les variables de la chanson actuellement chargée."""
    global current_song_data, lyrics_blocks, current_index
    current_song_data = {}
    lyrics_blocks = []
    current_index = -1
    update_obs_text() # Pour vider le texte affiché dans OBS

def apply_source_settings(settings):
    source = obs.obs_get_source_by_name(text_source_name)
    if source:
        text_color = obs.obs_data_get_int(settings, "text_color")
        bg_color = obs.obs_data_get_int(settings, "bg_color")
        bg_opacity = obs.obs_data_get_int(settings, "bg_opacity")
        s = obs.obs_data_create()
        obs.obs_data_set_int(s, "color", text_color)
        obs.obs_data_set_int(s, "bk_color", bg_color)
        obs.obs_data_set_int(s, "bk_opacity", bg_opacity)
        obs.obs_source_update(source, s)
        obs.obs_data_release(s)
        obs.obs_source_release(source)

def on_hotkey_pressed(hotkey_id):
    actions = {"mepc_lyrics_next": next_lyric, "mepc_lyrics_prev": prev_lyric, "mepc_lyrics_first": first_lyric, "mepc_lyrics_last": last_lyric}
    if hotkey_id in actions: actions[hotkey_id]()

def setup_hotkeys():
    hotkeys = {"mepc_lyrics_next": "Mepc_Lyrics: Suivant", "mepc_lyrics_prev": "Mepc_Lyrics: Précédent", "mepc_lyrics_first": "Mepc_Lyrics: Premier", "mepc_lyrics_last": "Mepc_Lyrics: Dernier"}
    for id, desc in hotkeys.items(): obs.obs_hotkey_register_frontend(id, desc, lambda p, id=id: on_hotkey_pressed(id) if p else None)

# --- LOGIQUE DE SCAN AVEC CATÉGORIES (SOUS-DOSSIERS) ---
def scan_freeshow_library(settings):
    global full_song_library, displayed_songs, current_category
    full_song_library.clear()
    
    if library_folder_path and os.path.isdir(library_folder_path):
        print("Scan de la bibliothèque FreeShow (.show) par catégories (dossiers)...")
        start_time = time.time()
        
        for root, dirs, files in os.walk(library_folder_path):
            if root == library_folder_path:
                category = "Non Classé"
            else:
                category = os.path.basename(root)

            for filename in files:
                if filename.lower().endswith(".show"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        song_data = data[1]
                        title = song_data.get("name", "Titre inconnu")
                        number = song_data.get("quickAccess", {}).get("number", "-")
                        blocks, full_lyrics_text = [], ""
                        slides = song_data.get("slides", {})
                        
                        for slide_id, slide_content in slides.items():
                            slide_text_lines = []
                            items = slide_content.get("items", [])
                            if items and "lines" in items[0]:
                                for line in items[0]["lines"]:
                                    line_text = "".join([part.get("value", "") for part in line.get("text", [])])
                                    slide_text_lines.append(line_text)
                            block_text = "\n".join(slide_text_lines)
                            if block_text:
                                blocks.append(block_text)
                                full_lyrics_text += block_text + "\n\n"
                                
                        full_song_library.append({
                            "title": title.strip(), 
                            "number": number.strip(), 
                            "lyrics": full_lyrics_text.strip().lower(), 
                            "blocks": blocks, 
                            "path": filepath,
                            "category": category 
                        })
                    except Exception as e:
                        print(f"  - Erreur de lecture du fichier '{filename}' ({category}): {e}")
                        
        # Tri par ordre numérique (1, 2, 3...) puis alphabétique
        def get_sort_key(song):
            number_str = song.get('number', '').strip()
            try:
                # Clé primaire: le numéro en tant qu'entier.
                return int(number_str)
            except ValueError:
                # Si non numérique (ex: "-", "A23"), on utilise float('inf') pour le placer
                # à la fin, et le titre en minuscule comme clé secondaire.
                return float('inf')

        full_song_library.sort(key=lambda x: (get_sort_key(x), x['title'].lower()))
        
        displayed_songs = full_song_library[:]
        
        end_time = time.time()
        print(f"{len(full_song_library)} chansons importées en {end_time - start_time:.2f} secondes.")
        
    if editor_window and editor_window.winfo_exists():
        editor_window.refresh_category_and_song_list() 

def load_song(song_dict):
    global lyrics_blocks, current_index, current_song_data, lines_per_display
    current_song_data = song_dict
    
    # Logique de segmentation en pages basées sur lines_per_display
    lyrics_blocks = []
    
    for i, full_block_text in enumerate(current_song_data.get("blocks", [])):
        all_lines = full_block_text.split('\n')
        
        # Découpe le bloc complet en pages de 'lines_per_display' lignes
        for j in range(0, len(all_lines), lines_per_display):
            # Construit la "page" (le sous-bloc)
            page_lines = all_lines[j : j + lines_per_display]
            page_text = "\n".join(page_lines)
            
            # Stocke le sous-bloc segmenté
            if page_text.strip():
                lyrics_blocks.append({
                    "text": page_text,
                    "is_new_verse": (j == 0), # Marque si c'est le début d'un nouveau couplet
                    "verse_index": i + 1      # Numéro du couplet original (pour l'affichage)
                })

    current_index = 0 if lyrics_blocks else -1
    if editor_window and editor_window.winfo_exists(): editor_window.update_on_song_select()
    update_obs_text()

def update_obs_text():
    if not text_source_name: return
    source = obs.obs_get_source_by_name(text_source_name)
    if source:
        text_to_display = ""
        if 0 <= current_index < len(lyrics_blocks):
            # Utilise le texte de la "page" segmentée
            text_to_display = lyrics_blocks[current_index]["text"]
            
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text_to_display)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

def navigate_to(index):
    global current_index
    if lyrics_blocks:
        current_index = max(0, min(index, len(lyrics_blocks) - 1))
        update_obs_text()
        if editor_window and editor_window.winfo_exists(): editor_window.highlight_current_verse()

def next_lyric(): navigate_to(current_index + 1)
def prev_lyric(): navigate_to(current_index - 1)
def first_lyric(): navigate_to(0)
def last_lyric(): navigate_to(len(lyrics_blocks) - 1)

def open_editor_callback(props, prop):
    global editor_window
    if editor_window is None or not editor_window.winfo_exists():
        editor_window = LyricsEditor()
        editor_window.protocol("WM_DELETE_WINDOW", editor_window.on_closing)
        editor_window.mainloop()
    else: editor_window.lift()

# ----------------------------------------------------------------------
# --- CLASSE TKINTER POUR L'ÉDITEUR ---
# ----------------------------------------------------------------------

class LyricsEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestionnaire de Louange"); self.geometry("1450x700") 

        self.attributes('-topmost', True)

        # --- STYLE MODERNE CLAIR ---
        self.font_main = font.Font(family="Segoe UI", size=10)
        self.font_list = font.Font(family="Segoe UI", size=11)
        self.font_editor = font.Font(family="Consolas", size=11)
        
        self.bg_color = "#f0f0f0"       
        self.fg_color = "#1f1f1f"       
        self.list_bg = "#ffffff"        
        self.select_bg = "#0078d4"      
        self.select_fg = "#ffffff"      
        self.button_bg = "#0078d4"      
        self.button_fg = "#ffffff"      
        self.button_active_bg = "#005a9e" 
        self.sash_color = "#cccccc"     
        self.label_color = "#555555"    
        
        self.configure(bg=self.bg_color)

        # --- BARRE DE CONTRÔLE SUPÉRIEURE (Recherche et Catégorie) ---
        control_frame = tk.Frame(self, bg=self.bg_color); control_frame.pack(fill=tk.X, padx=12, pady=(10,8))
        
        # Champ de recherche
        tk.Label(control_frame, text="🔍 Rechercher :", bg=self.bg_color, fg=self.label_color, font=self.font_main).pack(side=tk.LEFT)
        self.search_var = tk.StringVar(); self.search_var.trace("w", self.on_search_change)
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, bg=self.list_bg, fg=self.fg_color, insertbackground=self.fg_color, font=self.font_main, relief=tk.SOLID, bd=1, highlightthickness=1); search_entry.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=8, ipady=4)
        search_entry.config(highlightcolor=self.select_bg, highlightbackground="#dddddd")
        
        # Menu déroulant des catégories (Dropdown)
        tk.Label(control_frame, text="▶️ Catégorie :", bg=self.bg_color, fg=self.label_color, font=self.font_main).pack(side=tk.LEFT, padx=(20, 5))
        self.category_var = tk.StringVar(self)
        self.category_var.set(current_category)
        self.category_var.trace("w", self.on_category_change)
        self.category_dropdown = tk.OptionMenu(control_frame, self.category_var, "Placeholder") 
        self.category_dropdown.config(bg=self.button_bg, fg=self.button_fg, activebackground=self.button_active_bg, activeforeground=self.button_fg, relief=tk.FLAT, font=self.font_main, padx=10, pady=5, bd=0)
        self.category_dropdown.pack(side=tk.LEFT)

        bottom_frame = tk.Frame(self, bg=self.bg_color); bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(5,10))
        tk.Button(bottom_frame, text="💾 Sauvegarder les Modifications", command=self.save_lyrics, bg=self.button_bg, fg=self.button_fg, activebackground=self.button_active_bg, activeforeground=self.button_fg, relief=tk.FLAT, font=self.font_main, padx=10, pady=5, bd=0).pack(side=tk.RIGHT)
        
        # --- PANEDWINDOW POUR LES 4 COLONNES ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=self.sash_color, sashwidth=8, sashrelief=tk.FLAT, bd=0);
        main_pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,0))
        
        # Colonne 1 : Agenda
        agenda_container_frame = tk.LabelFrame(main_pane, text="Agenda", bg=self.bg_color, fg=self.label_color, font=self.font_main, bd=0, padx=5, pady=5); agenda_container_frame.grid_rowconfigure(0, weight=1); agenda_container_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(agenda_container_frame, width=300, minsize=200)

        agenda_frame = tk.Frame(agenda_container_frame, bg=self.list_bg); agenda_frame.grid(row=0, column=0, sticky="nsew")
        self.agenda_listbox = tk.Listbox(agenda_frame, bg=self.list_bg, fg=self.fg_color, selectbackground=self.select_bg, selectforeground=self.select_fg, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.agenda_listbox.pack(fill=tk.BOTH, expand=True)
        self.agenda_listbox.bind("<Double-Button-1>", self.on_agenda_select)
        
        # Boutons de l'Agenda
        agenda_button_frame = tk.Frame(agenda_container_frame, bg=self.bg_color); agenda_button_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        tk.Button(agenda_button_frame, text="⬆️", command=self.move_agenda_up, width=3, bg=self.list_bg, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT)
        tk.Button(agenda_button_frame, text="⬇️", command=self.move_agenda_down, width=3, bg=self.list_bg, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT, padx=3)
        tk.Button(agenda_button_frame, text="❌ Retirer", command=self.remove_from_agenda, bg=self.list_bg, relief=tk.FLAT, font=self.font_main).pack(side=tk.RIGHT)
        
        
        # Colonne 2 : Chansons Filtrées
        songs_frame = tk.LabelFrame(main_pane, text="Liste des Chansons", bg=self.bg_color, fg=self.label_color, font=self.font_main, bd=0, padx=5, pady=5); songs_frame.grid_rowconfigure(0, weight=1); songs_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(songs_frame, width=350, minsize=200)
        self.song_listbox = tk.Listbox(songs_frame, bg=self.list_bg, fg=self.fg_color, selectbackground=self.select_bg, selectforeground=self.select_fg, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.song_listbox.grid(row=0, column=0, sticky="nsew"); self.song_listbox.bind("<<ListboxSelect>>", self.on_song_select)
        self.song_listbox.bind("<Double-Button-1>", self.add_to_agenda) 
        
        # Bouton Ajouter à l'Agenda
        song_button_frame = tk.Frame(songs_frame, bg=self.bg_color); song_button_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        tk.Button(song_button_frame, text="➕ Ajouter à l'Agenda", command=self.add_to_agenda_button, bg="#e0e0e0", relief=tk.FLAT, font=self.font_main).pack(fill=tk.X)

        # Les autres colonnes (Verses et Éditeur)
        verses_frame = tk.LabelFrame(main_pane, text="Couplets", bg=self.bg_color, fg=self.label_color, font=self.font_main, bd=0, padx=5, pady=5); verses_frame.grid_rowconfigure(0, weight=1); verses_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(verses_frame, width=300, minsize=150)
        self.verse_listbox = tk.Listbox(verses_frame, bg=self.list_bg, fg=self.fg_color, selectbackground=self.select_bg, selectforeground=self.select_fg, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.verse_listbox.grid(row=0, column=0, sticky="nsew"); self.verse_listbox.bind("<<ListboxSelect>>", self.on_verse_select)
        
        editor_frame = tk.LabelFrame(main_pane, text="Éditeur de Texte", bg=self.bg_color, fg=self.label_color, font=self.font_main, bd=0, padx=5, pady=5); editor_frame.grid_rowconfigure(0, weight=1); editor_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(editor_frame, width=500, minsize=300)
        self.editor_text = tk.Text(editor_frame, wrap=tk.WORD, bg=self.list_bg, fg=self.fg_color, insertbackground=self.fg_color, selectbackground=self.select_bg, selectforeground=self.select_fg, font=self.font_editor, relief=tk.SOLID, bd=1, highlightthickness=0, undo=True, padx=8, pady=8)
        self.editor_text.grid(row=0, column=0, sticky="nsew")

        self.refresh_category_and_song_list() 
        
    def on_closing(self): global editor_window; editor_window = None; self.destroy()

    # --- GESTION DES CATÉGORIES (DROP-DOWN) ---
    def get_categories(self):
        """Récupère toutes les catégories uniques des chansons (sans "Toutes les chansons")."""
        categories = sorted(list(set(song['category'] for song in full_song_library)))
        return categories

    def refresh_category_and_song_list(self):
        """Met à jour le dropdown des catégories et la liste des chansons."""
        global current_category
        
        # 1. Mise à jour du Dropdown 
        menu = self.category_dropdown["menu"]
        menu.delete(0, "end")
        new_categories = self.get_categories()
        
        for category in new_categories:
            menu.add_command(label=category, command=lambda value=category: self.category_var.set(value))

        # Assurez-vous que la catégorie actuelle existe toujours et définit une par défaut
        if self.category_var.get() not in new_categories or not new_categories:
            new_default = new_categories[0] if new_categories else "" 
            self.category_var.set(new_default)
            current_category = new_default
            
        # 2. Mise à jour des listes
        self.filter_songs_by_category()
        self.refresh_song_list()
        self.refresh_agenda_list()

    def on_category_change(self, *args):
        """Action lorsque la catégorie sélectionnée change."""
        global current_category
        current_category = self.category_var.get()
        self.filter_songs_by_category()
        self.refresh_song_list()
        self.search_var.set("") 

    def filter_songs_by_category(self):
        """Filtre la liste displayed_songs selon la catégorie et la recherche."""
        global displayed_songs
        query = self.search_var.get().lower()
        
        # Filtre uniquement par la catégorie sélectionnée
        filtered_by_category = [song for song in full_song_library if song['category'] == current_category]
                
        # Appliquer la recherche sur le résultat filtré
        if query:
            displayed_songs = [song for song in filtered_by_category if query in song['title'].lower() or query in song['number'].lower() or query in song['lyrics']]
        else:
            displayed_songs = filtered_by_category[:]

    # --- GESTION DE LA RECHERCHE ---
    def on_search_change(self, *args):
        self.filter_songs_by_category()
        self.refresh_song_list()

    # --- LISTE DES CHANSONS ---
    def refresh_song_list(self):
        self.song_listbox.delete(0, tk.END)
        for song in displayed_songs:
            # Affiche UNIQUEMENT le numéro et le titre (sans la catégorie)
            number_display = f"{song['number']} - " if song['number'] and song['number'] != '-' else ""
            self.song_listbox.insert(tk.END, f" {number_display}{song['title']}")

    def on_song_select(self, event):
        selection = event.widget.curselection()
        if selection:
            song_index_in_displayed_list = selection[0]
            selected_song = displayed_songs[song_index_in_displayed_list]
            load_song(selected_song)

    # --- GESTION DE L'AGENDA (PLAYLIST) ---
    def refresh_agenda_list(self):
        """Affiche les chansons actuellement dans l'agenda."""
        self.agenda_listbox.delete(0, tk.END)
        for i, song in enumerate(song_agenda):
             self.agenda_listbox.insert(tk.END, f"{i+1:02d}. [{song['category']}] {song['number']} - {song['title']}")
             
    def add_to_agenda(self, event):
        """Ajoute la chanson double-cliquée à la liste de l'agenda."""
        self.add_to_agenda_button()
        
    def add_to_agenda_button(self):
        """Ajoute la chanson sélectionnée à la liste de l'agenda."""
        selection = self.song_listbox.curselection()
        if selection:
            song_index = selection[0]
            selected_song = displayed_songs[song_index]
            song_agenda.append(copy.deepcopy(selected_song)) 
            self.refresh_agenda_list()
            print(f"Ajouté à l'agenda: {selected_song['title']}")

    def on_agenda_select(self, event):
        """Charge la chanson double-cliquée depuis l'agenda."""
        selection = self.agenda_listbox.curselection()
        if selection:
            index = selection[0]
            selected_song = song_agenda[index]
            load_song(selected_song) 
            self.song_listbox.selection_clear(0, tk.END) 

    def remove_from_agenda(self):
        """Retire la chanson sélectionnée de l'agenda."""
        selection = self.agenda_listbox.curselection()
        if selection:
            index = selection[0]
            del song_agenda[index]
            self.refresh_agenda_list()
            
            new_index = min(index, len(song_agenda) - 1)
            if new_index >= 0:
                self.agenda_listbox.selection_set(new_index)
                self.agenda_listbox.activate(new_index)

    def move_agenda_up(self):
        """Déplace la chanson sélectionnée vers le haut dans l'agenda."""
        selection = self.agenda_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                song = song_agenda.pop(index)
                song_agenda.insert(index - 1, song)
                self.refresh_agenda_list()
                self.agenda_listbox.selection_set(index - 1)
                self.agenda_listbox.activate(index - 1)

    def move_agenda_down(self):
        """Déplace la chanson sélectionnée vers le bas dans l'agenda."""
        selection = self.agenda_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(song_agenda) - 1:
                song = song_agenda.pop(index)
                song_agenda.insert(index + 1, song)
                self.refresh_agenda_list()
                self.agenda_listbox.selection_set(index + 1)
                self.agenda_listbox.activate(index + 1)
                
    # --- GESTION DES COUPLETS ET DE L'ÉDITEUR ---
    def update_on_song_select(self):
        self.update_verse_list()
        self.editor_text.delete('1.0', tk.END)
        # L'éditeur affiche toujours le texte complet non segmenté du fichier d'origine
        full_text = "\n\n".join(current_song_data.get("blocks", []))
        self.editor_text.insert('1.0', full_text)

    def update_verse_list(self):
        self.verse_listbox.delete(0, tk.END)
        current_verse_num = 0
        
        # Affiche chaque "page" (segmentation de lignes) dans la liste des couplets
        for i, page_data in enumerate(lyrics_blocks):
            preview = page_data["text"].split('\n')[0]
            
            if page_data["is_new_verse"]:
                # Marque le début d'un nouveau couplet
                current_verse_num = page_data["verse_index"]
                prefix = f" Verse {current_verse_num:02d} | "
            else:
                # Page suivante du même couplet
                prefix = f"   - Page {i+1:02d} | " # Utilisation de :02d pour un meilleur alignement

            self.verse_listbox.insert(tk.END, f"{prefix}{preview}")
            
        self.highlight_current_verse()

    def on_verse_select(self, event):
        selection = event.widget.curselection()
        if selection: navigate_to(selection[0])

    def highlight_current_verse(self):
        self.verse_listbox.selection_clear(0, tk.END)
        if 0 <= current_index < self.verse_listbox.size():
            self.verse_listbox.selection_set(current_index)
            self.verse_listbox.activate(current_index)
            self.verse_listbox.see(current_index)
            
    # --- SAUVEGARDE ---
    def save_lyrics(self):
        if not current_song_data or not current_song_data.get("path"):
            print("Aucune chanson sélectionnée pour la sauvegarde.")
            return
        
        filepath = current_song_data["path"]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Le texte édité est toujours le texte complet non segmenté
            edited_text = self.editor_text.get("1.0", tk.END).strip()
            new_blocks = edited_text.split('\n\n')
            
            new_slides = {}
            slide_ids = list(original_data[1]["slides"].keys())
            
            # Reconstruction des slides (un slide par bloc/couplet, comme FreeShow l'attend)
            for i, block in enumerate(new_blocks):
                slide_id = slide_ids[i] if i < len(slide_ids) else f"newslide_{int(time.time())}_{i}"
                lines_data = []
                for line_text in block.split('\n'):
                    lines_data.append({"align": "", "text": [{"style": "", "value": line_text}]})
                
                # Récupère l'ancien template ou utilise un template par défaut
                slide_template = original_data[1]["slides"].get(slide_id, {
                    "group": "", "color": None, "settings": {}, "notes": "", "globalGroup": "verse"
                })
                slide_template["items"] = [{"style": "top:120px;left:50px;height:840px;width:1820px;", "lines": lines_data}]
                new_slides[slide_id] = slide_template
            
            original_data[1]["slides"] = new_slides
            
            # Mise à jour des layouts pour refléter les nouveaux IDs/nombre de slides
            for layout_id, layout_content in original_data[1]["layouts"].items():
                layout_content["slides"] = [{"id": sid} for sid in new_slides.keys()]

            with open(filepath, 'w', encoding='utf-8') as f:
                # Utiliser des séparateurs sans espace pour un fichier plus compact, comme FreeShow
                json.dump(original_data, f, ensure_ascii=False, separators=(',', ':'))
            
            print(f"Chanson '{os.path.basename(filepath)}' sauvegardée avec succès.")
            
            # Recharger la bibliothèque pour que les changements soient pris en compte
            current_title = current_song_data.get('title')
            scan_freeshow_library(None)
            
            # Mise à jour de l'Agenda (car l'original de la bibliothèque a changé)
            for i, agenda_song in enumerate(song_agenda):
                if agenda_song.get("path") == filepath:
                    updated_song = next((s for s in full_song_library if s["path"] == filepath), None)
                    if updated_song:
                        song_agenda[i] = copy.deepcopy(updated_song) 
                        print(f"Agenda mis à jour pour : {updated_song['title']}")
                        break

            editor_window.refresh_agenda_list()
            
            # Essayer de resélectionner la chanson après le rechargement
            if editor_window and editor_window.winfo_exists():
                for i, song in enumerate(displayed_songs):
                    if song['title'] == current_title:
                        editor_window.song_listbox.selection_set(i)
                        load_song(song)
                        break

        except Exception as e:
            print(f"ERREUR lors de la sauvegarde du fichier '{filepath}': {e}")