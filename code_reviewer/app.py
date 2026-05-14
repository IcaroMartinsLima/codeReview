import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .config import load_api_key, save_api_key
from .reviewer import review_diff_files, load_usage_history
from .components.config_row import ConfigRow
from .components.upload_row import UploadRow
from .components.issue_card import create_issue_card
from .constants import DEFAULT_MODEL


class CodeReviewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Code Reviewer")
        self.geometry("900x700")
        self.minsize(750, 550)

        self.api_key = tk.StringVar(value=load_api_key())
        self.model_name = tk.StringVar(value=DEFAULT_MODEL)
        self.uploaded_files = []
        self.all_issues = []
        self.current_filter = "all"
        self.token_usage = {}
        self.usage_history = load_usage_history()

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_main()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("#1E1E2E", "#1E1E2E"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="⟨/⟩ Code Reviewer",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#60A5FA"
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        ctk.CTkLabel(
            header, text="Powered by Groq",
            font=ctk.CTkFont(size=12), text_color="#4B5563"
        ).grid(row=0, column=2, padx=20, pady=14, sticky="e")

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_frame, width=800, height=600)
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

        self.report_outer = ctk.CTkFrame(reports_tab, fg_color="transparent")
        self.report_outer.grid(row=0, column=0, sticky="nsew")
        self.report_outer.grid_columnconfigure(0, weight=1)
        self.report_outer.grid_rowconfigure(0, weight=1)

        self._render_report()

    def _build_results_area(self, parent):
        self.results_outer = ctk.CTkFrame(parent, fg_color="transparent")
        self.results_outer.grid(row=2, column=0, sticky="nsew")
        self.results_outer.grid_columnconfigure(0, weight=1)
        self.results_outer.grid_rowconfigure(1, weight=1)

        self.placeholder = ctk.CTkLabel(
            self.results_outer,
            text="Adicione um arquivo .diff e clique em Analisar.",
            text_color="#4B5563", font=ctk.CTkFont(size=14)
        )
        self.placeholder.grid(row=0, column=0, pady=60)

        self.loading_label = ctk.CTkLabel(
            self.results_outer, text="",
            text_color="#60A5FA", font=ctk.CTkFont(size=14)
        )

        self.metrics_frame = ctk.CTkFrame(self.results_outer, fg_color="transparent")
        self.tab_frame = ctk.CTkFrame(self.results_outer, fg_color="transparent")
        self.scroll = ctk.CTkScrollableFrame(self.results_outer, fg_color="transparent")

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
            filetypes=[("Diff / Patch", "*.diff *.patch"), ("Todos", "*.*")]
        )
        for path in paths:
            if path not in self.uploaded_files:
                self.uploaded_files.append(path)
        self.upload_row.set_files(self.uploaded_files)

    def remove_file(self, remove_index=None):
        if remove_index is not None and 0 <= remove_index < len(self.uploaded_files):
            self.uploaded_files.pop(remove_index)
            self.upload_row.set_files(self.uploaded_files)

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
        self.upload_row.review_btn.configure(state="disabled", text="Analisando...")

        threading.Thread(target=self._run_review, args=(key,), daemon=True).start()

    def _run_review(self, key):
        try:
            issues, usage_record = review_diff_files(key, self.model_name.get(), self.uploaded_files)
            self.token_usage = usage_record
            self.usage_history = load_usage_history()
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
        self._build_tabs()
        self._filter(self.current_filter)
        self._render_report()

    def _build_metrics(self):
        f = self.metrics_frame
        for widget in f.winfo_children():
            widget.destroy()
        f.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total = len(self.all_issues)
        bugs = sum(1 for issue in self.all_issues if issue.get("type") == "bug")
        qual = sum(1 for issue in self.all_issues if issue.get("type") == "quality")
        perf = sum(1 for issue in self.all_issues if issue.get("type") == "performance")

        ctk.CTkLabel(f, text="Resultado da revisão", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        for col, (value, label, color) in enumerate([
            (total, "Total", "#D1D5DB"),
            (bugs, "Bugs", "#FF6B6B"),
            (qual, "Qualidade", "#60A5FA"),
            (perf, "Performance", "#FBBF24"),
        ]):
            card = ctk.CTkFrame(f, fg_color=("#1E293B", "#1E293B"), corner_radius=8)
            card.grid(row=1, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=26, weight="bold"), text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color="#6B7280").pack(pady=(0, 10))

        f.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    def _build_tabs(self):
        f = self.tab_frame
        for widget in f.winfo_children():
            widget.destroy()

        self.tab_btns = {}
        tabs = [
            ("all", "Todos"),
            ("bug", "🐛 Bugs"),
            ("quality", "✨ Qualidade"),
            ("performance", "⚡ Performance"),
        ]

        for key, label in tabs:
            btn = ctk.CTkButton(
                f, text=label, height=32,
                font=ctk.CTkFont(size=13),
                fg_color="#3B82F6" if key == self.current_filter else "transparent",
                hover_color="#2563EB",
                border_width=1, border_color="#374151",
                command=lambda k=key: self._filter(k)
            )
            btn.pack(side="left", padx=3)
            self.tab_btns[key] = btn

        f.grid(row=1, column=0, sticky="w", pady=(0, 10))

    def _filter(self, key):
        self.current_filter = key
        for current_key, btn in self.tab_btns.items():
            btn.configure(fg_color="#3B82F6" if current_key == key else "transparent")

        filtered = self.all_issues if key == "all" else [issue for issue in self.all_issues if issue.get("type") == key]
        self._render_issues(filtered)

    def _render_issues(self, issues):
        self.scroll.grid(row=2, column=0, sticky="nsew")
        self.results_outer.grid_rowconfigure(2, weight=1)

        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not issues:
            ctk.CTkLabel(self.scroll, text="Nenhum problema nesta categoria.",
                         text_color="#4B5563", font=ctk.CTkFont(size=13)).pack(pady=30)
            return

        for issue in issues:
            create_issue_card(self.scroll, issue)

    def _render_report(self):
        if not hasattr(self, 'report_outer'):
            return

        for widget in self.report_outer.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.report_outer,
            text="Relatório completo de tokens",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F1F5F9"
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        if not self.token_usage:
            ctk.CTkLabel(
                self.report_outer,
                text="Nenhum relatório disponível ainda. Faça uma análise para gerar dados.",
                text_color="#94A3B8",
                font=ctk.CTkFont(size=13)
            ).grid(row=1, column=0, sticky="w", pady=20)
            return

        summary_frame = ctk.CTkFrame(self.report_outer, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
        summary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        cards = [
            (self.token_usage["prompt_tokens"], "Prompt", "#60A5FA"),
            (self.token_usage["completion_tokens"], "Completion", "#FBBF24"),
            (self.token_usage["total_tokens"], "Total", "#A78BFA"),
            (self.token_usage.get("issues", 0), "Issues", "#34D399"),
        ]

        for col, (value, label, color) in enumerate(cards):
            card = ctk.CTkFrame(summary_frame, fg_color=("#111827", "#111827"), corner_radius=8)
            card.grid(row=0, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=24, weight="bold"), text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack(pady=(0, 10))

        chart_frame = ctk.CTkFrame(self.report_outer, fg_color=("#111827", "#111827"), corner_radius=12)
        chart_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        canvas = tk.Canvas(chart_frame, height=220, bg="#0F172A", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        canvas.bind("<Configure>", lambda event: self._draw_usage_chart(canvas))
        self._draw_usage_chart(canvas)

        history_frame = ctk.CTkFrame(self.report_outer, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
        history_frame.grid(row=3, column=0, sticky="ew")
        history_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            history_frame,
            text="Últimas análises",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F1F5F9"
        ).grid(row=0, column=0, sticky="w", pady=(10, 8), padx=10)

        for index, record in enumerate(self.usage_history[-5:][::-1], start=1):
            ctk.CTkLabel(
                history_frame,
                text=(f"{record['timestamp']} - Total: {record['total_tokens']} | "
                      f"Prompt: {record['prompt_tokens']} | Completion: {record['completion_tokens']} | "
                      f"Issues: {record['issues']}"),
                text_color="#D1D5DB",
                font=ctk.CTkFont(size=11),
                wraplength=820,
                anchor="w"
            ).grid(row=index, column=0, sticky="w", padx=10, pady=2)

        ctk.CTkLabel(
            self.report_outer,
            text="Histórico salvo em token_usage.json",
            text_color="#6B7280",
            font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, sticky="w", pady=(10, 10), padx=10)

    def _draw_usage_chart(self, canvas):
        canvas.delete("all")
        if not self.token_usage:
            return

        metrics = [
            ("Prompt", self.token_usage["prompt_tokens"], "#60A5FA"),
            ("Completion", self.token_usage["completion_tokens"], "#FBBF24"),
            ("Total", self.token_usage["total_tokens"], "#A78BFA"),
        ]
        width = canvas.winfo_width() or 400
        height = canvas.winfo_height() or 220
        max_val = max([value for _, value, _ in metrics] + [1])
        padding = 36
        available_width = width - padding * 2
        gap = 24
        bar_width = (available_width - gap * (len(metrics) - 1)) / len(metrics)

        for idx, (label, value, color) in enumerate(metrics):
            x0 = padding + idx * (bar_width + gap)
            x1 = x0 + bar_width
            bar_height = int((height - 90) * (value / max_val))
            y0 = height - 40 - bar_height
            y1 = height - 40
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            canvas.create_text((x0 + x1) / 2, y0 - 12, text=str(value), fill="#F8FAFC", font=("Arial", 10, "bold"))
            canvas.create_text((x0 + x1) / 2, height - 18, text=label, fill="#9CA3AF", font=("Arial", 10))
