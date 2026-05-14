import tkinter as tk
import customtkinter as ctk


class ReportPanel(ctk.CTkFrame):
    def __init__(self, parent, token_usage=None, usage_history=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.token_usage = token_usage or {}
        self.usage_history = usage_history or []
        self.chart_canvas = None
        self._render()

    def update(self, token_usage, usage_history):
        self.token_usage = token_usage or {}
        self.usage_history = usage_history or []
        self._render()

    def _render(self):
        for widget in self.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self,
            text="Relatório completo de tokens",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F1F5F9"
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        if not self.token_usage:
            ctk.CTkLabel(
                self,
                text="Nenhum relatório disponível ainda. Faça uma análise para gerar dados.",
                text_color="#94A3B8",
                font=ctk.CTkFont(size=13)
            ).grid(row=1, column=0, sticky="w", pady=20)
            return

        summary_frame = ctk.CTkFrame(self, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
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

        chart_frame = ctk.CTkFrame(self, fg_color=("#111827", "#111827"), corner_radius=12)
        chart_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.chart_canvas = tk.Canvas(chart_frame, height=220, bg="#0F172A", highlightthickness=0)
        self.chart_canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.chart_canvas.bind("<Configure>", lambda event: self._draw_usage_chart())
        self._draw_usage_chart()

        history_frame = ctk.CTkFrame(self, fg_color=("#1E293B", "#1E293B"), corner_radius=12)
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
            self,
            text="Histórico salvo em token_usage.json",
            text_color="#6B7280",
            font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, sticky="w", pady=(10, 10), padx=10)

    def _draw_usage_chart(self):
        if self.chart_canvas is None:
            return

        canvas = self.chart_canvas
        canvas.delete("all")

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
