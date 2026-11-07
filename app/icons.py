"""Lucide icons (https://lucide.dev, ISC licence) as inline SVG, plus avatar SVG files.

Streamlit buttons can't render custom SVG, so buttons use plain text; everything rendered as HTML
(headings, cards, chips, step bar, streaks) uses these icons.
"""
from __future__ import annotations

from pathlib import Path

PATHS = {  # Lucide 24x24 stroke icons
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "house": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "book-open": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "library": '<path d="m16 6 4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/>',
    "megaphone": '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "smile": '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "circle-x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "circle-dot": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "compass": '<path d="m16.24 7.76-1.804 5.411a2 2 0 0 1-1.265 1.265L7.76 16.24l1.804-5.411a2 2 0 0 1 1.265-1.265z"/><circle cx="12" cy="12" r="10"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "lightbulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
}
CREDIT = "Icons: Lucide (lucide.dev, ISC licence)"


def ic(name: str, size: int = 18, color: str = "currentColor", stroke: float = 2) -> str:
    """Inline Lucide icon for HTML strings (use with unsafe_allow_html=True)."""
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
            f"stroke='{color}' stroke-width='{stroke}' stroke-linecap='round' stroke-linejoin='round' "
            f"style='vertical-align:-3px;margin-right:6px'>{PATHS[name]}</svg>")


def dot(band: str) -> str:
    """Coloured square for a mastery band (replaces the coloured-square emojis)."""
    c = {"solid": "#1f9d55", "shaky": "#d9a21b", "weak": "#d64545"}.get(band, "#9aa1a9")
    return (f"<span style='display:inline-block;width:11px;height:11px;border-radius:3px;background:{c};"
            "margin-right:7px;vertical-align:0'></span>")


ASSETS = Path(__file__).resolve().parent / "assets"


def _avatar_svg(name: str, bg: str, fg: str = "#ffffff") -> str:
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>"
            f"<circle cx='32' cy='32' r='32' fill='{bg}'/>"
            f"<g transform='translate(16 16) scale(1.3333)' fill='none' stroke='{fg}' stroke-width='2' "
            f"stroke-linecap='round' stroke-linejoin='round'>{PATHS[name]}</g></svg>")


def avatar(kind: str) -> str:
    """Path to an avatar image: 'matteo' (green, smile) or 'student' (grey, user)."""
    ASSETS.mkdir(exist_ok=True)
    spec = {"matteo": ("smile", "#00a651"), "student": ("user", "#6e6e73"), "logo": ("smile", "#00a651")}[kind]
    p = ASSETS / f"{kind}.svg"
    if not p.exists():
        p.write_text(_avatar_svg(*spec), encoding="utf-8")
    return str(p)
