import os
import re
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

class BackgroundManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OKE GAS KOMBAT - Pengelola Background")
        self.root.geometry("1000x650")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        # Path Setup
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.background_dir = os.path.join(self.project_dir, "background")
        self.js_file = os.path.join(self.project_dir, "backgrounds.js")

        # Ensure background directory exists
        if not os.path.exists(self.background_dir):
            os.makedirs(self.background_dir)

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('.', background=BG_DARK, foreground=TEXT_WHITE)
        self.style.configure('TFrame', background=BG_DARK)
        self.style.configure('Card.TFrame', background=BG_CARD)
        
        # Load backgrounds
        self.backgrounds = self.load_backgrounds_list()
        self.preview_image = None

        # Build UI
        self.create_widgets()

        # Select first item if list is not empty
        if self.backgrounds:
            self.listbox.selection_set(0)
            self.on_select(None)

    def load_backgrounds_list(self):
        """Membaca daftar background dari backgrounds.js"""
        if not os.path.exists(self.js_file):
            # Buat file baru jika tidak ada
            return []
        
        try:
            with open(self.js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cari isi array di antara brackets
            match = re.search(r'const\s+backgrounds\s*=\s*\[(.*?)\];', content, re.DOTALL)
            if match:
                array_content = match.group(1)
                items = re.findall(r"['\"](.*?)['\"]", array_content)
                # Bersihkan path dari spasi berlebih
                return [item.strip() for item in items if item.strip()]
            return []
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca backgrounds.js:\n{str(e)}")
            return []

    def save_backgrounds_list(self):
        """Menulis daftar background ke backgrounds.js"""
        try:
            content = "const backgrounds = [\n"
            for bg in self.backgrounds:
                content += f"    '{bg}',\n"
            # Hapus koma terakhir jika ada item
            if self.backgrounds:
                content = content.rstrip(",\n") + "\n"
            content += "];\n"

            with open(self.js_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan ke backgrounds.js:\n{str(e)}")
            return False

    def create_widgets(self):
        # Header Game
        header_frame = tk.Frame(self.root, bg=BG_DARK, height=70)
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
            text=" - Background Asset Manager", 
            font=("Helvetica", 14, "italic"), 
            fg=TEXT_MUTED, 
            bg=BG_DARK
        )
        subtitle_label.pack(side=tk.LEFT, pady=(12, 0))

        # Main Layout Frame
        main_frame = tk.Frame(self.root, bg=BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Left Column (Background list and CRUD controls)
        left_frame = tk.Frame(main_frame, bg=BG_CARD, width=320)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_frame.pack_propagate(False)

        list_label = tk.Label(
            left_frame, 
            text="Daftar Background", 
            font=("Helvetica", 12, "bold"), 
            fg=TEXT_WHITE, 
            bg=BG_CARD
        )
        list_label.pack(anchor=tk.W, padx=15, pady=(15, 5))

        # Listbox with Scrollbar
        list_container = tk.Frame(left_frame, bg=BG_LIST)
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_container, 
            bg=BG_LIST, 
            fg=TEXT_WHITE, 
            selectbackground=ACCENT_COLOR, 
            selectforeground=BG_DARK,
            font=("Courier New", 11), 
            bd=0, 
            highlightthickness=0,
            exportselection=False,
            yscrollcommand=self.scrollbar.set
        )
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Populating listbox
        self.refresh_listbox()

        # Action Buttons
        btn_frame = tk.Frame(left_frame, bg=BG_CARD)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        self.add_btn = tk.Button(
            btn_frame, 
            text="➕ TAMBAH", 
            bg=GREEN_COLOR, 
            fg=TEXT_WHITE,
            activebackground=GREEN_COLOR,
            activeforeground=TEXT_WHITE,
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            relief="flat", 
            height=2,
            command=self.open_add_dialog
        )
        self.add_btn.pack(fill=tk.X, pady=5)

        self.edit_btn = tk.Button(
            btn_frame, 
            text="✏️ EDIT SUMBER", 
            bg=ACCENT_COLOR, 
            fg=BG_DARK,
            activebackground=ACCENT_HOVER,
            activeforeground=BG_DARK,
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            relief="flat", 
            height=2,
            command=self.open_edit_dialog
        )
        self.edit_btn.pack(fill=tk.X, pady=5)

        self.delete_btn = tk.Button(
            btn_frame, 
            text="🗑️ HAPUS", 
            bg=RED_COLOR, 
            fg=TEXT_WHITE,
            activebackground=RED_HOVER,
            activeforeground=TEXT_WHITE,
            font=("Helvetica", 10, "bold"), 
            bd=0, 
            relief="flat", 
            height=2,
            command=self.delete_selected
        )
        self.delete_btn.pack(fill=tk.X, pady=5)

        # Right Column (Preview Area)
        right_frame = tk.Frame(main_frame, bg=BG_CARD)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        preview_header = tk.Label(
            right_frame, 
            text="Pratinjau Gambar (Real-time Preview)", 
            font=("Helvetica", 12, "bold"), 
            fg=TEXT_WHITE, 
            bg=BG_CARD
        )
        preview_header.pack(anchor=tk.W, padx=15, pady=(15, 5))

        # Preview Display (Canvas for easy resizing and centered display)
        self.preview_canvas = tk.Canvas(
            right_frame, 
            bg=BG_LIST, 
            bd=0, 
            highlightthickness=1, 
            highlightbackground="#2b2b36"
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        self.preview_canvas.bind("<Configure>", self.on_canvas_resize)

        # Label info di bawah canvas
        self.info_label = tk.Label(
            right_frame, 
            text="Pilih gambar dari daftar untuk melihat pratinjau.", 
            font=("Helvetica", 10), 
            fg=TEXT_MUTED, 
            bg=BG_CARD
        )
        self.info_label.pack(fill=tk.X, padx=15, pady=(0, 15))

    def refresh_listbox(self):
        """Memperbarui item di listbox"""
        self.listbox.delete(0, tk.END)
        for bg in self.backgrounds:
            # Tampilkan hanya nama file untuk kemudahan baca
            filename = os.path.basename(bg)
            self.listbox.insert(tk.END, f"  {filename}")

    def on_select(self, event):
        """Dipanggil ketika item di listbox dipilih"""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        bg_path = self.backgrounds[index]
        full_path = os.path.join(self.project_dir, bg_path)

        self.info_label.config(text=f"Lokasi: {bg_path}")
        self.show_preview(full_path)

    def on_canvas_resize(self, event):
        """Mengatur ulang ukuran gambar saat canvas di-resize"""
        selection = self.listbox.curselection()
        if selection:
            self.on_select(None)

    def show_preview(self, image_path):
        """Memuat gambar dan menampilkan pratinjau di canvas"""
        self.preview_canvas.delete("all")
        
        if not os.path.exists(image_path):
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() / 2,
                self.preview_canvas.winfo_height() / 2,
                text="⚠️ Gambar Tidak Ditemukan",
                fill=RED_COLOR,
                font=("Helvetica", 14, "bold")
            )
            return

        try:
            img = Image.open(image_path)
            
            # Dapatkan dimensi canvas
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # Jika canvas belum di-render sepenuhnya, gunakan nilai default
            if canvas_width < 10 or canvas_height < 10:
                canvas_width = 600
                canvas_height = 400

            # Hitung rasio aspek dan sesuaikan ukuran
            img_width, img_height = img.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            
            new_width = int(img_width * ratio * 0.95)
            new_height = int(img_height * ratio * 0.95)
            
            # Hindari resize ke 0
            if new_width <= 0: new_width = 1
            if new_height <= 0: new_height = 1

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img_resized)

            # Gambar di tengah-tengah canvas
            self.preview_canvas.create_image(
                canvas_width / 2,
                canvas_height / 2,
                image=self.preview_image,
                anchor=tk.CENTER
            )
        except Exception as e:
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() / 2,
                self.preview_canvas.winfo_height() / 2,
                text=f"⚠️ Gagal memuat pratinjau:\n{str(e)}",
                fill=RED_COLOR,
                font=("Helvetica", 11),
                justify=tk.CENTER
            )

    def delete_selected(self):
        """Menghapus background yang sedang dipilih"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Peringatan", "Silakan pilih background yang ingin dihapus terlebih dahulu!")
            return

        index = selection[0]
        bg_path = self.backgrounds[index]
        filename = os.path.basename(bg_path)

        confirm = messagebox.askyesno(
            "Konfirmasi Hapus", 
            f"Apakah Anda yakin ingin menghapus background '{filename}'?\n\nFile di folder 'background/' juga akan dihapus secara fisik."
        )
        if not confirm:
            return

        # Hapus file fisik
        full_path = os.path.join(self.project_dir, bg_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            messagebox.showwarning("Peringatan", f"Daftar berhasil dihapus, namun gagal menghapus file fisik:\n{str(e)}")

        # Hapus dari list dan simpan
        del self.backgrounds[index]
        if self.save_backgrounds_list():
            self.refresh_listbox()
            self.preview_canvas.delete("all")
            self.info_label.config(text="Background berhasil dihapus.")
            # Pilih item pertama setelah penghapusan jika list tidak kosong
            if self.backgrounds:
                self.listbox.selection_set(0)
                self.on_select(None)
            messagebox.showinfo("Sukses", "Background berhasil dihapus dari daftar!")

    def open_add_dialog(self):
        """Membuka dialog tambah background baru"""
        SourceDialog(self.root, "Tambah Background", self.add_background_callback)

    def open_edit_dialog(self):
        """Membuka dialog edit sumber background"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Peringatan", "Silakan pilih background yang ingin diedit sumbernya terlebih dahulu!")
            return

        index = selection[0]
        bg_path = self.backgrounds[index]
        SourceDialog(self.root, "Edit Sumber Background", lambda source_type, path_or_url, filename: 
                     self.edit_background_callback(index, bg_path, source_type, path_or_url, filename))

    def add_background_callback(self, source_type, path_or_url, filename):
        """Callback saat user menambah background melalui dialog"""
        if not filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            # Tambahkan ekstensi bawaan jika user tidak memberikan
            ext = os.path.splitext(path_or_url)[1].lower() if source_type == 'file' else '.webp'
            if not ext or ext not in ['.png', '.jpg', '.jpeg', '.webp']:
                ext = '.webp'
            filename += ext

        dest_relative_path = f"background/{filename}"
        dest_full_path = os.path.join(self.project_dir, dest_relative_path)

        # Cek duplikasi nama
        if dest_relative_path in self.backgrounds:
            overwrite = messagebox.askyesno(
                "Konfirmasi Overwrite", 
                f"Background dengan nama '{filename}' sudah terdaftar. Apakah Anda ingin menimpanya?"
            )
            if not overwrite:
                return

        # Jalankan proses copy/download
        if source_type == 'file':
            self.copy_local_file(path_or_url, dest_full_path, dest_relative_path)
        else:
            self.download_remote_file(path_or_url, dest_full_path, dest_relative_path)

    def edit_background_callback(self, index, old_relative_path, source_type, path_or_url, filename):
        """Callback saat user mengedit sumber background melalui dialog"""
        if not filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            ext = os.path.splitext(path_or_url)[1].lower() if source_type == 'file' else '.webp'
            if not ext or ext not in ['.png', '.jpg', '.jpeg', '.webp']:
                ext = '.webp'
            filename += ext

        dest_relative_path = f"background/{filename}"
        dest_full_path = os.path.join(self.project_dir, dest_relative_path)

        # Cek jika mengganti nama dan bertabrakan dengan yang sudah ada
        if dest_relative_path in self.backgrounds and dest_relative_path != old_relative_path:
            messagebox.showerror("Error", f"Nama file '{filename}' sudah digunakan oleh background lain!")
            return

        # Hapus file lama jika berganti nama
        if dest_relative_path != old_relative_path:
            old_full_path = os.path.join(self.project_dir, old_relative_path)
            try:
                if os.path.exists(old_full_path):
                    os.remove(old_full_path)
            except Exception as e:
                print(f"Gagal menghapus file lama saat rename: {e}")

        # Jalankan proses copy/download
        if source_type == 'file':
            self.copy_local_file(path_or_url, dest_full_path, dest_relative_path, edit_index=index)
        else:
            self.download_remote_file(path_or_url, dest_full_path, dest_relative_path, edit_index=index)

    def copy_local_file(self, src, dest, relative_path, edit_index=None):
        """Menyalin berkas gambar lokal"""
        try:
            shutil.copy2(src, dest)
            
            # Verifikasi bahwa itu adalah file gambar valid
            with Image.open(dest) as img:
                img.verify()

            self.update_list_after_change(relative_path, edit_index)
            messagebox.showinfo("Sukses", f"Berhasil menyimpan background lokal:\n{os.path.basename(dest)}")
        except Exception as e:
            if os.path.exists(dest):
                try: os.remove(dest)
                except: pass
            messagebox.showerror("Error", f"Gagal menyalin atau memverifikasi berkas:\n{str(e)}")

    def download_remote_file(self, url, dest, relative_path, edit_index=None):
        """Mengunduh berkas gambar menggunakan thread terpisah agar UI responsif"""
        # Tampilkan status loading
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Mengunduh...")
        loading_window.geometry("300x120")
        loading_window.configure(bg=BG_DARK)
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        # Posisikan loading window di tengah window utama
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        loading_window.geometry(f"+{int(main_x + main_w/2 - 150)}+{int(main_y + main_h/2 - 60)}")

        label = tk.Label(
            loading_window, 
            text="Mengunduh gambar dari internet...\nMohon tunggu.", 
            fg=TEXT_WHITE, 
            bg=BG_DARK,
            font=("Helvetica", 10)
        )
        label.pack(pady=20)
        
        progress = ttk.Progressbar(loading_window, mode='indeterminate')
        progress.pack(fill=tk.X, padx=30)
        progress.start(10)

        def worker():
            try:
                # Custom User-Agent agar tidak diblokir webserver
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    with open(dest, 'wb') as out_file:
                        out_file.write(response.read())

                # Verifikasi format gambar
                with Image.open(dest) as img:
                    img.verify()

                # Update UI via main thread safe method
                self.root.after(0, lambda: self.download_success(loading_window, relative_path, edit_index, dest))
            except Exception as e:
                # Hapus file sampah jika gagal
                if os.path.exists(dest):
                    try: os.remove(dest)
                    except: pass
                self.root.after(0, lambda: self.download_failed(loading_window, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def download_success(self, loading_win, relative_path, edit_index, dest):
        loading_win.destroy()
        self.update_list_after_change(relative_path, edit_index)
        messagebox.showinfo("Sukses", f"Berhasil mengunduh background:\n{os.path.basename(dest)}")

    def download_failed(self, loading_win, err_msg):
        loading_win.destroy()
        messagebox.showerror("Error", f"Gagal mengunduh atau memverifikasi berkas gambar:\n{err_msg}")

    def update_list_after_change(self, relative_path, edit_index=None):
        """Memperbarui array list, menyimpan, dan me-refresh UI"""
        if edit_index is not None:
            # Ganti item yang ada
            self.backgrounds[edit_index] = relative_path
        else:
            # Tambah item baru jika belum ada di list
            if relative_path not in self.backgrounds:
                self.backgrounds.append(relative_path)

        if self.save_backgrounds_list():
            self.refresh_listbox()
            # Select item baru/terubah
            idx = edit_index if edit_index is not None else self.backgrounds.index(relative_path)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.on_select(None)


class SourceDialog:
    """Dialog Kustom untuk memasukkan file atau URL dan nama background"""
    def __init__(self, parent, title, callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x320")
        self.dialog.configure(bg=BG_DARK)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Posisikan di tengah
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        self.dialog.geometry(f"+{int(parent_x + parent_w/2 - 250)}+{int(parent_y + parent_h/2 - 160)}")

        self.callback = callback
        self.source_type = tk.StringVar(value="file")

        # Layout widgets
        self.create_widgets()

    def create_widgets(self):
        # Radio Buttons untuk pilihan sumber
        radio_frame = tk.Frame(self.dialog, bg=BG_DARK)
        radio_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(radio_frame, text="Pilih Sumber:", font=("Helvetica", 10, "bold"), fg=TEXT_WHITE, bg=BG_DARK).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Radiobutton(
            radio_frame, text="File Lokal", variable=self.source_type, value="file", 
            fg=TEXT_WHITE, bg=BG_DARK, selectcolor=BG_DARK, activebackground=BG_DARK, activeforeground=TEXT_WHITE,
            command=self.toggle_source_type, font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(
            radio_frame, text="URL Gambar", variable=self.source_type, value="url", 
            fg=TEXT_WHITE, bg=BG_DARK, selectcolor=BG_DARK, activebackground=BG_DARK, activeforeground=TEXT_WHITE,
            command=self.toggle_source_type, font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=10)

        # Form Input Frame
        form_frame = tk.Frame(self.dialog, bg=BG_CARD, bd=1, relief="solid", highlightthickness=0)
        form_frame.pack(fill=tk.X, padx=20, pady=5)

        # Input Sumber (Path/URL)
        self.src_label = tk.Label(form_frame, text="Pilih File Gambar:", fg=TEXT_WHITE, bg=BG_CARD, font=("Helvetica", 10))
        self.src_label.grid(row=0, column=0, sticky=tk.W, padx=15, pady=(15, 5))

        entry_frame = tk.Frame(form_frame, bg=BG_CARD)
        entry_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))
        entry_frame.columnconfigure(0, weight=1)

        self.src_entry = tk.Entry(entry_frame, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", font=("Helvetica", 10))
        self.src_entry.grid(row=0, column=0, sticky="ew", ipady=5)

        self.browse_btn = tk.Button(
            entry_frame, text="Cari File...", bg=ACCENT_COLOR, fg=BG_DARK, font=("Helvetica", 9, "bold"),
            activebackground=ACCENT_HOVER, activeforeground=BG_DARK, bd=0, relief="flat", padx=10, command=self.browse_file
        )
        self.browse_btn.grid(row=0, column=1, padx=(10, 0))

        # Input Nama File Output
        tk.Label(form_frame, text="Nama File Background Baru (contoh: bg-monas):", fg=TEXT_WHITE, bg=BG_CARD, font=("Helvetica", 10)).grid(
            row=2, column=0, sticky=tk.W, padx=15, pady=(5, 5)
        )
        
        self.name_entry = tk.Entry(form_frame, bg=BG_LIST, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, bd=1, relief="flat", font=("Helvetica", 10))
        self.name_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15), ipady=5)

        # Action Buttons
        btn_frame = tk.Frame(self.dialog, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        self.cancel_btn = tk.Button(
            btn_frame, text="BATAL", bg="#3a3a3c", fg=TEXT_WHITE, font=("Helvetica", 10, "bold"),
            activebackground="#2c2c2e", activeforeground=TEXT_WHITE, bd=0, relief="flat", width=12, height=2, command=self.dialog.destroy
        )
        self.cancel_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(
            btn_frame, text="SIMPAN", bg=ACCENT_COLOR, fg=BG_DARK, font=("Helvetica", 10, "bold"),
            activebackground=ACCENT_HOVER, activeforeground=BG_DARK, bd=0, relief="flat", width=12, height=2, command=self.submit
        )
        self.submit_btn.pack(side=tk.RIGHT)

    def toggle_source_type(self):
        """Menyesuaikan label dan tombol sesuai pilihan jenis sumber"""
        stype = self.source_type.get()
        self.src_entry.delete(0, tk.END)
        if stype == "file":
            self.src_label.config(text="Pilih File Gambar:")
            self.browse_btn.grid(row=0, column=1, padx=(10, 0))
        else:
            self.src_label.config(text="Masukkan URL Gambar:")
            self.browse_btn.grid_forget()

    def browse_file(self):
        """Membuka file dialog untuk mencari gambar lokal"""
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp"), ("All Files", "*.*")]
        )
        if file_path:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, file_path)
            
            # Otomatis isi nama file output dari nama file asli
            basename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(basename)[0]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, name_without_ext)

    def submit(self):
        stype = self.source_type.get()
        path_or_url = self.src_entry.get().strip()
        filename = self.name_entry.get().strip()

        if not path_or_url:
            messagebox.showwarning("Peringatan", "Silakan tentukan sumber file atau masukkan URL!")
            return
        if not filename:
            messagebox.showwarning("Peringatan", "Silakan masukkan nama file background baru!")
            return

        # Panggil callback dan tutup dialog
        self.dialog.destroy()
        self.callback(stype, path_or_url, filename)


if __name__ == "__main__":
    root = tk.Tk()
    app = BackgroundManagerApp(root)
    root.mainloop()
