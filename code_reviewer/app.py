import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .config import load_api_key, save_api_key
from .reviewer import review_diff_files, load_usage_history
from .components.config_row import ConfigRow
from .components.upload_row import UploadRow
from .components.issue_card import create_issue_card
from .components.report_panel import ReportPanel
from .components.settings_panel import SettingsPanel
from .constants import DEFAULT_MODEL
from .settings import load_settings


class CodeReviewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Code Reviewer")
        self.geometry("960x720")
        self.minsize(780, 560)

        self.api_key      = tk.StringVar(value=load_api_key())
        self.model_name   = tk.StringVar(value=DEFAULT_MODEL)
        self.uploaded_files = []
        self.all_issues   = []
        self.current_filter = "all"
        self.token_usage  = {}
        self.prompt_settings = load_settings()
        try:
            self.usage_history = load_usage_history() or []
        except Exception:
            self.usage_history = []

        self._build_ui()

    # ── UI scaffold ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_main()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("#13131F", "#13131F"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Logo area
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        ctk.CTkLabel(
            logo_frame, text="⟨/⟩",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#3B82F6",
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame, text="Code Reviewer",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#F1F5F9",
        ).pack(side="left")

        ctk.CTkLabel(
            logo_frame, text="beta",
            fg_color="#1E3A5F", corner_radius=4,
            font=ctk.CTkFont(size=9), text_color="#60A5FA",
            padx=5, pady=1,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            header, text="Powered by Groq",
            font=ctk.CTkFont(size=11), text_color="#374151",
        ).grid(row=0, column=2, padx=20, sticky="e")

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_frame, width=860, height=640)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        review_tab = self.tabview.add("Revisão")
        review_tab.grid_columnconfigure(0, weight=1)
        review_tab.grid_rowconfigure(2, weight=1)

        self.config_row = ConfigRow(review_tab, self.api_key, self.model_name, self._save_key)
        self.config_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.upload_row = UploadRow(review_tab, self.pick_files, self.start_review, self.remove_file)
        self.upload_row.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self._build_results_area(review_tab)

        if load_api_key():
            self.config_row.show_status("✓ Chave carregada do .env", "#4ADE80")

        reports_tab = self.tabview.add("Relatórios")
        reports_tab.grid_columnconfigure(0, weight=1)
        reports_tab.grid_rowconfigure(0, weight=1)

        self.report_panel = ReportPanel(reports_tab, usage_history=self.usage_history)
        self.report_panel.grid(row=0, column=0, sticky="nsew")

        settings_tab = self.tabview.add("⚙ Configurações")
        settings_tab.grid_columnconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(0, weight=1)

        scroll_settings = ctk.CTkScrollableFrame(settings_tab, fg_color="transparent")
        scroll_settings.grid(row=0, column=0, sticky="nsew")
        scroll_settings.grid_columnconfigure(0, weight=1)

        self.settings_panel = SettingsPanel(
            scroll_settings,
            on_save=self._on_settings_saved,
        )
        self.settings_panel.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

    def _build_results_area(self, parent):
        self.results_outer = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_outer.grid(row=2, column=0, sticky="nsew")
        self.results_outer.grid_columnconfigure(0, weight=1)
        self.results_outer.grid_rowconfigure(2, weight=1)

        self.placeholder = ctk.CTkLabel(
            self.results_outer,
            text="Adicione um arquivo .diff e clique em Analisar ▶",
            text_color="#374151", font=ctk.CTkFont(size=14),
        )
        self.placeholder.grid(row=0, column=0, pady=60)

        self.loading_label = ctk.CTkLabel(
            self.results_outer, text="",
            text_color="#60A5FA", font=ctk.CTkFont(size=14),
        )

        self.metrics_frame = ctk.CTkFrame(self.results_outer, fg_color="transparent")
        self.tab_frame     = ctk.CTkFrame(self.results_outer, fg_color="transparent")
        self.scroll        = ctk.CTkScrollableFrame(self.results_outer, fg_color="transparent")

    # ── Actions ──────────────────────────────────────────────────────────────
    def _save_key(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("API Key", "Digite a API Key antes de salvar.")
            return
        save_api_key(key)
        self.config_row.show_status("✓ Salvo em .env", "#4ADE80")

    def pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar arquivo diff",
            filetypes=[("Diff / Patch", "*.diff *.patch"), ("Todos", "*.*")],
        )
        for path in paths:
            if path not in self.uploaded_files:
                self.uploaded_files.append(path)
        self.upload_row.set_files(self.uploaded_files)

    def remove_file(self, remove_index=None):
        if remove_index is not None and 0 <= remove_index < len(self.uploaded_files):
            self.uploaded_files.pop(remove_index)
            self.upload_row.set_files(self.uploaded_files)

    def _on_settings_saved(self, new_settings: dict):
        self.prompt_settings = new_settings

    def start_review(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("API Key", "Informe a API Key do Groq primeiro.")
            return

        self.placeholder.grid_remove()
        self.metrics_frame.grid_remove()
        self.tab_frame.grid_remove()
        self.scroll.grid_remove()

        self.loading_label.configure(text="⏳ Analisando diff com Groq...")
        self.loading_label.grid(row=0, column=0, pady=60)
        self.upload_row.review_btn.configure(state="disabled", text="Analisando…")

        threading.Thread(
            target=self._run_review,
            args=(key, dict(self.prompt_settings)),
            daemon=True,
        ).start()

    def _run_review(self, key, settings):
        try:
            issues, usage_record = review_diff_files(
                key, self.model_name.get(), self.uploaded_files, settings=settings
            )
            self.token_usage   = usage_record or {}
            try:
                self.usage_history = load_usage_history() or []
            except Exception:
                self.usage_history = []
        except Exception as error:
            self.after(0, self._show_error, str(error))
            return
        self.after(0, self._show_results, issues)

    def _show_error(self, msg):
        self.loading_label.grid_remove()
        self.upload_row.review_btn.configure(state="normal", text="Analisar ▶")
        messagebox.showerror("Erro", f"Falha na análise:\n{msg}")

    def _show_results(self, issues):
        self.all_issues = issues
        self.loading_label.grid_remove()
        self.upload_row.review_btn.configure(state="normal", text="Analisar ▶")

        self._build_metrics()
        self._build_filter_tabs()
        self._filter(self.current_filter)
        self.report_panel.update(self.token_usage, self.usage_history)

    # ── Metrics bar ──────────────────────────────────────────────────────────
    def _build_metrics(self):
        f = self.metrics_frame
        for w in f.winfo_children():
            w.destroy()
        f.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total = len(self.all_issues)
        bugs  = sum(1 for i in self.all_issues if i.get("type") == "bug")
        qual  = sum(1 for i in self.all_issues if i.get("type") == "quality")
        perf  = sum(1 for i in self.all_issues if i.get("type") == "performance")

        high   = sum(1 for i in self.all_issues if i.get("severity") == "high")
        medium = sum(1 for i in self.all_issues if i.get("severity") == "medium")
        low    = sum(1 for i in self.all_issues if i.get("severity") == "low")

        # Row 0: title + severity pills
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="Resultado da revisão",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#F1F5F9",
        ).grid(row=0, column=0, sticky="w")

        sev_row = ctk.CTkFrame(top, fg_color="transparent")
        sev_row.grid(row=0, column=1, sticky="e")
        for label, value, color in [
            ("● Alta",  high,   "#FF6B6B"),
            ("● Média", medium, "#FBBF24"),
            ("● Baixa", low,    "#4ADE80"),
        ]:
            ctk.CTkLabel(
                sev_row, text=f"{label} {value}",
                font=ctk.CTkFont(size=11), text_color=color,
            ).pack(side="left", padx=6)

        # Row 1: stat cards
        for col, (value, label, color, icon) in enumerate([
            (total, "Total",       "#D1D5DB", "📋"),
            (bugs,  "Bugs",        "#FF6B6B", "🐛"),
            (qual,  "Qualidade",   "#60A5FA", "✨"),
            (perf,  "Performance", "#FBBF24", "⚡"),
        ]):
            card = ctk.CTkFrame(f, fg_color=("#1E293B", "#1E293B"), corner_radius=10)
            card.grid(row=1, column=col, padx=4, sticky="ew")

            ctk.CTkLabel(
                card, text=icon,
                font=ctk.CTkFont(size=18),
            ).pack(pady=(10, 0))
            ctk.CTkLabel(
                card, text=str(value),
                font=ctk.CTkFont(size=28, weight="bold"), text_color=color,
            ).pack()
            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=11), text_color="#6B7280",
            ).pack(pady=(0, 10))

        f.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    # ── Filter tabs ──────────────────────────────────────────────────────────
    def _build_filter_tabs(self):
        f = self.tab_frame
        for w in f.winfo_children():
            w.destroy()

        self.tab_btns = {}
        tabs = [
            ("all",         "Todos"),
            ("bug",         "🐛 Bugs"),
            ("quality",     "✨ Qualidade"),
            ("performance", "⚡ Performance"),
        ]

        for key, label in tabs:
            count = (
                len(self.all_issues) if key == "all"
                else sum(1 for i in self.all_issues if i.get("type") == key)
            )
            btn = ctk.CTkButton(
                f, text=f"{label}  {count}", height=32,
                font=ctk.CTkFont(size=12),
                fg_color="#3B82F6" if key == self.current_filter else "transparent",
                hover_color="#2563EB",
                border_width=1, border_color="#374151",
                command=lambda k=key: self._filter(k),
            )
            btn.pack(side="left", padx=3)
            self.tab_btns[key] = btn

        f.grid(row=1, column=0, sticky="w", pady=(0, 10))

    def _filter(self, key):
        self.current_filter = key
        for k, btn in self.tab_btns.items():
            btn.configure(fg_color="#3B82F6" if k == key else "transparent")

        filtered = (
            self.all_issues if key == "all"
            else [i for i in self.all_issues if i.get("type") == key]
        )
        self._render_issues(filtered)

    def _render_issues(self, issues):
        self.scroll.grid(row=2, column=0, sticky="nsew")
        self.results_outer.grid_rowconfigure(2, weight=1)

        for w in self.scroll.winfo_children():
            w.destroy()

        if not issues:
            ctk.CTkLabel(
                self.scroll, text="Nenhum problema nesta categoria.",
                text_color="#4B5563", font=ctk.CTkFont(size=13),
            ).pack(pady=30)
            return

        for issue in issues:
            create_issue_card(self.scroll, issue)