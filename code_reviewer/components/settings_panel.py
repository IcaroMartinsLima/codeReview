import tkinter as tk
import customtkinter as ctk

from ..settings import (
    load_settings, save_settings,
    TONE_INSTRUCTIONS, LANGUAGE_INSTRUCTIONS, FOCUS_LABELS,
)


class SettingsPanel(ctk.CTkFrame):
    """Full settings tab: tone, language, focus, max issues."""

    def __init__(self, parent, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_save = on_save          # callback(settings: dict)
        self.settings = load_settings()
        self.grid_columnconfigure(0, weight=1)
        self._vars = {}
        self._build()

    # ── build ────────────────────────────────────────────────────────────────
    def _build(self):
        row = 0

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Configurações de Prompt",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#F1F5F9",
        ).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1

        ctk.CTkLabel(
            self,
            text="Essas configurações afetam como o modelo analisa o diff em cada revisão.",
            font=ctk.CTkFont(size=12), text_color="#6B7280",
        ).grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        # ── Tone ──────────────────────────────────────────────────────────────
        row = self._section(row, "Tom da revisão",
                            "Define o estilo da linguagem usada nas sugestões.")

        tone_frame = ctk.CTkFrame(self, fg_color="transparent")
        tone_frame.grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        self._vars["tone"] = tk.StringVar(value=self.settings.get("tone", "direto"))
        tone_options = [
            ("direto",   "Direto",   "Objetivo e sem rodeios."),
            ("didático", "Didático", "Explica o raciocínio de cada problema."),
            ("rigoroso", "Rigoroso", "Minucioso — aponta até problemas menores."),
        ]
        for col, (val, label, hint) in enumerate(tone_options):
            self._radio_card(tone_frame, self._vars["tone"], val, label, hint, col)

        # ── Language ──────────────────────────────────────────────────────────
        row = self._section(row, "Idioma da revisão",
                            "O modelo responderá neste idioma.")

        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        self._vars["language"] = tk.StringVar(value=self.settings.get("language", "pt"))
        lang_options = [
            ("pt", "🇧🇷  Português", "Respostas em PT-BR."),
            ("en", "🇺🇸  English",   "Responses in English."),
            ("es", "🇪🇸  Español",   "Respuestas en español."),
        ]
        for col, (val, label, hint) in enumerate(lang_options):
            self._radio_card(lang_frame, self._vars["language"], val, label, hint, col)

        # ── Focus ─────────────────────────────────────────────────────────────
        row = self._section(row, "Foco da análise",
                            "Selecione quais categorias o modelo deve priorizar.")

        focus_frame = ctk.CTkFrame(self, fg_color="transparent")
        focus_frame.grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        self._vars["focus"] = {}
        current_focus = self.settings.get("focus", list(FOCUS_LABELS))
        for col, (key, label) in enumerate(FOCUS_LABELS.items()):
            var = tk.BooleanVar(value=key in current_focus)
            self._vars["focus"][key] = var
            self._checkbox_card(focus_frame, var, label, col)

        # ── Max issues ────────────────────────────────────────────────────────
        row = self._section(row, "Máximo de issues",
                            "Quantos problemas o modelo pode retornar por análise.")

        slider_frame = ctk.CTkFrame(self, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
        slider_frame.grid(row=row, column=0, sticky="ew", pady=(0, 24))
        slider_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._vars["max_issues"] = tk.IntVar(value=int(self.settings.get("max_issues", 8)))
        self._max_label = ctk.CTkLabel(
            slider_frame,
            text=self._max_label_text(self._vars["max_issues"].get()),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#60A5FA",
        )
        self._max_label.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        slider = ctk.CTkSlider(
            slider_frame,
            from_=3, to=20, number_of_steps=17,
            variable=self._vars["max_issues"],
            command=self._on_slider,
            button_color="#3B82F6", button_hover_color="#2563EB",
            progress_color="#1D4ED8",
        )
        slider.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        hint_row = ctk.CTkFrame(slider_frame, fg_color="transparent")
        hint_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        hint_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hint_row, text="3", font=ctk.CTkFont(size=10),
                     text_color="#4B5563").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hint_row, text="20", font=ctk.CTkFont(size=10),
                     text_color="#4B5563").grid(row=0, column=1, sticky="e")

        # ── Save button + status ───────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=row, column=0, sticky="w")
        row += 1

        ctk.CTkButton(
            btn_row, text="💾 Salvar configurações", height=38, width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            command=self._save,
        ).pack(side="left", padx=(0, 12))

        self._status = ctk.CTkLabel(
            btn_row, text="", font=ctk.CTkFont(size=12), text_color="#4ADE80",
        )
        self._status.pack(side="left")

    # ── helpers ───────────────────────────────────────────────────────────────
    def _section(self, row: int, title: str, subtitle: str) -> int:
        sep = ctk.CTkFrame(self, fg_color="#1E293B", height=1, corner_radius=0)
        sep.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E2E8F0").grid(row=row, column=0, sticky="w")
        row += 1

        ctk.CTkLabel(self, text=subtitle,
                     font=ctk.CTkFont(size=11), text_color="#6B7280",
                     ).grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        return row

    def _radio_card(self, parent, var, value, label, hint, col):
        is_selected = var.get() == value
        card = ctk.CTkFrame(
            parent,
            fg_color="#1E3A5F" if is_selected else "#1E293B",
            corner_radius=10,
            border_width=2,
            border_color="#3B82F6" if is_selected else "#2D3748",
        )
        card.grid(row=0, column=col, padx=(0, 8), sticky="nsew")

        def _select(v=value, c=card):
            var.set(v)
            # recolor all siblings
            for sibling in parent.grid_slaves(row=0):
                sval = sibling.cget if False else None
                sibling.configure(
                    fg_color="#1E293B",
                    border_color="#2D3748",
                )
            c.configure(fg_color="#1E3A5F", border_color="#3B82F6")

        ctk.CTkRadioButton(
            card, text=label, variable=var, value=value,
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#F1F5F9",
            fg_color="#3B82F6", hover_color="#2563EB",
            command=_select,
        ).pack(padx=14, pady=(14, 4), anchor="w")

        ctk.CTkLabel(card, text=hint, font=ctk.CTkFont(size=11),
                     text_color="#6B7280", wraplength=160,
                     ).pack(padx=14, pady=(0, 14), anchor="w")

    def _checkbox_card(self, parent, var, label, col):
        card = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=10,
                            border_width=2, border_color="#2D3748")
        card.grid(row=0, column=col, padx=(0, 8), sticky="nsew")

        def _toggle(c=card):
            if var.get():
                c.configure(fg_color="#1E3A5F", border_color="#3B82F6")
            else:
                c.configure(fg_color="#1E293B", border_color="#2D3748")

        if var.get():
            card.configure(fg_color="#1E3A5F", border_color="#3B82F6")

        ctk.CTkCheckBox(
            card, text=label, variable=var,
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#F1F5F9",
            fg_color="#3B82F6", hover_color="#2563EB",
            checkmark_color="#FFFFFF",
            command=_toggle,
        ).pack(padx=14, pady=14)

    def _max_label_text(self, val: int) -> str:
        return f"Máximo: {val} issues"

    def _on_slider(self, val):
        self._max_label.configure(text=self._max_label_text(int(val)))

    # ── save ─────────────────────────────────────────────────────────────────
    def _save(self):
        focus_selected = [k for k, v in self._vars["focus"].items() if v.get()]
        if not focus_selected:
            self._status.configure(text="⚠ Selecione ao menos um foco.", text_color="#FBBF24")
            return

        new_settings = {
            "tone":       self._vars["tone"].get(),
            "language":   self._vars["language"].get(),
            "focus":      focus_selected,
            "max_issues": self._vars["max_issues"].get(),
        }
        save_settings(new_settings)
        self.settings = new_settings

        if callable(self.on_save):
            self.on_save(new_settings)

        self._status.configure(text="✓ Salvo!", text_color="#4ADE80")
        self.after(2500, lambda: self._status.configure(text=""))

    def get_settings(self) -> dict:
        """Return current in-memory settings (last saved)."""
        return dict(self.settings)