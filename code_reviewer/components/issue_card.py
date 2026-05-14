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

    return card
