# CODE V1.0.1 - MEPC MONTREAL LYRICS (VERSION STABLE SANS FENÊTRE VIRTUELLE)

import obspython as obs
import tkinter as tk
from tkinter import font, messagebox
import os
import json
import time
import copy
import unicodedata # Ajout pour la normalisation des accents

# --- Constantes Globales pour l'Agenda ---
AGENDA_FILE = "mepc_lyrics_agenda.json"
HOTKEY_NEXT_AGENDA = "mepc_lyrics_next_agenda"

# --- Variables Globales (Gestionnaires) ---
lyrics_manager = None

# ----------------------------------------------------------------------
# --- CLASSE LyricsManager ---
# ----------------------------------------------------------------------

class LyricsManager:
    """Encapsule toutes les données et la logique de gestion des paroles."""
    def __init__(self, library_path, lines_per_disp):
        self.library_folder_path = library_path
        # Assure que lines_per_display est >= 1 (corrige ValueError)
        self.lines_per_display = max(1, lines_per_disp)
        self.full_song_library = [] 
        self.displayed_songs = []   
        self.song_agenda = []       
        self.current_song_data = {} 
        self.lyrics_blocks = []     
        self.current_index = -1     
        self.current_agenda_index = -1 
        self.current_category = ""
        self.editor_window = None
        self.text_source_name = "" 

        self.load_agenda_from_file()

    # --- Fonctions de Normalisation et de Recherche Avancée (V3.0.0) ---

    def _normalize_text(self, text):
        """Convertit le texte en minuscules et supprime les accents (pour une recherche agnostique)."""
        text = text.lower()
        # Supprime les accents
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text.strip()

    def _get_score(self, song, query_tokens_normalized, query_str_normalized):
        """Calcule un score de pertinence pour une chanson donnée."""
        score = 0
        title_normalized = self._normalize_text(song['title'])
        number_normalized = self._normalize_text(song['number'])
        full_text_normalized = song['lyrics']
        
        # 1. Correspondance de Séquence (Fuzzy Matching/Exacte)
        if query_str_normalized in title_normalized:
            score += 15 
        if query_str_normalized in number_normalized:
            score += 20 

        # 2. Correspondance par Mots-clés (Tokenization & Priorisation)
        tokens_found_in_title = 0
        
        for token in query_tokens_normalized:
            if token in title_normalized:
                tokens_found_in_title += 1
                score += 5 

            if token in full_text_normalized:
                score += 1 
        
        # Bonus si TOUS les mots-clés (non filtrés) sont dans le titre
        if tokens_found_in_title == len(query_tokens_normalized) and len(query_tokens_normalized) > 0:
            score += 10
            
        # 3. Score minimal pour la correspondance simple dans le texte
        if score == 0 and query_str_normalized in full_text_normalized:
             score += 1 

        return score
    
    # --- Gestion de l'Agenda et de la Bibliothèque ---

    def save_agenda_to_file(self):
        try:
            agenda_data_to_save = [{
                "title": song['title'],
                "number": song['number'],
                "path": song['path'],
                "category": song['category']
            } for song in self.song_agenda]

            if not self.library_folder_path:
                print("Impossible de sauvegarder : le chemin de la bibliothèque est vide.")
                return

            filepath = os.path.join(self.library_folder_path, AGENDA_FILE)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(agenda_data_to_save, f, ensure_ascii=False, indent=4)
            print("Agenda sauvegardé manuellement.")
            if self.editor_window and self.editor_window.winfo_exists():
                messagebox.showinfo("Sauvegarde Agenda", "L'agenda a été sauvegardé avec succès.")
        except Exception as e:
            print(f"ERREUR lors de la sauvegarde de l'agenda : {e}")
            if self.editor_window and self.editor_window.winfo_exists():
                messagebox.showerror("Erreur", f"Échec de la sauvegarde de l'agenda : {e}")

    def load_agenda_from_file(self):
        self.song_agenda.clear()
        if not self.library_folder_path or not os.path.isdir(self.library_folder_path): return

        filepath = os.path.join(self.library_folder_path, AGENDA_FILE)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    agenda_lite_data = json.load(f)
                
                print(f"Tentative de chargement de l'agenda (lite data): {len(agenda_lite_data)} entrées.")
                self._agenda_lite_data = agenda_lite_data 

            except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                print(f"Erreur lors du chargement de l'agenda: {e}")
        else:
            print("Aucun fichier d'agenda trouvé. L'agenda est vide.")

    def _reconstitute_agenda(self):
        if not hasattr(self, '_agenda_lite_data'):
            return

        temp_agenda = []
        for lite_song in self._agenda_lite_data:
            found_song = next((s for s in self.full_song_library if s['path'] == lite_song['path']), None)
            if found_song:
                temp_agenda.append(copy.deepcopy(found_song))
            else:
                print(f"Avertissement: Chanson '{lite_song.get('title', 'Inconnu')}' non trouvée. Retirée de l'agenda.")
        
        self.song_agenda = temp_agenda
        del self._agenda_lite_data
        print(f"Agenda reconstitué: {len(self.song_agenda)} chansons.")


    def clear_agenda(self):
        self.song_agenda.clear()
        self.current_agenda_index = -1
        if self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.refresh_agenda_list()

    def load_next_agenda_song(self):
        if not self.song_agenda:
            self.reset_current_song_state()
            return False

        if self.current_agenda_index == -1:
            if self.current_song_data:
                 for i, song in enumerate(self.song_agenda):
                     if song.get('path') == self.current_song_data.get('path'):
                         self.current_agenda_index = i 
                         break
            if self.current_agenda_index == -1:
                self.current_agenda_index = 0
            else:
                self.current_agenda_index += 1
        else:
            self.current_agenda_index += 1

        if self.current_agenda_index < len(self.song_agenda):
            self.load_song(self.song_agenda[self.current_agenda_index])
            return True
        else:
            self.current_agenda_index = max(0, len(self.song_agenda) - 1)
            return False

    def reset_current_song_state(self):
        self.current_song_data = {}
        self.lyrics_blocks = []
        self.current_index = -1
        update_obs_text() 

    def load_song(self, song_dict):
        self.current_song_data = song_dict
        self.lyrics_blocks = []

        for i, full_block_text in enumerate(self.current_song_data.get("blocks", [])):
            all_lines = full_block_text.split('\n')

            for j in range(0, len(all_lines), self.lines_per_display):
                page_lines = all_lines[j : j + self.lines_per_display]
                page_text = "\n".join(page_lines)

                if page_text.strip():
                    self.lyrics_blocks.append({
                        "text": page_text,
                        "is_new_verse": (j == 0),
                        "verse_index": i + 1     
                    })

        self.current_index = 0 if self.lyrics_blocks else -1
        if self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.update_on_song_select()
        update_obs_text()

    def navigate_to(self, index):
        if self.lyrics_blocks:
            self.current_index = max(0, min(index, len(self.lyrics_blocks) - 1))
            update_obs_text()
            if self.editor_window and self.editor_window.winfo_exists():
                self.editor_window.highlight_current_verse()

    def scan_freeshow_library(self, settings):
        self.full_song_library.clear()
        self.load_agenda_from_file()

        if not self.library_folder_path or not os.path.isdir(self.library_folder_path):
            print("Chemin de la bibliothèque invalide ou non défini.")
            return

        print("Scan de la bibliothèque FreeShow (.show) par catégories (dossiers)...")
        start_time = time.time()

        for root, dirs, files in os.walk(self.library_folder_path):
            if root == self.library_folder_path:
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
                        title = song_data.get("name", "Titre inconnu").strip()
                        number = song_data.get("quickAccess", {}).get("number", "-").strip()
                        blocks, full_lyrics_text = [], ""
                        slides = song_data.get("slides", {})

                        for slide_content in slides.values():
                            items = slide_content.get("items", [])
                            slide_text_lines = []
                            if items and "lines" in items[0]:
                                for line in items[0]["lines"]:
                                    line_text = "".join([part.get("value", "") for part in line.get("text", [])])
                                    slide_text_lines.append(line_text)
                            block_text = "\n".join(slide_text_lines)
                            if block_text:
                                blocks.append(block_text)
                                full_lyrics_text += block_text + "\n\n"

                        self.full_song_library.append({
                            "title": title,
                            "number": number,
                            # Le champ 'lyrics' est normalisé pour la recherche intelligente
                            "lyrics": self._normalize_text(full_lyrics_text),
                            "blocks": blocks,
                            "path": filepath,
                            "category": category
                        })
                    except json.JSONDecodeError:
                        print(f" - Erreur JSON (fichier corrompu) pour '{filename}' ({category})")
                    except Exception as e:
                        print(f" - Erreur de lecture/OS pour '{filename}' ({category}): {e}")

        def get_sort_key(song):
            number_str = song.get('number', '').strip()
            try: return int(number_str)
            except ValueError: return float('inf')

        self.full_song_library.sort(key=lambda x: (get_sort_key(x), x['title'].lower()))

        self.displayed_songs = self.full_song_library[:]
        
        self._reconstitute_agenda()

        end_time = time.time()
        print(f"{len(self.full_song_library)} chansons importées en {end_time - start_time:.2f} secondes.")

        if self.editor_window and self.editor_window.winfo_exists():
            self.editor_window.refresh_category_and_song_list()
            self.editor_window.refresh_agenda_list()


