import customtkinter as ctk

from ..constants import TYPE_COLORS, TYPE_LABELS, SEV_COLORS, SEV_LABELS


def create_issue_card(parent, issue):
    itype     = issue.get("type", "quality")
    accent, bg = TYPE_COLORS.get(itype, ("#60A5FA", "#0A1628"))
    sev       = issue.get("severity", "medium")
    sev_color = SEV_COLORS.get(sev, "#D1D5DB")

    # ── Outer card ────────────────────────────────────────────────────────────
    card = ctk.CTkFrame(parent, fg_color=("#1E293B", "#1E293B"), corner_radius=10)
    card.pack(fill="x", pady=(0, 6), padx=2)

    # Horizontal split: accent bar | content
    bar = ctk.CTkFrame(card, fg_color=accent, width=6, corner_radius=0)
    bar.pack(side="left", fill="y")
    bar.pack_propagate(False)

    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

    # ── Header row: badges (left) + file/toggle (right) ───────────────────────
    header = ctk.CTkFrame(content, fg_color="transparent")
    header.pack(fill="x")

    badges = ctk.CTkFrame(header, fg_color="transparent")
    badges.pack(side="left")

    ctk.CTkLabel(
        badges,
        text=TYPE_LABELS.get(itype, itype),
        fg_color=bg, corner_radius=6,
        text_color=accent,
        font=ctk.CTkFont(size=11, weight="bold"),
        padx=8, pady=2,
    ).pack(side="left", padx=(0, 8))

    ctk.CTkLabel(
        badges,
        text=f"● {SEV_LABELS.get(sev, sev)}",
        font=ctk.CTkFont(size=11),
        text_color=sev_color,
    ).pack(side="left")

    # Right side: file info + toggle button
    right = ctk.CTkFrame(header, fg_color="transparent")
    right.pack(side="right")

    file_label = issue.get("file", "")
    line_label = issue.get("line", "?")
    if file_label:
        ctk.CTkLabel(
            right,
            text=f"{file_label}  :{line_label}",
            text_color="#4B5563",
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(0, 8))

    toggle_btn = ctk.CTkButton(
        right,
        text="▼",
        width=28, height=22,
        fg_color="#111827", hover_color="#1F2937",
        font=ctk.CTkFont(size=11),
        text_color="#6B7280",
        border_width=0,
        corner_radius=6,
    )
    toggle_btn.pack(side="left")

    # ── Title ─────────────────────────────────────────────────────────────────
    ctk.CTkLabel(
        content,
        text=issue.get("title", ""),
        anchor="w",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color="#F1F5F9",
    ).pack(fill="x", pady=(6, 0))

    # ── Collapsible details ───────────────────────────────────────────────────
    details = ctk.CTkFrame(content, fg_color="transparent")
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
            ).pack(fill="x", pady=(4, 0))

        # Snippet
        snippet = issue.get("snippet", "").strip()
        if snippet:
            snip_frame = ctk.CTkFrame(details, fg_color="#0D1B2A", corner_radius=8)
            snip_frame.pack(fill="x", pady=(8, 0))

            snip_hdr = ctk.CTkFrame(snip_frame, fg_color="#0F172A", corner_radius=0)
            snip_hdr.pack(fill="x")

            ctk.CTkLabel(
                snip_hdr, text="código", anchor="w",
                font=ctk.CTkFont(size=10), text_color="#4B5563",
            ).pack(side="left", padx=10, pady=3)

            ctk.CTkButton(
                snip_hdr, text="📋 copiar", width=68, height=20,
                fg_color="transparent", hover_color="#1F2937",
                font=ctk.CTkFont(size=10), text_color="#6B7280",
                corner_radius=4,
                command=lambda s=snippet: _copy(snip_hdr, s),
            ).pack(side="right", padx=6, pady=3)

            ctk.CTkLabel(
                snip_frame, text=snippet, anchor="w",
                font=ctk.CTkFont(family="Courier", size=12),
                text_color="#7DD3FC",
            ).pack(fill="x", padx=12, pady=(4, 10))

        # Suggestion
        suggestion = issue.get("suggestion", "").strip()
        if suggestion:
            sug_frame = ctk.CTkFrame(details, fg_color="#071A12", corner_radius=8)
            sug_frame.pack(fill="x", pady=(8, 0))

            sug_hdr = ctk.CTkFrame(sug_frame, fg_color="#0A1F17", corner_radius=0)
            sug_hdr.pack(fill="x")

            ctk.CTkLabel(
                sug_hdr, text="sugestão", anchor="w",
                font=ctk.CTkFont(size=10), text_color="#4B5563",
            ).pack(side="left", padx=10, pady=3)

            ctk.CTkButton(
                sug_hdr, text="📋 copiar", width=68, height=20,
                fg_color="transparent", hover_color="#1A2F27",
                font=ctk.CTkFont(size=10), text_color="#6B7280",
                corner_radius=4,
                command=lambda s=suggestion: _copy(sug_hdr, s),
            ).pack(side="right", padx=6, pady=3)

            ctk.CTkLabel(
                sug_frame, text=f"💡 {suggestion}", anchor="w",
                font=ctk.CTkFont(size=12), text_color="#6EE7B7",
                wraplength=680,
            ).pack(fill="x", padx=12, pady=(4, 10))

    def _toggle():
        _expanded[0] = not _expanded[0]
        if _expanded[0]:
            _build_details()
            details.pack(fill="x", pady=(8, 0))
            toggle_btn.configure(text="▲")
        else:
            details.pack_forget()
            toggle_btn.configure(text="▼")

    toggle_btn.configure(command=_toggle)
    return card