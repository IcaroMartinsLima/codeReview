import customtkinter as ctk


class ConfigRow(ctk.CTkFrame):
    def __init__(self, parent, api_key_var, model_var, save_callback, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.api_key_var = api_key_var
        self.model_var = model_var
        self.save_callback = save_callback
        self._key_status_label = None
        self._build_row()

    def _build_row(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="API Key Groq:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )

        self.apikey_entry = ctk.CTkEntry(
            self, textvariable=self.api_key_var, show="•",
            placeholder_text="gsk_...", height=36
        )
        self.apikey_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(self, text="Modelo:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=3, padx=(12, 8), sticky="w"
        )

        self.model_entry = ctk.CTkEntry(
            self, textvariable=self.model_var,
            placeholder_text="llama-3.3-70b-versatile", width=260, height=36
        )
        self.model_entry.grid(row=0, column=4, sticky="w", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            self, text="💾 Salvar", width=90, height=36,
            fg_color="#1F2937", hover_color="#374151",
            font=ctk.CTkFont(size=12), command=self.save_callback
        )
        self.save_btn.grid(row=0, column=2)

    def show_status(self, msg: str, color: str):
        if self._key_status_label is not None:
            self._key_status_label.destroy()

        self._key_status_label = ctk.CTkLabel(
            self, text=msg, font=ctk.CTkFont(size=11), text_color=color
        )
        self._key_status_label.grid(row=1, column=0, columnspan=5, sticky="e", pady=(8, 0))
