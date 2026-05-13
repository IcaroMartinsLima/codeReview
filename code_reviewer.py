import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import json
from pathlib import Path
from groq import Groq

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ENV_FILE = Path(__file__).parent / ".env"

TYPE_COLORS = {
    "bug":         ("#FF6B6B", "#4A0000"),
    "quality":     ("#60A5FA", "#0A1628"),
    "performance": ("#FBBF24", "#2A1800"),
}
TYPE_LABELS = {
    "bug": "🐛 Bug",
    "quality": "✨ Qualidade",
    "performance": "⚡ Performance",
}
SEV_COLORS = {
    "high":   "#FF6B6B",
    "medium": "#FBBF24",
    "low":    "#4ADE80",
}
SEV_LABELS = {"high": "Alta", "medium": "Média", "low": "Baixa"}


def load_api_key():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def save_api_key(key: str):
    ENV_FILE.write_text(f"GROQ_API_KEY={key}\n", encoding="utf-8")


class CodeReviewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Code Reviewer")
        self.geometry("900x700")
        self.minsize(750, 550)

        self.api_key = tk.StringVar(value=load_api_key())
        self.uploaded_files = []
        self.all_issues = []
        self.current_filter = "all"

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
            font=ctk.CTkFont(size=12),
            text_color="#4B5563"
        ).grid(row=0, column=2, padx=20, pady=14, sticky="e")

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        self._build_config_row()
        self._build_upload_row()
        self._build_results_area()

    def _build_config_row(self):
        row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text="API Key Groq:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(0, 8), sticky="w")

        self.apikey_entry = ctk.CTkEntry(
            row, textvariable=self.api_key, show="•",
            placeholder_text="gsk_...", height=36
        )
        self.apikey_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            row, text="💾 Salvar",
            width=90, height=36,
            fg_color="#1F2937", hover_color="#374151",
            font=ctk.CTkFont(size=12),
            command=self._save_key
        )
        self.save_btn.grid(row=0, column=2)

        if load_api_key():
            self._show_key_status("✓ Chave carregada do .env", "#4ADE80")

    def _save_key(self):
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("API Key", "Digite a API Key antes de salvar.")
            return
        save_api_key(key)
        self._show_key_status("✓ Salvo em .env", "#4ADE80")

    def _show_key_status(self, msg, color):
        if hasattr(self, "_key_status_label"):
            self._key_status_label.destroy()
        self._key_status_label = ctk.CTkLabel(
            self.main_frame, text=msg,
            font=ctk.CTkFont(size=11), text_color=color
        )
        self._key_status_label.grid(row=0, column=0, sticky="e", pady=(0, 10))

    def _build_upload_row(self):
        row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            row, text="+ Adicionar Diff",
            height=38, font=ctk.CTkFont(size=13),
            command=self.pick_files
        ).grid(row=0, column=0, padx=(0, 12))

        self.files_frame = ctk.CTkScrollableFrame(
            row, height=38, fg_color=("#2A2A3E", "#2A2A3E"),
            orientation="horizontal", scrollbar_button_color="#3B82F6"
        )
        self.files_frame.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        self.review_btn = ctk.CTkButton(
            row, text="Analisar ▶",
            height=38, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB",
            state="disabled", command=self.start_review
        )
        self.review_btn.grid(row=0, column=2)

    def _build_results_area(self):
        self.results_outer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
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

    def pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecionar arquivo diff",
            filetypes=[("Diff / Patch", "*.diff *.patch"), ("Todos", "*.*")]
        )
        for p in paths:
            if p not in self.uploaded_files:
                self.uploaded_files.append(p)
        self._refresh_file_chips()

    def _refresh_file_chips(self):
        for w in self.files_frame.winfo_children():
            w.destroy()
        for i, path in enumerate(self.uploaded_files):
            name = os.path.basename(path)
            chip = ctk.CTkFrame(self.files_frame, fg_color="#374151", corner_radius=6)
            chip.pack(side="left", padx=3, pady=2)
            ctk.CTkLabel(chip, text=name, font=ctk.CTkFont(size=12), text_color="#D1D5DB").pack(side="left", padx=(8, 2), pady=3)
            ctk.CTkButton(
                chip, text="×", width=20, height=20,
                fg_color="transparent", hover_color="#4B5563",
                font=ctk.CTkFont(size=12), text_color="#9CA3AF",
                command=lambda idx=i: self._remove_file(idx)
            ).pack(side="left", padx=(0, 4))

        self.review_btn.configure(state="normal" if self.uploaded_files else "disabled")

    def _remove_file(self, idx):
        self.uploaded_files.pop(idx)
        self._refresh_file_chips()

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
        self.review_btn.configure(state="disabled", text="Analisando...")

        threading.Thread(target=self._run_review, args=(key,), daemon=True).start()

    def _run_review(self, key):
        try:
            parts = []
            for path in self.uploaded_files:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    diff_content = f.read(8000)
                parts.append(f"### Diff: {os.path.basename(path)}\n```diff\n{diff_content}\n```")
            combined = "\n\n".join(parts)

            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{
                    "role": "user",
                    "content": (
                        "Você é um revisor de código sênior. Analise o diff abaixo e retorne APENAS um JSON válido, sem markdown, sem texto fora do JSON.\n\n"
                        "Analise SOMENTE as linhas com + (adições novas). Ignore linhas com - e linhas de contexto.\n\n"
                        "Formato:\n"
                        '{"issues":[{"type":"bug"|"quality"|"performance","severity":"high"|"medium"|"low",'
                        '"file":"arquivo modificado","line":"linha no diff","title":"título curto",'
                        '"description":"explicação do problema na mudança","suggestion":"como corrigir",'
                        '"snippet":"linha problemática sem o sinal de +"}]}\n\n'
                        "Retorne entre 3 e 10 problemas encontrados nas mudanças. Foque em: bugs, qualidade/boas práticas, performance.\n\n"
                        + combined
                    )
                }],
                temperature=0.2,
                max_tokens=2000,
            )
            text = resp.choices[0].message.content.strip()
            clean = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
            issues = parsed.get("issues", [])
        except json.JSONDecodeError:
            issues = []
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
            return

        self.after(0, lambda: self._show_results(issues))

    def _show_error(self, msg):
        self.loading_label.grid_remove()
        self.review_btn.configure(state="normal", text="Analisar ▶")
        messagebox.showerror("Erro", f"Falha na análise:\n{msg}")

    def _show_results(self, issues):
        self.all_issues = issues
        self.current_filter = "all"
        self.loading_label.grid_remove()
        self.review_btn.configure(state="normal", text="Analisar ▶")

        self._build_metrics()
        self._build_tabs()
        self._render_issues(issues)

    def _build_metrics(self):
        f = self.metrics_frame
        for w in f.winfo_children():
            w.destroy()
        f.grid_columnconfigure((0, 1, 2, 3), weight=1)

        total = len(self.all_issues)
        bugs  = sum(1 for i in self.all_issues if i["type"] == "bug")
        qual  = sum(1 for i in self.all_issues if i["type"] == "quality")
        perf  = sum(1 for i in self.all_issues if i["type"] == "performance")

        ctk.CTkLabel(f, text="Resultado da revisão", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        for col, (val, label, color) in enumerate([
            (total, "Total",       "#D1D5DB"),
            (bugs,  "Bugs",        "#FF6B6B"),
            (qual,  "Qualidade",   "#60A5FA"),
            (perf,  "Performance", "#FBBF24"),
        ]):
            card = ctk.CTkFrame(f, fg_color=("#1E293B", "#1E293B"), corner_radius=8)
            card.grid(row=1, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(card, text=str(val), font=ctk.CTkFont(size=26, weight="bold"), text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12), text_color="#6B7280").pack(pady=(0, 10))

        f.grid(row=0, column=0, sticky="ew", pady=(0, 12))

    def _build_tabs(self):
        f = self.tab_frame
        for w in f.winfo_children():
            w.destroy()

        self.tab_btns = {}
        tabs = [("all", "Todos"), ("bug", "🐛 Bugs"), ("quality", "✨ Qualidade"), ("performance", "⚡ Performance")]
        for key, label in tabs:
            btn = ctk.CTkButton(
                f, text=label, height=32,
                font=ctk.CTkFont(size=13),
                fg_color="#3B82F6" if key == "all" else "transparent",
                hover_color="#2563EB",
                border_width=1, border_color="#374151",
                command=lambda k=key: self._filter(k)
            )
            btn.pack(side="left", padx=3)
            self.tab_btns[key] = btn

        f.grid(row=1, column=0, sticky="w", pady=(0, 10))

    def _filter(self, key):
        self.current_filter = key
        for k, btn in self.tab_btns.items():
            btn.configure(fg_color="#3B82F6" if k == key else "transparent")
        filtered = self.all_issues if key == "all" else [i for i in self.all_issues if i["type"] == key]
        self._render_issues(filtered)

    def _render_issues(self, issues):
        self.scroll.grid(row=2, column=0, sticky="nsew")
        self.results_outer.grid_rowconfigure(2, weight=1)

        for w in self.scroll.winfo_children():
            w.destroy()

        if not issues:
            ctk.CTkLabel(self.scroll, text="Nenhum problema nesta categoria.",
                         text_color="#4B5563", font=ctk.CTkFont(size=13)).pack(pady=30)
            return

        for issue in issues:
            self._issue_card(self.scroll, issue)

    def _issue_card(self, parent, issue):
        itype  = issue.get("type", "quality")
        accent, bg = TYPE_COLORS.get(itype, ("#60A5FA", "#0A1628"))
        sev    = issue.get("severity", "medium")

        card = ctk.CTkFrame(parent, fg_color=("#1E293B", "#1E293B"), corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=0)
        bar.place(relx=0, rely=0, relheight=1, anchor="nw")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=(14, 12), pady=10)
        inner.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        badges = ctk.CTkFrame(top, fg_color="transparent")
        badges.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(badges, text=TYPE_LABELS.get(itype, itype),
                     fg_color=bg, corner_radius=6,
                     text_color=accent, font=ctk.CTkFont(size=11, weight="bold"),
                     padx=8, pady=2).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(badges, text=SEV_LABELS.get(sev, sev),
                     fg_color="#1F2937", corner_radius=6,
                     text_color=SEV_COLORS.get(sev, "#D1D5DB"),
                     font=ctk.CTkFont(size=11), padx=8, pady=2).pack(side="left")

        ctk.CTkLabel(top, text=f"{issue.get('file', '')}  L{issue.get('line', '?')}",
                     text_color="#4B5563", font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(inner, text=issue.get("title", ""), anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#F1F5F9").grid(row=1, column=0, sticky="w", pady=(6, 2))

        ctk.CTkLabel(inner, text=issue.get("description", ""), anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#94A3B8",
                     wraplength=700).grid(row=2, column=0, sticky="w")

        snippet = issue.get("snippet", "").strip()
        if snippet:
            snip_frame = ctk.CTkFrame(inner, fg_color="#0F172A", corner_radius=6)
            snip_frame.grid(row=3, column=0, sticky="ew", pady=(6, 0))
            ctk.CTkLabel(snip_frame, text=snippet, anchor="w",
                         font=ctk.CTkFont(family="Courier", size=12),
                         text_color="#7DD3FC").pack(padx=10, pady=6, anchor="w")

        suggestion = issue.get("suggestion", "").strip()
        if suggestion:
            ctk.CTkLabel(inner, text=f"💡 {suggestion}", anchor="w",
                         font=ctk.CTkFont(size=12), text_color="#6EE7B7",
                         wraplength=700).grid(row=4, column=0, sticky="w", pady=(5, 0))


if __name__ == "__main__":
    app = CodeReviewerApp()
    app.mainloop()
