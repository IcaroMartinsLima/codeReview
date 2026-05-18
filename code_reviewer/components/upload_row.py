import customtkinter as ctk
import tkinter as tk


class UploadRow(ctk.CTkFrame):
    def __init__(self, parent, add_callback, review_callback, remove_callback,
                 paste_review_callback=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.add_callback          = add_callback
        self.review_callback       = review_callback
        self.remove_callback       = remove_callback
        self.paste_review_callback = paste_review_callback
        self.files_frame           = None
        self.review_btn            = None
        self._paste_window         = None
        self._build_row()

    def _build_row(self):
        self.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            self, text="+ Adicionar Diff", height=38,
            font=ctk.CTkFont(size=13), command=self.add_callback
        ).grid(row=0, column=0, padx=(0, 8))

        # ── Paste button ──────────────────────────────────────────────────────
        ctk.CTkButton(
            self, text="📋 Colar Diff", height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#1F2937", hover_color="#374151",
            border_width=1, border_color="#374151",
            command=self._open_paste_window,
        ).grid(row=0, column=1, padx=(0, 8))

        # ── Chips area: plain frame, hidden when empty ────────────────────────
        self.files_frame = ctk.CTkFrame(
            self, height=38, fg_color="#1E293B", corner_radius=8
        )
        # not gridded yet — appears only when files are added

        self.review_btn = ctk.CTkButton(
            self, text="Analisar ▶", height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            state="disabled", command=self.review_callback
        )
        self.review_btn.grid(row=0, column=3)

    # ── Paste window ─────────────────────────────────────────────────────────
    def _open_paste_window(self):
        # Prevent multiple windows
        if self._paste_window is not None and self._paste_window.winfo_exists():
            self._paste_window.lift()
            return

        win = ctk.CTkToplevel(self)
        win.title("Colar Diff")
        win.geometry("720x520")
        win.minsize(560, 400)
        win.grab_set()          # modal
        self._paste_window = win

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(win, fg_color=("#13131F", "#13131F"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Cole o conteúdo do diff abaixo",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F1F5F9",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        ctk.CTkLabel(
            header,
            text="git diff dev -w | clip   (Windows)   •   git diff dev -w | pbcopy   (Mac)",
            font=ctk.CTkFont(size=11, family="Courier"),
            text_color="#4B5563",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        # Text area
        self._paste_text = ctk.CTkTextbox(
            win,
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color="#0D1117",
            text_color="#C9D1D9",
            border_width=1,
            border_color="#21262D",
            wrap="none",
        )
        self._paste_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 0))

        # Try to auto-paste clipboard content if it looks like a diff
        try:
            clip = win.clipboard_get()
            if clip.strip().startswith("diff --git") or clip.strip().startswith("---"):
                self._paste_text.insert("0.0", clip)
                self._paste_text.configure(border_color="#3B82F6")
        except Exception:
            pass

        # Footer
        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=12)
        footer.grid_columnconfigure(0, weight=1)

        self._paste_status = ctk.CTkLabel(
            footer, text="", font=ctk.CTkFont(size=12), text_color="#FBBF24"
        )
        self._paste_status.grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Limpar", width=90, height=36,
            fg_color="#1F2937", hover_color="#374151",
            font=ctk.CTkFont(size=12),
            command=lambda: self._paste_text.delete("0.0", "end"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Analisar ▶", width=110, height=36,
            fg_color="#3B82F6", hover_color="#2563EB",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._submit_paste,
        ).pack(side="left")

        # Close cleans up reference
        win.protocol("WM_DELETE_WINDOW", self._close_paste_window)

    def _close_paste_window(self):
        if self._paste_window and self._paste_window.winfo_exists():
            self._paste_window.destroy()
        self._paste_window = None

    def _submit_paste(self):
        content = self._paste_text.get("0.0", "end").strip()

        if not content:
            self._paste_status.configure(text="⚠ Cole o conteúdo do diff antes de analisar.")
            return

        if not (
            content.startswith("diff --git")
            or content.startswith("---")
            or "@@" in content
        ):
            self._paste_status.configure(
                text="⚠ Conteúdo não parece ser um diff válido."
            )
            return

        self._close_paste_window()

        if callable(self.paste_review_callback):
            self.paste_review_callback(content)

    # ── File chips ───────────────────────────────────────────────────────────
    def set_files(self, uploaded_files):
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        if uploaded_files:
            for i, path in enumerate(uploaded_files):
                name = path.split("\\")[-1].split("/")[-1]
                chip = ctk.CTkFrame(self.files_frame, fg_color="#374151", corner_radius=6)
                chip.pack(side="left", padx=(4, 0), pady=4)
                ctk.CTkLabel(
                    chip, text=name, font=ctk.CTkFont(size=12), text_color="#D1D5DB"
                ).pack(side="left", padx=(8, 2), pady=3)
                ctk.CTkButton(
                    chip, text="×", width=20, height=20,
                    fg_color="transparent", hover_color="#4B5563",
                    font=ctk.CTkFont(size=12), text_color="#9CA3AF",
                    command=lambda idx=i: self._on_remove(idx),
                ).pack(side="left", padx=(0, 4))

            # Show chips frame between the paste button and analisar button
            self.files_frame.grid(row=0, column=2, sticky="ew", padx=(8, 8))
        else:
            # Hide completely when no files
            self.files_frame.grid_remove()

        self.review_btn.configure(state="normal" if uploaded_files else "disabled")

    def _on_remove(self, idx):
        if callable(self.remove_callback):
            self.remove_callback(idx)