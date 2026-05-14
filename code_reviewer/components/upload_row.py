import customtkinter as ctk


class UploadRow(ctk.CTkFrame):
    def __init__(self, parent, add_callback, review_callback, remove_callback, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.add_callback = add_callback
        self.review_callback = review_callback
        self.remove_callback = remove_callback
        self.files_frame = None
        self.review_btn = None
        self._build_row()

    def _build_row(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            self, text="+ Adicionar Diff", height=38,
            font=ctk.CTkFont(size=13), command=self.add_callback
        ).grid(row=0, column=0, padx=(0, 12))

        self.files_frame = ctk.CTkScrollableFrame(
            self, height=38, fg_color=("#2A2A3E", "#2A2A3E"),
            orientation="horizontal", scrollbar_button_color="#3B82F6"
        )
        self.files_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        self.review_btn = ctk.CTkButton(
            self, text="Analisar ▶", height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            state="disabled", command=self.review_callback
        )
        self.review_btn.grid(row=0, column=2)

    def set_files(self, uploaded_files):
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        for i, path in enumerate(uploaded_files):
            name = path.split("\\")[-1]
            chip = ctk.CTkFrame(self.files_frame, fg_color="#374151", corner_radius=6)
            chip.pack(side="left", padx=3, pady=2)
            ctk.CTkLabel(chip, text=name, font=ctk.CTkFont(size=12), text_color="#D1D5DB").pack(side="left", padx=(8, 2), pady=3)
            ctk.CTkButton(
                chip, text="×", width=20, height=20,
                fg_color="transparent", hover_color="#4B5563",
                font=ctk.CTkFont(size=12), text_color="#9CA3AF",
                command=lambda idx=i: self._on_remove(idx)
            ).pack(side="left", padx=(0, 4))

        self.review_btn.configure(state="normal" if uploaded_files else "disabled")

    def _on_remove(self, idx):
        if callable(self.remove_callback):
            self.remove_callback(idx)
