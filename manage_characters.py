import os
import re
import json
import shutil
import urllib.request
import urllib.parse
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading

# Color Scheme
BG_DARK = "#121214"
BG_CARD = "#1a1a1e"
BG_LIST = "#0e0e10"
ACCENT_COLOR = "#ffcc00"  # OKE GAS Kombat Yellow
ACCENT_HOVER = "#e6b800"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#8e8e93"
RED_COLOR = "#ff453a"
RED_HOVER = "#d63b30"
GREEN_COLOR = "#30d158"

class CharacterManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OKE GAS KOMBAT - Pengelola Karakter")
        self.root.geometry("1150x720")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        # Path Setup
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.char_dir = os.path.join(self.project_dir, "char")
        self.js_file = os.path.join(self.project_dir, "characters.js")

        # Load characters
        self.characters = self.load_characters_list()
        self.preview_images = {}  # Cache PhotoImage references
        self.current_key = None

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('.', background=BG_DARK, foreground=TEXT_WHITE)
        self.style.configure('TFrame', background=BG_DARK)
        self.style.configure('Card.TFrame', background=BG_CARD)

        # Build UI
        self.create_widgets()

        # Select first character if available
        if self.characters:
            self.listbox.selection_set(0)
            self.on_select(None)

    def load_characters_list(self):
        """Membaca dan memparsing data karakter dari characters.js"""
        if not os.path.exists(self.js_file):
            return {}
        
        try:
            with open(self.js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ekstrak objek javascript di antara chars = { ... }
            match = re.search(r'const\s+chars\s*=\s*(\{.*\});', content, re.DOTALL)
            if not match:
                return {}
            
            js_obj = match.group(1)
            
            # Format manual agar menjadi JSON valid
            # 1. Tambahkan double quotes pada keys (e.g. name: -> "name":)
            json_str = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', js_obj)
            
            # 2. Ubah single quotes ke double quotes pada strings
            def repl(m):
                s = m.group(1)
                s_escaped = s.replace('"', '\\"')
                return f'"{s_escaped}"'
            json_str = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", repl, json_str)
            
            # 3. Hapus koma terakhir sebelum closing curly brace
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            
            return json.loads(json_str)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca atau memparsing characters.js:\n{str(e)}")
            return {}

    def save_characters_list(self):
        """Menyimpan data karakter kembali ke characters.js"""
        try:
            content = "const chars = {\n"
            for char_key, char_data in self.characters.items():
                content += f"    {char_key}: {{\n"
                for attr_key, attr_val in char_data.items():
                    if isinstance(attr_val, str):
                        content += f"        {attr_key}: '{attr_val}',\n"
                    else:
                        content += f"        {attr_key}: {attr_val},\n"
                # Strip last comma
                content = content.rstrip(",\n") + "\n"
                content += "    },\n"
            # Strip last character comma
            if self.characters:
                content = content.rstrip(",\n") + "\n"
            content += "};\n"

            with open(self.js_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menulis ke characters.js:\n{str(e)}")
            return False

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg=BG_DARK, height=75)
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame, 
            text="OKE GAS KOMBAT", 
            font=("Impact", 28), 
            fg=ACCENT_COLOR, 
            bg=BG_DARK
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(
            header_frame, 
            text=" - Character Config Manager", 
            font=("Helvetica", 14, "italic"), 
            fg=TEXT_MUTED, 
            bg=BG_DARK
        )
        subtitle_label.pack(side=tk.LEFT, pady=(12, 0))

        # Main Layout
        main_frame = tk.Frame(self.root, bg=BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Left Column (List of characters and Actions)
        left_frame = tk.Frame(main_frame, bg=BG_CARD, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_frame.pack_propagate(False)

        tk.Label(
            left_frame, 
            text="Petarung", 
            font=("Helvetica", 12, "bold"), 
            fg=TEXT_WHITE, 
            bg=BG_CARD
        ).pack(anchor=tk.W, padx=15, pady=(15, 5))

        list_container = tk.Frame(left_frame, bg=BG_LIST)
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_container, 
            bg=BG_LIST, 
            fg=TEXT_WHITE, 
            selectbackground=ACCENT_COLOR, 
            selectforeground=BG_DARK,
            font=("Helvetica", 11, "bold"), 
            bd=0, 
            highlightthickness=0,
            exportselection=False,
            yscrollcommand=self.scrollbar.set
        )
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        self.refresh_listbox()

        # Left Column Buttons
        btn_frame = tk.Frame(left_frame, bg=BG_CARD)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        self.add_btn = tk.Button(
            btn_frame, 
            text="➕ TAMBAH KARAKTER", 
            bg=GREEN_COLOR, 
            fg=TEXT_WHITE,
            activebackground=GREEN_COLOR,
            activeforeground=TEXT_WHITE,
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            relief="flat", 
            height=2,
            command=self.open_add_character_dialog
        )
        self.add_btn.pack(fill=tk.X, pady=5)

        self.delete_btn = tk.Button(
            btn_frame, 
            text="🗑️ HAPUS KARAKTER", 
            bg=RED_COLOR, 
            fg=TEXT_WHITE,
            activebackground=RED_HOVER,
            activeforeground=TEXT_WHITE,
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            relief="flat", 
            height=2,
            command=self.delete_character
        )
        self.delete_btn.pack(fill=tk.X, pady=5)

        # Right Column (Scrollable Form)
        right_frame = tk.Frame(main_frame, bg=BG_CARD)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Canvas & Scrollbar for Form to ensure all fits on small screens
        form_canvas = tk.Canvas(right_frame, bg=BG_CARD, bd=0, highlightthickness=0)
        form_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=form_canvas.yview)
        self.scrollable_form = tk.Frame(form_canvas, bg=BG_CARD)

        self.scrollable_form.bind(
            "<Configure>",
            lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all"))
        )
        form_canvas.create_window((0, 0), window=self.scrollable_form, anchor="nw")
        form_canvas.configure(yscrollcommand=form_scrollbar.set)

        form_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Build inside scrollable form
        # Form Container divided into stats form and image fields
        self.build_form(self.scrollable_form)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for key, char in self.characters.items():
            name = char.get("name", key.upper())
            self.listbox.insert(tk.END, f"  {name} ({key})")

    def build_form(self, container):
        # Master container to hold stats on left, previews on right
        form_grid = tk.Frame(container, bg=BG_CARD)
        form_grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        form_grid.columnconfigure(0, weight=3) # Form input
        form_grid.columnconfigure(1, weight=2) # Previews

        # ------------------ LEFT SIDE: STATS FORM ------------------
        left_side = tk.Frame(form_grid, bg=BG_CARD)
        left_side.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        tk.Label(
            left_side, 
            text="STATUS & IDENTITAS", 
            font=("Helvetica", 12, "bold"), 
            fg=ACCENT_COLOR, 
            bg=BG_CARD
        ).pack(anchor=tk.W, pady=(0, 10))

        # Inputs helper
        self.inputs = {}

        # 1. Key & Nama
        identitas_frame = tk.Frame(left_side, bg=BG_CARD)
        identitas_frame.pack(fill=tk.X, pady=5)
        identitas_frame.columnconfigure(0, weight=1)
        identitas_frame.columnconfigure(1, weight=1)

        # Key (ID)
        key_box = tk.Frame(identitas_frame, bg=BG_CARD)
        key_box.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Label(key_box, text="ID Karakter (e.g. balil):", fg=TEXT_MUTED, bg=BG_CARD).pack(anchor=tk.W)
        self.inputs["key"] = tk.Entry(key_box, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", state="disabled", font=("Helvetica", 10))
        self.inputs["key"].pack(fill=tk.X, ipady=4, pady=2)

        # Name
        name_box = tk.Frame(identitas_frame, bg=BG_CARD)
        name_box.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        tk.Label(name_box, text="Nama Karakter (e.g. BALIL):", fg=TEXT_MUTED, bg=BG_CARD).pack(anchor=tk.W)
        self.inputs["name"] = tk.Entry(name_box, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", font=("Helvetica", 10))
        self.inputs["name"].pack(fill=tk.X, ipady=4, pady=2)

        # 2. Stats (Speed, Damage, UnlockWins, Punch Duration, Knockback, Knockback Delay)
        stats_frame = tk.Frame(left_side, bg=BG_CARD)
        stats_frame.pack(fill=tk.X, pady=10)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)

        # Speed
        self.add_stat_input(stats_frame, "Kecepatan (speed):", "speed", 0, 0)
        # Damage
        self.add_stat_input(stats_frame, "Damage Pukulan:", "damage", 0, 1)
        # UnlockWins
        self.add_stat_input(stats_frame, "Syarat Menang (Lock):", "unlockWins", 0, 2)
        # Punch Duration
        self.add_stat_input(stats_frame, "Durasi Pukul (ms):", "punchDuration", 1, 0)
        # Knockback
        self.add_stat_input(stats_frame, "Knockback Jarak:", "knockback", 1, 1, is_float=True)
        # Knockback Delay
        self.add_stat_input(stats_frame, "Knockback Delay (ms):", "knockbackDelay", 1, 2)

        # 3. Image Paths inputs
        tk.Label(
            left_side, 
            text="ASET GAMBAR", 
            font=("Helvetica", 12, "bold"), 
            fg=ACCENT_COLOR, 
            bg=BG_CARD
        ).pack(anchor=tk.W, pady=(15, 5))

        self.add_image_input(left_side, "Gambar Kartu Seleksi (Card):", "card")
        self.add_image_input(left_side, "Gambar Diam (Stance Stance):", "stance")
        self.add_image_input(left_side, "Gambar Berlari (Run Animation):", "run")
        self.add_image_input(left_side, "Gambar Memukul (Punch Animation):", "punch")

        # Submit Button
        self.save_btn = tk.Button(
            left_side,
            text="💾 SIMPAN PERUBAHAN KARAKTER",
            bg=ACCENT_COLOR,
            fg=BG_DARK,
            font=("Helvetica", 11, "bold"),
            activebackground=ACCENT_HOVER,
            activeforeground=BG_DARK,
            bd=0,
            relief="flat",
            height=2,
            command=self.save_character_changes
        )
        self.save_btn.pack(fill=tk.X, pady=(25, 0))

        # ------------------ RIGHT SIDE: IMAGE PREVIEWS ------------------
        right_side = tk.Frame(form_grid, bg=BG_CARD)
        right_side.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            right_side, 
            text="PRATINJAU GAMBAR (2x2)", 
            font=("Helvetica", 12, "bold"), 
            fg=TEXT_WHITE, 
            bg=BG_CARD
        ).pack(anchor=tk.CENTER, pady=(0, 10))

        grid_preview = tk.Frame(right_side, bg=BG_CARD)
        grid_preview.pack(fill=tk.BOTH, expand=True)
        grid_preview.columnconfigure(0, weight=1)
        grid_preview.columnconfigure(1, weight=1)

        self.previews = {}
        self.build_preview_box(grid_preview, "Card Preview", "card", 0, 0)
        self.build_preview_box(grid_preview, "Stance Preview", "stance", 0, 1)
        self.build_preview_box(grid_preview, "Run Preview", "run", 1, 0)
        self.build_preview_box(grid_preview, "Punch Preview", "punch", 1, 1)

    def add_stat_input(self, parent, label_text, key, row, col, is_float=False):
        box = tk.Frame(parent, bg=BG_CARD)
        box.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
        tk.Label(box, text=label_text, fg=TEXT_MUTED, bg=BG_CARD, font=("Helvetica", 9)).pack(anchor=tk.W)
        
        entry = tk.Entry(box, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", font=("Helvetica", 10))
        entry.pack(fill=tk.X, ipady=4, pady=2)
        self.inputs[key] = entry

    def add_image_input(self, parent, label_text, key):
        box = tk.Frame(parent, bg=BG_CARD)
        box.pack(fill=tk.X, pady=6)

        tk.Label(box, text=label_text, fg=TEXT_MUTED, bg=BG_CARD, font=("Helvetica", 9)).pack(anchor=tk.W)

        row_frame = tk.Frame(box, bg=BG_CARD)
        row_frame.pack(fill=tk.X, pady=2)
        row_frame.columnconfigure(0, weight=1)

        entry = tk.Entry(row_frame, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", font=("Helvetica", 9))
        entry.grid(row=0, column=0, sticky="ew", ipady=4)
        self.inputs[key] = entry

        # Browse button
        browse = tk.Button(
            row_frame, 
            text="Cari File...", 
            bg="#3a3a3c", 
            fg=TEXT_WHITE, 
            font=("Helvetica", 8, "bold"),
            activebackground="#2c2c2e", 
            activeforeground=TEXT_WHITE, 
            bd=0, 
            relief="flat", 
            padx=8,
            command=lambda: self.browse_image(key)
        )
        browse.grid(row=0, column=1, padx=(8, 0))

        # Preview refresh button
        refresh = tk.Button(
            row_frame, 
            text="🔄 Preview", 
            bg="#3a3a3c", 
            fg=TEXT_WHITE, 
            font=("Helvetica", 8, "bold"),
            activebackground="#2c2c2e", 
            activeforeground=TEXT_WHITE, 
            bd=0, 
            relief="flat", 
            padx=8,
            command=lambda: self.refresh_single_preview(key)
        )
        refresh.grid(row=0, column=2, padx=(5, 0))

    def build_preview_box(self, parent, label_text, key, row, col):
        frame = tk.Frame(parent, bg=BG_CARD, bd=1, relief="solid", highlightcolor="#2b2b36")
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        tk.Label(frame, text=label_text, fg=TEXT_MUTED, bg=BG_CARD, font=("Helvetica", 9, "bold")).pack(pady=2)

        canvas = tk.Canvas(frame, bg=BG_LIST, height=130, width=150, bd=0, highlightthickness=0)
        canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.previews[key] = canvas

    def browse_image(self, key):
        file_path = filedialog.askopenfilename(
            title="Pilih Aset Karakter",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp"), ("All Files", "*.*")]
        )
        if file_path:
            self.inputs[key].delete(0, tk.END)
            self.inputs[key].insert(0, file_path)
            self.refresh_single_preview(key)

    def refresh_single_preview(self, key):
        """Memuat gambar pratinjau tunggal pada canvas terkait"""
        val = self.inputs[key].get().strip()
        canvas = self.previews[key]
        canvas.delete("all")

        if not val:
            canvas.create_text(75, 65, text="Kosong", fill=TEXT_MUTED, font=("Helvetica", 10))
            return

        # Cek jika berupa URL atau path lokal
        is_url = val.startswith(("http://", "https://"))
        
        if is_url:
            canvas.create_text(75, 65, text="🌐 URL Link\n(Download Dulu)", fill=ACCENT_COLOR, justify=tk.CENTER, font=("Helvetica", 9))
            return

        full_path = val if os.path.isabs(val) else os.path.join(self.project_dir, val)

        if not os.path.exists(full_path):
            canvas.create_text(75, 65, text="⚠️ Tidak Ditemukan", fill=RED_COLOR, font=("Helvetica", 9))
            return

        try:
            img = Image.open(full_path)
            # Resize
            img.thumbnail((140, 110), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Cache reference
            self.preview_images[key] = photo

            canvas.create_image(75, 65, image=photo, anchor=tk.CENTER)
        except Exception as e:
            canvas.create_text(75, 65, text="Error Load", fill=RED_COLOR, font=("Helvetica", 9))

    def on_select(self, event):
        """Ketika karakter dipilih dari daftar"""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        # Dapatkan key dari baris terpilih
        keys = list(self.characters.keys())
        self.current_key = keys[index]
        char = self.characters[self.current_key]

        # Reset states
        self.inputs["key"].config(state="normal")
        self.inputs["key"].delete(0, tk.END)
        self.inputs["key"].insert(0, self.current_key)
        self.inputs["key"].config(state="disabled")

        # Fill inputs
        self.fill_field("name", char.get("name", ""))
        self.fill_field("speed", str(char.get("speed", 0)))
        self.fill_field("damage", str(char.get("damage", 0)))
        self.fill_field("unlockWins", str(char.get("unlockWins", 0)))
        self.fill_field("punchDuration", str(char.get("punchDuration", 0)))
        self.fill_field("knockback", str(char.get("knockback", 0)))
        self.fill_field("knockbackDelay", str(char.get("knockbackDelay", 0)))

        self.fill_field("card", char.get("card", ""))
        self.fill_field("stance", char.get("stance", ""))
        self.fill_field("run", char.get("run", ""))
        self.fill_field("punch", char.get("punch", ""))

        # Refresh previews
        for k in ["card", "stance", "run", "punch"]:
            self.refresh_single_preview(k)

    def fill_field(self, key, value):
        self.inputs[key].delete(0, tk.END)
        self.inputs[key].insert(0, value)

    def open_add_character_dialog(self):
        """Membuka pop-up kecil untuk memasukkan ID karakter baru"""
        NewCharacterDialog(self.root, self.add_character_callback)

    def add_character_callback(self, key_id):
        key_id = key_id.lower().strip()
        if not key_id or not re.match(r'^[a-zA-Z0-9_]+$', key_id):
            messagebox.showerror("Error", "ID Karakter tidak valid! Hanya huruf, angka, dan underscore.")
            return

        if key_id in self.characters:
            messagebox.showerror("Error", f"Karakter dengan ID '{key_id}' sudah ada!")
            return

        # Daftarkan karakter kosong baru
        self.characters[key_id] = {
            "name": key_id.upper(),
            "card": f"char/{key_id}/{key_id}-card.webp",
            "stance": f"char/{key_id}/{key_id}-stance.webp",
            "run": f"char/{key_id}/{key_id}-run.webp",
            "punch": f"char/{key_id}/{key_id}-punch.webp",
            "speed": 10,
            "punchDuration": 600,
            "damage": 5,
            "knockback": 0.5,
            "knockbackDelay": 100,
            "unlockWins": 0
        }

        # Simpan
        if self.save_characters_list():
            # Refresh listbox dan arahkan ke item baru
            self.refresh_listbox()
            keys = list(self.characters.keys())
            idx = keys.index(key_id)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.on_select(None)
            
            # Buat foldernya
            folder_path = os.path.join(self.char_dir, key_id)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            messagebox.showinfo("Sukses", f"Karakter '{key_id}' berhasil ditambahkan ke daftar. Silakan lengkapi status dan berkas gambar di sebelah kanan.")

    def delete_character(self):
        """Menghapus karakter yang dipilih"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Peringatan", "Silakan pilih karakter yang ingin dihapus terlebih dahulu!")
            return

        index = selection[0]
        keys = list(self.characters.keys())
        key_id = keys[index]
        char_name = self.characters[key_id].get("name", key_id)

        confirm = messagebox.askyesno(
            "Konfirmasi Hapus", 
            f"Apakah Anda yakin ingin menghapus karakter '{char_name}' ({key_id})?\n\nFolder aset 'char/{key_id}' beserta seluruh isinya juga akan dihapus permanen!"
        )
        if not confirm:
            return

        # Hapus folder aset
        folder_path = os.path.join(self.char_dir, key_id)
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
        except Exception as e:
            messagebox.showwarning("Peringatan", f"Data terhapus dari daftar, namun gagal menghapus folder fisik:\n{str(e)}")

        # Hapus dari dictionary
        del self.characters[key_id]

        if self.save_characters_list():
            self.refresh_listbox()
            self.current_key = None
            # Clear inputs
            for entry in self.inputs.values():
                entry.config(state="normal")
                entry.delete(0, tk.END)
            self.inputs["key"].config(state="disabled")

            # Clear previews
            for canvas in self.previews.values():
                canvas.delete("all")

            # Pilih item pertama jika tersisa
            if self.characters:
                self.listbox.selection_set(0)
                self.on_select(None)
            
            messagebox.showinfo("Sukses", "Karakter berhasil dihapus!")

    def save_character_changes(self):
        """Menyimpan perubahan status dan memproses aset gambar (salin / unduh)"""
        if not self.current_key:
            messagebox.showwarning("Peringatan", "Tidak ada karakter yang sedang dipilih!")
            return

        # Kumpulkan nilai status & konversi tipe datanya
        try:
            name = self.inputs["name"].get().strip()
            speed = int(self.inputs["speed"].get().strip())
            damage = int(self.inputs["damage"].get().strip())
            unlockWins = int(self.inputs["unlockWins"].get().strip())
            punchDuration = int(self.inputs["punchDuration"].get().strip())
            knockback = float(self.inputs["knockback"].get().strip())
            knockbackDelay = int(self.inputs["knockbackDelay"].get().strip())
        except ValueError as e:
            messagebox.showerror("Error", "Nilai status tidak valid! Pastikan tipe data benar (Kecepatan, Damage, Menang, Durasi, Delay berupa Integer; Knockback berupa Float).")
            return

        if not name:
            messagebox.showerror("Error", "Nama karakter tidak boleh kosong!")
            return

        # Validasi berkas gambar
        image_inputs = {
            "card": self.inputs["card"].get().strip(),
            "stance": self.inputs["stance"].get().strip(),
            "run": self.inputs["run"].get().strip(),
            "punch": self.inputs["punch"].get().strip()
        }

        # Cek jika ada input gambar yang kosong
        for img_key, val in image_inputs.items():
            if not val:
                messagebox.showerror("Error", f"Kolom gambar '{img_key}' tidak boleh kosong!")
                return

        # Folder aset karakter
        char_dest_dir = os.path.join(self.char_dir, self.current_key)
        if not os.path.exists(char_dest_dir):
            os.makedirs(char_dest_dir)

        # Loading window untuk memproses gambar
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Memproses...")
        loading_window.geometry("320x150")
        loading_window.configure(bg=BG_DARK)
        loading_window.transient(self.root)
        loading_window.grab_set()

        # Center loading
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        loading_window.geometry(f"+{int(main_x + main_w/2 - 160)}+{int(main_y + main_h/2 - 75)}")

        status_lbl = tk.Label(
            loading_window, 
            text="Sedang memproses aset gambar...\nMohon tunggu sebentar.", 
            fg=TEXT_WHITE, 
            bg=BG_DARK,
            font=("Helvetica", 10)
        )
        status_lbl.pack(pady=20)
        
        progress = ttk.Progressbar(loading_window, mode='indeterminate')
        progress.pack(fill=tk.X, padx=30)
        progress.start(10)

        # Worker thread
        def worker():
            final_paths = {}
            for img_key, path_or_url in image_inputs.items():
                # Jika sudah berupa target relative path yang valid, tidak perlu dicopy/diunduh lagi
                expected_rel = f"char/{self.current_key}/{self.current_key}-{img_key}"
                
                # Cek jika path_or_url adalah file di folder tujuan
                if path_or_url.replace("\\", "/").startswith(expected_rel):
                    final_paths[img_key] = path_or_url.replace("\\", "/")
                    continue

                # Tentukan ekstensi
                ext = ".webp"
                if path_or_url.startswith(("http://", "https://")):
                    parsed = urllib.parse.urlparse(path_or_url)
                    extracted_ext = os.path.splitext(parsed.path)[1].lower()
                    if extracted_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        ext = extracted_ext
                else:
                    extracted_ext = os.path.splitext(path_or_url)[1].lower()
                    if extracted_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        ext = extracted_ext

                filename = f"{self.current_key}-{img_key}{ext}"
                dest_path = os.path.join(char_dest_dir, filename)
                rel_path = f"char/{self.current_key}/{filename}"

                # Proses
                try:
                    if path_or_url.startswith(("http://", "https://")):
                        # Download URL
                        req = urllib.request.Request(
                            path_or_url,
                            headers={'User-Agent': 'Mozilla/5.0'}
                        )
                        with urllib.request.urlopen(req, timeout=15) as response:
                            with open(dest_path, 'wb') as f:
                                f.write(response.read())
                    else:
                        # Salin file lokal
                        shutil.copy2(path_or_url, dest_path)

                    # Verifikasi dengan Pillow
                    with Image.open(dest_path) as img:
                        img.verify()

                    final_paths[img_key] = rel_path
                except Exception as e:
                    # Cleanup file rusak jika ada
                    if os.path.exists(dest_path):
                        try: os.remove(dest_path)
                        except: pass
                    self.root.after(0, lambda: self.process_failed(loading_window, img_key, str(e)))
                    return

            # Jika semua gambar sukses
            self.root.after(0, lambda: self.process_success(
                loading_window, name, speed, damage, unlockWins, punchDuration, knockback, knockbackDelay, final_paths
            ))

        threading.Thread(target=worker, daemon=True).start()

    def process_failed(self, loading_win, img_key, err_msg):
        loading_win.destroy()
        messagebox.showerror("Error", f"Gagal memproses gambar '{img_key}':\n{err_msg}")

    def process_success(self, loading_win, name, speed, damage, unlockWins, punchDuration, knockback, knockbackDelay, img_paths):
        loading_win.destroy()

        # Update data karakter
        self.characters[self.current_key].update({
            "name": name,
            "speed": speed,
            "damage": damage,
            "unlockWins": unlockWins,
            "punchDuration": punchDuration,
            "knockback": knockback,
            "knockbackDelay": knockbackDelay,
            "card": img_paths["card"],
            "stance": img_paths["stance"],
            "run": img_paths["run"],
            "punch": img_paths["punch"]
        })

        if self.save_characters_list():
            # Refresh listbox & selection
            cur_sel = self.listbox.curselection()[0]
            self.refresh_listbox()
            self.listbox.selection_set(cur_sel)
            self.on_select(None)
            messagebox.showinfo("Sukses", "Perubahan karakter berhasil disimpan ke database game!")


class NewCharacterDialog:
    """Dialog kecil kustom untuk meminta ID karakter baru"""
    def __init__(self, parent, callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Karakter Baru")
        self.dialog.geometry("360x160")
        self.dialog.configure(bg=BG_DARK)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        self.dialog.geometry(f"+{int(parent_x + parent_w/2 - 180)}+{int(parent_y + parent_h/2 - 80)}")

        self.callback = callback

        # Widgets
        tk.Label(
            self.dialog, 
            text="Masukkan ID Karakter Baru:\n(Gunakan huruf kecil/angka, contoh: goku)", 
            fg=TEXT_WHITE, 
            bg=BG_DARK,
            font=("Helvetica", 10)
        ).pack(pady=(15, 5))

        self.entry = tk.Entry(
            self.dialog, 
            bg=BG_LIST, 
            fg=TEXT_WHITE, 
            insertbackground=TEXT_WHITE, 
            bd=1, 
            relief="flat", 
            font=("Helvetica", 11),
            justify=tk.CENTER
        )
        self.entry.pack(fill=tk.X, padx=30, ipady=4, pady=5)
        self.entry.focus_set()

        btn_frame = tk.Frame(self.dialog, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, padx=30, pady=10)

        tk.Button(
            btn_frame, text="BATAL", bg="#3a3a3c", fg=TEXT_WHITE, font=("Helvetica", 9, "bold"),
            activebackground="#2c2c2e", activeforeground=TEXT_WHITE, bd=0, relief="flat", width=10, height=2, command=self.dialog.destroy
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="BUAT", bg=ACCENT_COLOR, fg=BG_DARK, font=("Helvetica", 9, "bold"),
            activebackground=ACCENT_HOVER, activeforeground=BG_DARK, bd=0, relief="flat", width=10, height=2, command=self.submit
        ).pack(side=tk.RIGHT)

    def submit(self):
        val = self.entry.get().strip()
        if not val:
            messagebox.showwarning("Peringatan", "ID Karakter tidak boleh kosong!")
            return
        self.dialog.destroy()
        self.callback(val)


if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterManagerApp(root)
    root.mainloop()