# --- Fonctions Globales pour OBS ---

def update_obs_text():
    global lyrics_manager
    if not lyrics_manager: return

    text_to_display = ""
    if 0 <= lyrics_manager.current_index < len(lyrics_manager.lyrics_blocks):
        text_to_display = lyrics_manager.lyrics_blocks[lyrics_manager.current_index]["text"]

    if lyrics_manager.text_source_name:
        source = obs.obs_get_source_by_name(lyrics_manager.text_source_name)
        if source:
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text_to_display)
            obs.obs_source_update(source, settings)
            obs.obs_source_release(source)
            obs.obs_data_release(settings)

    if lyrics_manager.editor_window and lyrics_manager.editor_window.winfo_exists():
         lyrics_manager.editor_window.update_status_bar()

def on_hotkey_pressed(hotkey_id):
    global lyrics_manager
    if lyrics_manager:
        if hotkey_id == "mepc_lyrics_next": lyrics_manager.navigate_to(lyrics_manager.current_index + 1)
        elif hotkey_id == "mepc_lyrics_prev": lyrics_manager.navigate_to(lyrics_manager.current_index - 1)
        elif hotkey_id == "mepc_lyrics_first": lyrics_manager.navigate_to(0)
        elif hotkey_id == "mepc_lyrics_last": lyrics_manager.navigate_to(len(lyrics_manager.lyrics_blocks) - 1)
        elif hotkey_id == HOTKEY_NEXT_AGENDA: lyrics_manager.load_next_agenda_song()

