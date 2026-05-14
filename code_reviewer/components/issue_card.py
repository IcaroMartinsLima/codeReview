import customtkinter as ctk

from ..constants import TYPE_COLORS, TYPE_LABELS, SEV_COLORS, SEV_LABELS


def create_issue_card(parent, issue):
    itype = issue.get("type", "quality")
    accent, bg = TYPE_COLORS.get(itype, ("#60A5FA", "#0A1628"))
    sev = issue.get("severity", "medium")

    card = ctk.CTkFrame(parent, fg_color=("#1E293B", "#1E293B"), corner_radius=10)
    card.pack(fill="x", pady=4, padx=2)
    card.grid_columnconfigure(0, weight=1)

    bar = ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=0)
    bar.place(relx=0, rely=0, relheight=1, anchor="nw")

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.pack(fill="x", padx=(14, 12), pady=10)
    inner.grid_columnconfigure(0, weight=1)

    # ── Top row: badges + file info + toggle ─────────────────────────────────
    top = ctk.CTkFrame(inner, fg_color="transparent")
    top.grid(row=0, column=0, sticky="ew")
    top.grid_columnconfigure(1, weight=1)

    badges = ctk.CTkFrame(top, fg_color="transparent")
    badges.grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
        badges, text=TYPE_LABELS.get(itype, itype),
        fg_color=bg, corner_radius=6,
        text_color=accent, font=ctk.CTkFont(size=11, weight="bold"),
        padx=8, pady=2,
    ).pack(side="left", padx=(0, 6))

    ctk.CTkLabel(
        badges, text=SEV_LABELS.get(sev, sev),
        fg_color="#1F2937", corner_radius=6,
        text_color=SEV_COLORS.get(sev, "#D1D5DB"),
        font=ctk.CTkFont(size=11), padx=8, pady=2,
    ).pack(side="left")

    right_meta = ctk.CTkFrame(top, fg_color="transparent")
    right_meta.grid(row=0, column=1, sticky="e")

    file_label = issue.get("file", "")
    line_label = issue.get("line", "?")
    ctk.CTkLabel(
        right_meta, text=f"📄 {file_label}  L{line_label}",
        text_color="#4B5563", font=ctk.CTkFont(size=11),
    ).pack(side="left", padx=(0, 10))

    toggle_btn = ctk.CTkButton(
        right_meta, text="▼ detalhes", width=96, height=24,
        fg_color="transparent", hover_color="#1F2937",
        font=ctk.CTkFont(size=11), text_color="#6B7280",
        border_width=1, border_color="#2D3748", corner_radius=6,
    )
    toggle_btn.pack(side="left")

    # ── Title (always visible) ────────────────────────────────────────────────
    ctk.CTkLabel(
        inner, text=issue.get("title", ""), anchor="w",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="#F1F5F9",
    ).grid(row=1, column=0, sticky="w", pady=(6, 0))

    # ── Collapsible details ───────────────────────────────────────────────────
    details = ctk.CTkFrame(inner, fg_color="transparent")
    details.grid_columnconfigure(0, weight=1)
    _expanded = [False]

    def _copy(widget, text):
        widget.clipboard_clear()
        widget.clipboard_append(text)

    def _build_details():
        for w in details.winfo_children():
            w.destroy()

        # Description
        desc = issue.get("description", "").strip()
        if desc:
            ctk.CTkLabel(
                details, text=desc, anchor="w",
                font=ctk.CTkFont(size=12), text_color="#94A3B8",
                wraplength=700,
            ).grid(row=0, column=0, sticky="w", pady=(2, 0))

        # Snippet
        snippet = issue.get("snippet", "").strip()
        if snippet:
            snip_frame = ctk.CTkFrame(details, fg_color="#0D1B2A", corner_radius=8)
            snip_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
            snip_frame.grid_columnconfigure(0, weight=1)

            # Header bar
            snip_header = ctk.CTkFrame(snip_frame, fg_color="#0F172A", corner_radius=0)
            snip_header.grid(row=0, column=0, sticky="ew")
            snip_header.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                snip_header, text="código", anchor="w",
                font=ctk.CTkFont(size=10), text_color="#4B5563",
            ).grid(row=0, column=0, sticky="w", padx=10, pady=3)
            ctk.CTkButton(
                snip_header, text="📋 copiar", width=68, height=20,
                fg_color="transparent", hover_color="#1F2937",
                font=ctk.CTkFont(size=10), text_color="#6B7280",
                corner_radius=4,
                command=lambda s=snippet: _copy(snip_header, s),
            ).grid(row=0, column=1, sticky="e", padx=6, pady=3)

            ctk.CTkLabel(
                snip_frame, text=snippet, anchor="w",
                font=ctk.CTkFont(family="Courier", size=12),
                text_color="#7DD3FC",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 10))

        # Suggestion
        suggestion = issue.get("suggestion", "").strip()
        if suggestion:
            sug_frame = ctk.CTkFrame(details, fg_color="#071A12", corner_radius=8)
            sug_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
            sug_frame.grid_columnconfigure(0, weight=1)

            sug_header = ctk.CTkFrame(sug_frame, fg_color="#0A1F17", corner_radius=0)
            sug_header.grid(row=0, column=0, sticky="ew")
            sug_header.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                sug_header, text="sugestão", anchor="w",
                font=ctk.CTkFont(size=10), text_color="#4B5563",
            ).grid(row=0, column=0, sticky="w", padx=10, pady=3)
            ctk.CTkButton(
                sug_header, text="📋 copiar", width=68, height=20,
                fg_color="transparent", hover_color="#1A2F27",
                font=ctk.CTkFont(size=10), text_color="#6B7280",
                corner_radius=4,
                command=lambda s=suggestion: _copy(sug_header, s),
            ).grid(row=0, column=1, sticky="e", padx=6, pady=3)

            ctk.CTkLabel(
                sug_frame, text=f"💡 {suggestion}", anchor="w",
                font=ctk.CTkFont(size=12), text_color="#6EE7B7",
                wraplength=680,
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 10))

    def _toggle():
        _expanded[0] = not _expanded[0]
        if _expanded[0]:
            _build_details()
            details.grid(row=2, column=0, sticky="ew", pady=(6, 0))
            toggle_btn.configure(text="▲ ocultar")
        else:
            details.grid_remove()
            toggle_btn.configure(text="▼ detalhes")

    toggle_btn.configure(command=_toggle)
    return card