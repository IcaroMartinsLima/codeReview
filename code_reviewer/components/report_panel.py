import math
import tkinter as tk
import customtkinter as ctk


class ReportPanel(ctk.CTkFrame):
    def __init__(self, parent, token_usage=None, usage_history=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.token_usage = token_usage or {}
        self.usage_history = usage_history or []
        # Seed token_usage from last history record on first load if none provided
        if not self.token_usage and self.usage_history:
            self.token_usage = dict(self.usage_history[-1])
        self.chart_canvas = None
        self.pie_canvas = None
        self.grid_columnconfigure(0, weight=1)
        self._render()

    def update(self, token_usage, usage_history):
        self.token_usage = token_usage or {}
        self.usage_history = usage_history or []
        # If no explicit token_usage given but history exists, use the last record
        if not self.token_usage and self.usage_history:
            self.token_usage = dict(self.usage_history[-1])
        self._render()

    # ─────────────────────────────────────────────────────────────────────────
    def _render(self):
        for w in self.winfo_children():
            w.destroy()
        self.chart_canvas = None
        self.pie_canvas = None

        # Title + export button
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row, text="Relatório de tokens & uso",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#F1F5F9",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            title_row, text="⬇ Exportar CSV", width=130, height=32,
            fg_color="#1F2937", hover_color="#374151",
            font=ctk.CTkFont(size=12), text_color="#D1D5DB",
            border_width=1, border_color="#374151",
            command=self._export_csv,
        ).grid(row=0, column=1, sticky="e")

        if not self.token_usage:
            ctk.CTkLabel(
                self,
                text="Nenhum relatório disponível ainda. Faça uma análise para gerar dados.",
                text_color="#94A3B8", font=ctk.CTkFont(size=13),
            ).grid(row=1, column=0, sticky="w", pady=20)
            return

        # Summary cards
        summary = ctk.CTkFrame(self, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
        summary.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for col, (value, label, color) in enumerate([
            (self.token_usage.get("prompt_tokens",     0), "Prompt",     "#60A5FA"),
            (self.token_usage.get("completion_tokens", 0), "Completion", "#FBBF24"),
            (self.token_usage.get("total_tokens",      0), "Total",      "#A78BFA"),
            (self.token_usage.get("issues",            0), "Issues",     "#34D399"),
        ]):
            card = ctk.CTkFrame(summary, fg_color=("#111827", "#111827"), corner_radius=8)
            card.grid(row=0, column=col, padx=4, pady=8, sticky="ew")
            ctk.CTkLabel(card, text=str(value),
                         font=ctk.CTkFont(size=24, weight="bold"),
                         text_color=color).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack(pady=(0, 10))

        # Charts side by side
        charts_row = ctk.CTkFrame(self, fg_color="transparent")
        charts_row.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        charts_row.grid_columnconfigure(0, weight=3)
        charts_row.grid_columnconfigure(1, weight=2)

        # — Line chart: token history —
        line_frame = ctk.CTkFrame(charts_row, fg_color=("#111827", "#111827"), corner_radius=12)
        line_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        line_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(line_frame, text="Histórico de tokens",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8",
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self.chart_canvas = tk.Canvas(line_frame, height=160, bg="#0F172A", highlightthickness=0)
        self.chart_canvas.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
        self.chart_canvas.bind("<Configure>", lambda _e: self._draw_line_chart())
        self._draw_line_chart()

        # — Pie chart: last analysis —
        pie_frame = ctk.CTkFrame(charts_row, fg_color=("#111827", "#111827"), corner_radius=12)
        pie_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        pie_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pie_frame, text="Distribuição (última análise)",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8",
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self.pie_canvas = tk.Canvas(pie_frame, height=160, bg="#0F172A", highlightthickness=0)
        self.pie_canvas.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 12))
        self.pie_canvas.bind("<Configure>", lambda _e: self._draw_pie_chart())
        self._draw_pie_chart()

        # History table
        hist_frame = ctk.CTkFrame(self, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
        hist_frame.grid(row=3, column=0, sticky="ew")
        hist_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hist_frame, text="Últimas análises",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#F1F5F9").grid(row=0, column=0, sticky="w", pady=(10, 4), padx=12)

        # Table header
        cols = ["Hora", "Modelo", "Prompt", "Completion", "Total", "Issues"]
        header = ctk.CTkFrame(hist_frame, fg_color="#0F172A", corner_radius=6)
        header.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        for col_i, text in enumerate(cols):
            header.grid_columnconfigure(col_i, weight=1 if col_i <= 1 else 0, minsize=70)
            ctk.CTkLabel(header, text=text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6B7280").grid(row=0, column=col_i, sticky="w", padx=8, pady=5)

        col_colors = ["#D1D5DB", "#9CA3AF", "#60A5FA", "#FBBF24", "#A78BFA", "#34D399"]
        for row_i, record in enumerate(self.usage_history[-8:][::-1]):
            row_bg = "#111827" if row_i % 2 == 0 else "#1A2236"
            row_f = ctk.CTkFrame(hist_frame, fg_color=row_bg, corner_radius=4)
            row_f.grid(row=row_i + 2, column=0, sticky="ew", padx=12, pady=1)
            for col_i, col_hd in enumerate(cols):
                row_f.grid_columnconfigure(col_i, weight=1 if col_i <= 1 else 0, minsize=70)

            ts = record.get("timestamp", "")[:16].replace("T", " ")
            values = [
                ts,
                record.get("model", "—")[:22],
                f"{record.get('prompt_tokens', 0):,}",
                f"{record.get('completion_tokens', 0):,}",
                f"{record.get('total_tokens', 0):,}",
                str(record.get("issues", 0)),
            ]
            for col_i, (val, color) in enumerate(zip(values, col_colors)):
                ctk.CTkLabel(row_f, text=val, text_color=color,
                             font=ctk.CTkFont(size=11), anchor="w",
                             ).grid(row=0, column=col_i, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(self, text="Histórico salvo em token_usage.json",
                     text_color="#6B7280", font=ctk.CTkFont(size=11),
                     ).grid(row=4, column=0, sticky="w", pady=(8, 4), padx=4)

    # ── Line chart ────────────────────────────────────────────────────────────
    def _draw_line_chart(self):
        canvas = self.chart_canvas
        if not canvas:
            return
        canvas.delete("all")

        history = self.usage_history[-12:]
        if not history:
            canvas.create_text(80, 80, text="Sem dados", fill="#4B5563", font=("Arial", 11))
            return

        w = canvas.winfo_width() or 420
        h = canvas.winfo_height() or 160
        pl, pr, pt, pb = 48, 16, 16, 28

        series = [
            ("Total",  [r.get("total_tokens",      0) for r in history], "#A78BFA"),
            ("Prompt", [r.get("prompt_tokens",      0) for r in history], "#60A5FA"),
            ("Compl.", [r.get("completion_tokens",  0) for r in history], "#FBBF24"),
        ]

        max_val = max((v for _, vals, _ in series for v in vals), default=1)

        def _x(i):
            if len(history) == 1:
                return (pl + w - pr) / 2
            return pl + i * (w - pl - pr) / (len(history) - 1)

        def _y(v):
            return pt + (1 - v / max_val) * (h - pt - pb)

        # Horizontal grid lines
        for frac in (0.25, 0.5, 0.75, 1.0):
            gy = pt + (1 - frac) * (h - pt - pb)
            canvas.create_line(pl, gy, w - pr, gy, fill="#1E293B", dash=(3, 4))
            canvas.create_text(pl - 6, gy, text=f"{int(max_val * frac):,}",
                               fill="#4B5563", font=("Arial", 7), anchor="e")

        # Series
        for _label, vals, color in series:
            pts = [(_x(i), _y(v)) for i, v in enumerate(vals)]
            if len(pts) >= 2:
                canvas.create_line(
                    *[c for pt in pts for c in pt],
                    fill=color, width=2, smooth=True,
                )
            for px, py in pts:
                canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="")

        # X-axis timestamps
        for i, record in enumerate(history):
            ts = record.get("timestamp", "")[11:16]
            canvas.create_text(_x(i), h - pb + 10, text=ts,
                               fill="#4B5563", font=("Arial", 7))

        # Legend
        lx = pl
        for label, _, color in series:
            canvas.create_rectangle(lx, pt - 2, lx + 8, pt + 6, fill=color, outline="")
            canvas.create_text(lx + 11, pt + 2, text=label,
                               fill="#9CA3AF", font=("Arial", 8), anchor="w")
            lx += 58

    # ── Pie chart ─────────────────────────────────────────────────────────────
    def _draw_pie_chart(self):
        canvas = self.pie_canvas
        if not canvas:
            return
        canvas.delete("all")

        prompt     = self.token_usage.get("prompt_tokens", 0)
        completion = self.token_usage.get("completion_tokens", 0)
        total      = prompt + completion
        if total == 0:
            canvas.create_text(80, 80, text="Sem dados", fill="#4B5563", font=("Arial", 11))
            return

        w = canvas.winfo_width() or 260
        h = canvas.winfo_height() or 160
        cx, cy = w * 0.36, h / 2
        r = min(cx, cy) - 10

        slices = [
            ("Prompt",     prompt,     "#60A5FA"),
            ("Completion", completion, "#FBBF24"),
        ]

        angle = -90.0
        for label, value, color in slices:
            ext = 360.0 * value / total
            canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=angle, extent=ext,
                fill=color, outline="#0F172A", width=2,
            )
            mid = math.radians(angle + ext / 2)
            tx, ty = cx + r * 0.60 * math.cos(mid), cy + r * 0.60 * math.sin(mid)
            canvas.create_text(tx, ty, text=f"{value / total * 100:.0f}%",
                               fill="#0F172A", font=("Arial", 9, "bold"))
            angle += ext

        # Legend
        lx = cx + r + 16
        for i, (label, value, color) in enumerate(slices):
            ly = cy - 14 + i * 24
            canvas.create_rectangle(lx, ly, lx + 10, ly + 10, fill=color, outline="")
            canvas.create_text(lx + 14, ly + 5, text=f"{label}: {value:,}",
                               fill="#D1D5DB", font=("Arial", 9), anchor="w")

    # ── CSV export ────────────────────────────────────────────────────────────
    def _export_csv(self):
        if not self.usage_history:
            import tkinter.messagebox as mb
            mb.showinfo("Exportar CSV", "Nenhum dado para exportar ainda.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="token_usage.csv",
        )
        if not path:
            return

        import csv
        fields = ["timestamp", "model", "prompt_tokens",
                  "completion_tokens", "total_tokens", "issues", "files"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.usage_history)

        import tkinter.messagebox as mb
        mb.showinfo("Exportar CSV", f"Exportado com sucesso:\n{path}")