def setup_hotkeys():
    hotkeys = {
        "mepc_lyrics_next": "Mepc_Lyrics: Suivant",
        "mepc_lyrics_prev": "Mepc_Lyrics: Précédent",
        "mepc_lyrics_first": "Mepc_Lyrics: Premier",
        "mepc_lyrics_last": "Mepc_Lyrics: Dernier",
        HOTKEY_NEXT_AGENDA: "Mepc_Lyrics: Prochain Chant de l'Agenda"
    }
    for id, desc in hotkeys.items():
        obs.obs_hotkey_register_frontend(id, desc, lambda p, id=id: on_hotkey_pressed(id) if p else None)

def open_editor_callback(props, prop):
    global lyrics_manager
    if not lyrics_manager:
         print("Erreur: Le LyricsManager n'est pas initialisé.")
         return

    if lyrics_manager.editor_window is None or not lyrics_manager.editor_window.winfo_exists():
        lyrics_manager.editor_window = LyricsEditor(lyrics_manager)
        lyrics_manager.editor_window.protocol("WM_DELETE_WINDOW", lyrics_manager.editor_window.on_closing)
        
        lyrics_manager.editor_window.mainloop()
    else:
        lyrics_manager.editor_window.lift()

# --- Fonctions de Script OBS Standard ---

def script_description(): 
    return """
    <h2>MEPC MONTREAL LYRICS (Gestionnaire de Paroles) V1.0.1</h2>
    <p>Gérez et modifiez votre bibliothèque de chants FreeShow (.show) avec un éditeur moderne qui reste au-dessus d'OBS.</p>
    <p>Ce script a été développé par l'équipe de production de louange de <a href='https://www.mepcmontreal.ca'>www.mepcmontreal.ca</a>.</p>
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
    
    obs.obs_properties_add_button(props, "editor_button", "Ouvrir le Gestionnaire", open_editor_callback)

    return props

def script_load(settings):
    global lyrics_manager
    text_source_name = obs.obs_data_get_string(settings, "text_source")
    library_folder_path = obs.obs_data_get_string(settings, "library_folder")
    
    lines_per_display = max(1, obs.obs_data_get_int(settings, "lines_to_show"))

    lyrics_manager = LyricsManager(library_folder_path, lines_per_display)
    lyrics_manager.text_source_name = text_source_name

    setup_hotkeys()
    lyrics_manager.scan_freeshow_library(settings)
    lyrics_manager.reset_current_song_state()

    print("MEPC MONTREAL LYRICS (V1.0.1) chargé.")

def script_update(settings): 
    global lyrics_manager
    if not lyrics_manager: return

    new_lines_per_display = max(1, obs.obs_data_get_int(settings, "lines_to_show"))
    lines_changed = new_lines_per_display != lyrics_manager.lines_per_display
    lyrics_manager.lines_per_display = new_lines_per_display

    new_folder_path = obs.obs_data_get_string(settings, "library_folder")
    if new_folder_path != lyrics_manager.library_folder_path:
        lyrics_manager.library_folder_path = new_folder_path
        lyrics_manager.scan_freeshow_library(settings)

    lyrics_manager.text_source_name = obs.obs_data_get_string(settings, "text_source")

    if lines_changed:
        if lyrics_manager.current_song_data:
            lyrics_manager.load_song(lyrics_manager.current_song_data)
    
    update_obs_text()

def script_unload(): 
    global lyrics_manager
    if lyrics_manager and lyrics_manager.editor_window and lyrics_manager.editor_window.winfo_exists():
        lyrics_manager.editor_window.after(0, lyrics_manager.editor_window.destroy) 
    print("MEPC MONTREAL LYRICS (V1.0.1) déchargé.")


# ----------------------------------------------------------------------
# --- CLASSE TKINTER POUR L'ÉDITEUR (LyricsEditor) ---
# ----------------------------------------------------------------------

class LyricsEditor(tk.Tk):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.title("Gestionnaire de Louange V1.0.1"); self.geometry("1450x700")

        # Polices
        self.font_main = font.Font(family="Segoe UI", size=10)
        self.font_list = font.Font(family="Segoe UI", size=11)
        self.font_editor = font.Font(family="Consolas", size=11)
        self.font_status = font.Font(family="Segoe UI", size=9)
        
        # Couleurs fixes
        self.bg_default = "#f0f0f0" 
        self.fg_default = "#1f1f1f"
        self.list_bg_default = "#ffffff"
        self.select_bg_default = "#0078d4"
        self.select_fg_default = "#ffffff"
        self.button_bg_default = "#e0e0e0"
        self.button_fg_default = "#1f1f1f"
        self.label_color_default = "#555555"

        # 1. Création des widgets
        self.create_widgets()

        # 2. Application du thème de base (après création)
        self.apply_theme() 

        # 3. Remplissage initial
        self.refresh_category_and_song_list() 
        self.bind_hotkeys() 

    def on_closing(self): 
        self.manager.editor_window = None 
        self.destroy()

    def apply_theme(self, *args):
        bg_color = self.bg_default
        fg_color = self.fg_default
        list_bg = self.list_bg_default
        select_bg = self.select_bg_default
        select_fg = self.select_fg_default
        button_bg = self.button_bg_default
        label_color = self.label_color_default

        self.configure(bg=bg_color)
        
        widgets_to_update = [
            self.control_frame, self.bottom_frame, self.agenda_container_frame,
            self.agenda_frame, self.agenda_button_frame, self.songs_frame,
            self.song_button_frame, self.verses_frame, self.editor_frame,
            self.status_bar, self.agenda_control_frame
        ]

        for w in widgets_to_update:
            if w and w.winfo_exists(): w.config(bg=bg_color)

        self.search_entry.config(bg=list_bg, fg=fg_color, insertbackground=fg_color, highlightcolor=select_bg, highlightbackground=button_bg)
        self.editor_text.config(bg=list_bg, fg=fg_color, insertbackground=fg_color, selectbackground=select_bg, selectforeground=select_fg)
        self.agenda_listbox.config(bg=list_bg, fg=fg_color, selectbackground=select_bg, selectforeground=select_fg)
        self.song_listbox.config(bg=list_bg, fg=fg_color, selectbackground=select_bg, selectforeground=select_fg)
        self.verse_listbox.config(bg=list_bg, fg=fg_color, selectbackground=select_bg, selectforeground=select_fg)
        
        for frame in [self.agenda_container_frame, self.songs_frame, self.verses_frame, self.editor_frame]:
            if frame.winfo_exists(): frame.config(fg=label_color)

        self.status_bar.config(bg=button_bg, fg=fg_color)

        self.update_button_colors(self.control_frame)
        self.update_button_colors(self.bottom_frame)
        self.update_button_colors(self.agenda_button_frame)
        self.update_button_colors(self.song_button_frame)
        self.update_button_colors(self.live_button_frame)
        self.update_button_colors(self.agenda_control_frame)
        
        self.highlight_current_agenda_song() 

    def update_button_colors(self, parent_frame):
        bg = self.button_bg_default
        fg = self.button_fg_default
        active_bg = "#cccccc"
        
        for child in parent_frame.winfo_children():
            if isinstance(child, tk.Button):
                child.config(bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg, relief=tk.FLAT, bd=0)
            elif isinstance(child, tk.Label):
                child.config(bg=self.bg_default, fg=self.label_color_default)
            elif isinstance(child, tk.OptionMenu):
                child.config(bg=bg, fg=fg, activebackground=active_bg, activeforeground=fg)

    def create_widgets(self):
        self.configure(bg=self.bg_default)
        
        # --- Contrôles Supérieurs ---
        self.control_frame = tk.Frame(self, bg=self.bg_default); self.control_frame.pack(fill=tk.X, padx=12, pady=(10,8))
        
        tk.Label(self.control_frame, text="🔍 Rechercher :", bg=self.bg_default, fg=self.label_color_default, font=self.font_main).pack(side=tk.LEFT)
        self.search_var = tk.StringVar(); self.search_var.trace("w", self.on_search_change)
        self.search_entry = tk.Entry(self.control_frame, textvariable=self.search_var, font=self.font_main, relief=tk.SOLID, bd=1, highlightthickness=1); self.search_entry.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=8, ipady=4)

        tk.Label(self.control_frame, text="▶️ Catégorie :", bg=self.bg_default, fg=self.label_color_default, font=self.font_main).pack(side=tk.LEFT, padx=(20, 5))
        self.category_var = tk.StringVar(self); self.category_var.trace("w", self.on_category_change)
        self.category_dropdown = tk.OptionMenu(self.control_frame, self.category_var, "Placeholder")
        self.category_dropdown.config(relief=tk.FLAT, font=self.font_main, padx=10, pady=5, bd=0)
        self.category_dropdown.pack(side=tk.LEFT)

        # --- Barre d'État ---
        self.status_bar = tk.Label(self, text="Prêt | Aucune chanson chargée", anchor=tk.W, font=self.font_status, padx=10, pady=2, bd=0, relief=tk.FLAT)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # --- Barre d'Action Inférieure ---
        self.bottom_frame = tk.Frame(self, bg=self.bg_default); self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(5,0))
        tk.Button(self.bottom_frame, text="💾 Sauvegarder les Modifications", command=self.save_lyrics, relief=tk.FLAT, font=self.font_main, padx=10, pady=5, bd=0).pack(side=tk.RIGHT)

        # --- PanedWindow ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#cccccc", sashwidth=8, sashrelief=tk.FLAT, bd=0);
        main_pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,0))

        # Colonne 1 : Agenda
        self.agenda_container_frame = tk.LabelFrame(main_pane, text="Agenda", bg=self.bg_default, fg=self.label_color_default, font=self.font_main, bd=0, padx=5, pady=5); self.agenda_container_frame.grid_rowconfigure(0, weight=1); self.agenda_container_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(self.agenda_container_frame, width=300, minsize=200)

        self.agenda_frame = tk.Frame(self.agenda_container_frame, bg=self.list_bg_default); self.agenda_frame.grid(row=0, column=0, sticky="nsew")
        self.agenda_listbox = tk.Listbox(self.agenda_frame, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.agenda_listbox.pack(fill=tk.BOTH, expand=True)
        self.agenda_listbox.bind("<Double-Button-1>", self.on_agenda_select)

        self.agenda_button_frame = tk.Frame(self.agenda_container_frame, bg=self.bg_default); self.agenda_button_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        tk.Button(self.agenda_button_frame, text="⬆️", command=self.move_agenda_up, width=3, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT)
        tk.Button(self.agenda_button_frame, text="⬇️", command=self.move_agenda_down, width=3, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT, padx=3)
        tk.Button(self.agenda_button_frame, text="❌ Retirer", command=self.remove_from_agenda, relief=tk.FLAT, font=self.font_main).pack(side=tk.RIGHT)

        self.agenda_control_frame = tk.Frame(self.agenda_container_frame, bg=self.bg_default); self.agenda_control_frame.grid(row=2, column=0, sticky="ew", pady=(5,0))
        tk.Button(self.agenda_control_frame, text="🗑️ Effacer l'Agenda", command=self.manager.clear_agenda, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(self.agenda_control_frame, text="💾 Sauvegarde Manuelle", command=self.manager.save_agenda_to_file, relief=tk.FLAT, font=self.font_main).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Colonne 2 : Chansons Filtrées
        self.songs_frame = tk.LabelFrame(main_pane, text="Liste des Chansons", bg=self.bg_default, fg=self.label_color_default, font=self.font_main, bd=0, padx=5, pady=5); self.songs_frame.grid_rowconfigure(0, weight=1); self.songs_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(self.songs_frame, width=350, minsize=200)
        self.song_listbox = tk.Listbox(self.songs_frame, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.song_listbox.grid(row=0, column=0, sticky="nsew"); self.song_listbox.bind("<<ListboxSelect>>", self.on_song_select)
        self.song_listbox.bind("<Double-Button-1>", self.add_to_agenda)

        self.song_button_frame = tk.Frame(self.songs_frame, bg=self.bg_default); self.song_button_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        tk.Button(self.song_button_frame, text="➕ Ajouter à l'Agenda", command=self.add_to_agenda_button, relief=tk.FLAT, font=self.font_main).pack(fill=tk.X)

        # Colonne 3 : Couplets
        self.verses_frame = tk.LabelFrame(main_pane, text="Couplets", bg=self.bg_default, fg=self.label_color_default, font=self.font_main, bd=0, padx=5, pady=5); self.verses_frame.grid_rowconfigure(0, weight=1); self.verses_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(self.verses_frame, width=300, minsize=150)
        self.verse_listbox = tk.Listbox(self.verses_frame, font=self.font_list, relief=tk.SOLID, bd=1, highlightthickness=0, activestyle='none', exportselection=False); self.verse_listbox.grid(row=0, column=0, sticky="nsew"); self.verse_listbox.bind("<<ListboxSelect>>", self.on_verse_select)

        self.live_button_frame = tk.Frame(self.verses_frame, bg=self.bg_default); self.live_button_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        tk.Button(self.live_button_frame, text="|<", command=lambda: self.manager.navigate_to(0), width=3, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT)
        tk.Button(self.live_button_frame, text="<", command=lambda: self.manager.navigate_to(self.manager.current_index - 1), width=3, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT, padx=3)
        tk.Button(self.live_button_frame, text=">", command=lambda: self.manager.navigate_to(self.manager.current_index + 1), width=3, relief=tk.FLAT, font=self.font_main).pack(side=tk.LEFT, padx=(3, 10))
        tk.Button(self.live_button_frame, text="Prochain Chant (F1)", command=self.manager.load_next_agenda_song, relief=tk.FLAT, font=self.font_main).pack(side=tk.RIGHT)

        # Colonne 4 : Éditeur
        self.editor_frame = tk.LabelFrame(main_pane, text="Éditeur de Texte", bg=self.bg_default, fg=self.label_color_default, font=self.font_main, bd=0, padx=5, pady=5); self.editor_frame.grid_rowconfigure(0, weight=1); self.editor_frame.grid_columnconfigure(0, weight=1)
        main_pane.add(self.editor_frame, width=350, minsize=300)
        self.editor_text = tk.Text(self.editor_frame, wrap=tk.WORD, font=self.font_editor, relief=tk.SOLID, bd=1, highlightthickness=0, undo=True, padx=8, pady=8); 
        self.editor_text.grid(row=0, column=0, sticky="nsew")

    # --- Reste des méthodes ---
    def toggle_theme(self):
        pass 

    def update_status_bar(self):
        status_text = "Prêt | Aucune chanson chargée"
        if self.manager.current_song_data and self.manager.current_index != -1:
            song_title = self.manager.current_song_data.get('title', 'Chant Inconnu')
            current = self.manager.current_index + 1
            total = len(self.manager.lyrics_blocks)
            verse_index = self.manager.lyrics_blocks[self.manager.current_index]["verse_index"] if self.manager.current_index >= 0 else 0

            agenda_info = ""
            if self.manager.current_agenda_index >= 0:
                agenda_info = f" (Agenda {self.manager.current_agenda_index + 1}/{len(self.manager.song_agenda)})"
            
            status_text = f"ACTIF: {song_title}{agenda_info} | Couplet {verse_index} | Page {current}/{total}"
            
        self.status_bar.config(text=status_text)
        self.highlight_current_agenda_song() 

    def get_categories(self):
        categories = sorted(list(set(song['category'] for song in self.manager.full_song_library)))
        return categories

    def refresh_category_and_song_list(self):
        menu = self.category_dropdown["menu"]
        menu.delete(0, "end")
        new_categories = self.get_categories()
        for category in new_categories:
            menu.add_command(label=category, command=lambda value=category: self.category_var.set(value))

        if self.category_var.get() not in new_categories or not new_categories:
            new_default = new_categories[0] if new_categories else ""
            self.category_var.set(new_default)
            self.manager.current_category = new_default

        # Déclenche la recherche intelligente
        self.filter_songs_by_category()
        self.refresh_song_list()
        self.refresh_agenda_list()

    def on_category_change(self, *args):
        self.manager.current_category = self.category_var.get()
        # Filtrage intelligent
        self.filter_songs_by_category()
        self.refresh_song_list()
        self.search_var.set("")

    def filter_songs_by_category(self):
        # Cette fonction implémente la recherche intelligente
        query = self.search_var.get()
        
        # 1. Filtre initial par catégorie
        filtered_by_category = [song for song in self.manager.full_song_library if song['category'] == self.manager.current_category]

        if not query:
            self.manager.displayed_songs = filtered_by_category[:]
            return

        # 2. Préparation de la requête pour la tokenization et la normalisation
        query_normalized = self.manager._normalize_text(query)
        # 5. Filtrage des Mots Vides (Stop Words)
        stop_words = ["le", "la", "les", "un", "une", "de", "du", "à", "et", "ou", "mais"] 
        query_tokens = [t for t in query_normalized.split() if t not in stop_words and len(t) > 1]
        
        if not query_tokens: query_tokens = [query_normalized] 

        results_with_score = []

        for song in filtered_by_category:
            # 3. et 4. Correspondance et Priorisation
            score = self.manager._get_score(song, query_tokens, query_normalized)
            
            if score > 0:
                results_with_score.append((score, song))
        
        # Tri par score (décroissant) puis par titre
        results_with_score.sort(key=lambda x: (x[0], x[1]['title'].lower()), reverse=True)
        self.manager.displayed_songs = [song for score, song in results_with_score]


    def on_search_change(self, *args):
        # Déclenche le filtrage intelligent
        self.filter_songs_by_category()
        self.refresh_song_list()

    def refresh_song_list(self):
        self.song_listbox.delete(0, tk.END)
        for song in self.manager.displayed_songs:
            number_display = f"{song['number']} - " if song['number'] and song['number'] != '-' else ""
            self.song_listbox.insert(tk.END, f" {number_display}{song['title']}")

    def on_song_select(self, event):
        selection = event.widget.curselection()
        if selection:
            song_index_in_displayed_list = selection[0]
            selected_song = self.manager.displayed_songs[song_index_in_displayed_list]
            self.manager.load_song(selected_song)
            self.manager.current_agenda_index = -1 
            self.highlight_current_agenda_song() 


    def refresh_agenda_list(self):
        self.agenda_listbox.delete(0, tk.END)
        for i, song in enumerate(self.manager.song_agenda):
            self.agenda_listbox.insert(tk.END, f"{i+1:02d}. [{song['category']}] {song['number']} - {song['title']}")
        self.highlight_current_agenda_song() 

    def add_to_agenda(self, event): self.add_to_agenda_button()

    def add_to_agenda_button(self):
        selection = self.song_listbox.curselection()
        if selection:
            song_index = selection[0]
            selected_song = self.manager.displayed_songs[song_index]
            self.manager.song_agenda.append(copy.deepcopy(selected_song))
            self.refresh_agenda_list()

    def on_agenda_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            selected_song = self.manager.song_agenda[index]
            self.manager.current_agenda_index = index 
            self.manager.load_song(selected_song)
            self.song_listbox.selection_clear(0, tk.END) 
            self.highlight_current_agenda_song()

    def remove_from_agenda(self):
        selection = self.agenda_listbox.curselection()
        if selection:
            index = selection[0]
            if index == self.manager.current_agenda_index: 
                self.manager.current_agenda_index = -1 
                self.manager.reset_current_song_state()
            
            del self.manager.song_agenda[index]
            if self.manager.current_agenda_index > index: self.manager.current_agenda_index -= 1 
            self.refresh_agenda_list()

    def move_agenda_up(self):
        selection = self.agenda_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            song = self.manager.song_agenda.pop(index)
            self.manager.song_agenda.insert(index - 1, song)
            if self.manager.current_agenda_index == index: self.manager.current_agenda_index -= 1
            elif self.manager.current_agenda_index == index - 1: self.manager.current_agenda_index += 1
            self.refresh_agenda_list()
            self.agenda_listbox.selection_set(index - 1); self.agenda_listbox.activate(index - 1)

    def move_agenda_down(self):
        selection = self.agenda_listbox.curselection()
        if selection and selection[0] < len(self.manager.song_agenda) - 1:
            index = selection[0]
            song = self.manager.song_agenda.pop(index)
            self.manager.song_agenda.insert(index + 1, song)
            if self.manager.current_agenda_index == index: self.manager.current_agenda_index += 1
            elif self.manager.current_agenda_index == index + 1: self.manager.current_agenda_index -= 1
            self.refresh_agenda_list()
            self.agenda_listbox.selection_set(index + 1); self.agenda_listbox.activate(index + 1)

    def highlight_current_agenda_song(self):
        for i in range(self.agenda_listbox.size()):
            self.agenda_listbox.itemconfig(i, {'bg': self.list_bg_default, 'fg': self.fg_default})

        if 0 <= self.manager.current_agenda_index < len(self.manager.song_agenda):
            self.agenda_listbox.itemconfig(self.manager.current_agenda_index, {'bg': '#2E8B57', 'fg': 'white'}) 
            self.agenda_listbox.see(self.manager.current_agenda_index)


    def update_on_song_select(self):
        self.update_verse_list()
        self.editor_text.delete('1.0', tk.END)
        full_text = "\n\n".join(self.manager.current_song_data.get("blocks", []))
        self.editor_text.insert('1.0', full_text)
        self.update_status_bar() 

    def update_verse_list(self):
        self.verse_listbox.delete(0, tk.END)
        
        verse_fg = "#B8860B"  # Or foncé
        default_fg = self.fg_default

        for i, page_data in enumerate(self.manager.lyrics_blocks):
            preview = page_data["text"].split('\n')[0]
            
            if page_data["is_new_verse"]:
                prefix = f" Verse {page_data['verse_index']:02d} | "
                self.verse_listbox.insert(tk.END, f"{prefix}{preview}")
                # Correction stable : Utilisation de itemconfig avec SEULEMENT fg (couleur)
                self.verse_listbox.itemconfig(i, fg=verse_fg) 
            else:
                prefix = f"    - Page {i+1:02d} | "
                self.verse_listbox.insert(tk.END, f"{prefix}{preview}")
                self.verse_listbox.itemconfig(i, fg=default_fg)

        self.highlight_current_verse()

    def on_verse_select(self, event):
        selection = event.widget.curselection()
        if selection: self.manager.navigate_to(selection[0])

    def highlight_current_verse(self):
        self.verse_listbox.selection_clear(0, tk.END)
        if 0 <= self.manager.current_index < self.verse_listbox.size():
            self.verse_listbox.selection_set(self.manager.current_index)
            self.verse_listbox.activate(self.manager.current_index)
            self.verse_listbox.see(self.manager.current_index)

    def bind_hotkeys(self):
        self.bind('<Right>', lambda event: self.manager.navigate_to(self.manager.current_index + 1))
        self.bind('<Left>', lambda event: self.manager.navigate_to(self.manager.current_index - 1))
        self.bind('<Up>', lambda event: self.manager.navigate_to(0)) 
        self.bind('<Down>', lambda event: self.manager.navigate_to(len(self.manager.lyrics_blocks) - 1)) 
        self.bind('<F1>', lambda event: self.manager.load_next_agenda_song())

    def save_lyrics(self):
        if not self.manager.current_song_data or not self.manager.current_song_data.get("path"):
            messagebox.showwarning("Sauvegarde", "Aucune chanson sélectionnée pour la sauvegarde.")
            return

        filepath = self.manager.current_song_data["path"]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_data = json.load(f)

            edited_text = self.editor_text.get("1.0", tk.END).strip()
            new_blocks = edited_text.split('\n\n')

            new_slides = {}
            slide_ids = list(original_data[1]["slides"].keys())

            for i, block in enumerate(new_blocks):
                slide_id = slide_ids[i] if i < len(slide_ids) else f"newslide_{int(time.time())}_{i}"
                lines_data = [{"align": "", "text": [{"style": "", "value": line_text}]} for line_text in block.split('\n')]

                slide_template = original_data[1]["slides"].get(slide_id, {"group": "", "color": None, "settings": {}, "notes": "", "globalGroup": "verse"})
                slide_template["items"] = [{"style": "top:120px;left:50px;height:840px;width:1820px;", "lines": lines_data}]
                new_slides[slide_id] = slide_template

            original_data[1]["slides"] = new_slides
            
            for layout_content in original_data[1]["layouts"].values():
                layout_content["slides"] = [{"id": sid} for sid in new_slides.keys()]

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, ensure_ascii=False, separators=(',', ':'))

            messagebox.showinfo("Sauvegarde", f"Chanson '{os.path.basename(filepath)}' sauvegardée avec succès.")

            current_title = self.manager.current_song_data.get('title')
            
            def dummy_settings():
                return obs.obs_data_create()
            
            self.manager.scan_freeshow_library(dummy_settings())

            updated_song = next((s for s in self.manager.full_song_library if s["title"] == current_title), None)
            if updated_song:
                self.manager.load_song(updated_song)
                
            self.refresh_agenda_list() 

        except Exception as e:
            messagebox.showerror("Erreur de Sauvegarde", f"ERREUR lors de la sauvegarde du fichier '{filepath}': {e}")
            print(f"ERREUR lors de la sauvegarde du fichier '{filepath}': {e}")
