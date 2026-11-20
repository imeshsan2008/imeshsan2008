#!/usr/bin/env python3
"""
Master Profile OS Builder for imeshsan2008.
Generates the entire zero-glow, dual-theme (dark & light) Swiss-Industrial SVG Bento System:
  1. Hero Workstation OS Banner (hero-dark/light.svg)
  2. Live Physics Contribution Breakout Arcade (breakout-dark/light.svg) + docs/contrib.json
  3. 4 Individually Clickable Project Bento Cards (proj-*-dark/light.svg)
  4. 3-Panel Live GitHub Telemetry & 12-Week Animated Bar Chart (telemetry-dark/light.svg)
  5. Architectural Capabilities & Career Timeline Blueprint (blueprint-dark/light.svg)
  6. Flat Industrial Hardware Action Dock Keycaps (dock-*.svg)
Pure Python stdlib — zero external dependencies, 100% zero glow/blur.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from breakout_engine import (
    build_grid_from_days,
    render_breakout_svg,
    simulate_breakout,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
USERNAME = os.environ.get("GITHUB_USERNAME", "imeshsan2008")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "surface": "#161B22",
        "inset": "#090C10",
        "border": "#30363D",
        "border_soft": "#21262D",
        "ink": "#E6EDF3",
        "muted": "#8B949E",
        "subtle": "#6E7681",
        "accent": "#DC2626",
        "grid": "#1B212A",
        "bars": ["#DC2626", "#E6EDF3", "#8B949E", "#484F58"],
        "spark_bar": "#30363D",
        "spark_mid": "#6E7681",
        "spark_peak": "#DC2626",
    },
    "light": {
        "bg": "#FFFFFF",
        "surface": "#F6F8FA",
        "inset": "#F3F5F7",
        "border": "#D0D7DE",
        "border_soft": "#E5E9EE",
        "ink": "#1F2328",
        "muted": "#57606A",
        "subtle": "#656D76",
        "accent": "#CC0000",
        "grid": "#EAEEF2",
        "bars": ["#CC0000", "#1F2328", "#656D76", "#B0B8C1"],
        "spark_bar": "#D0D7DE",
        "spark_mid": "#656D76",
        "spark_peak": "#CC0000",
    },
}


def http_get_text(url: str, accept: str | None = None, use_auth: bool = False) -> str:
    headers = {"User-Agent": f"{USERNAME}-profile-os"}
    if accept:
        headers["Accept"] = accept
    if use_auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def gh_json(url: str) -> Any:
    return json.loads(http_get_text(url, accept="application/vnd.github+json", use_auth=True))


def fetch_contributions() -> tuple[list[dict[str, Any]], int, list[int]]:
    """Fetch real GitHub contribution calendar & 12-week activity histogram."""
    try:
        raw = http_get_text(f"https://github.com/users/{USERNAME}/contributions")
        matches = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', raw)
        # Sort chronologically (GitHub table renders row-by-row by weekday!)
        days = sorted(
            [{"date": d, "level": int(lv)} for d, lv in matches],
            key=lambda x: x["date"],
        )
        total_m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", raw)
        total = int(total_m.group(1).replace(",", "")) if total_m else sum(d["level"] * 2 for d in days)

        # Build 12-week activity intensity (last 84 days grouped in 7-day buckets)
        last_84 = days[-84:]
        weekly: list[int] = []
        for i in range(0, len(last_84), 7):
            chunk = last_84[i : i + 7]
            weekly.append(sum(c["level"] for c in chunk))
        while len(weekly) < 12:
            weekly.insert(0, 0)
        return days, total, weekly[-12:]
    except Exception:
        return [], 286, [2, 4, 1, 5, 3, 6, 4, 2, 7, 5, 3, 4]


def fetch_github_metrics() -> dict[str, Any]:
    """Fetch live repo & byte-level language metrics with graceful fallback."""
    fallback = {
        "public_repos": 26,
        "original_repos": 25,
        "public_gists": 12,
        "followers": 2,
        "total_stars": 0,
        "total_forks": 2,
        "total_bytes": 4_512_752,
        "created_year": "2022",
        "languages": [("JavaScript", 62.7), ("HTML", 18.1), ("CSS", 16.6), ("Other", 2.6)],
        "updated_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    try:
        user = gh_json(f"https://api.github.com/users/{USERNAME}")
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = gh_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        orig = [r for r in repos if not r.get("fork")]
        stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
        forks = sum(int(r.get("forks_count", 0)) for r in repos)

        lang_bytes: dict[str, int] = {}
        scanned = 0
        rate_limited = False
        for r in orig:
            lurl = r.get("languages_url")
            if not lurl:
                continue
            try:
                ldata = gh_json(lurl)
                scanned += 1
                for k, v in ldata.items():
                    lang_bytes[k] = lang_bytes.get(k, 0) + int(v)
            except urllib.error.URLError:
                rate_limited = True
                break

        total_bytes = sum(lang_bytes.values())
        if not rate_limited and scanned >= max(1, int(len(orig) * 0.8)) and total_bytes > 0:
            s_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)
            top3 = [(k, round((v / total_bytes) * 100.0, 1)) for k, v in s_langs[:3]]
            rest = sum(v for _, v in s_langs[3:])
            if rest > 0:
                top3.append(("Other", round(max(0.1, 100.0 - sum(p for _, p in top3)), 1)))
            langs = top3
        else:
            total_bytes = fallback["total_bytes"]
            langs = fallback["languages"]

        return {
            "public_repos": int(user.get("public_repos", len(repos))),
            "original_repos": len(orig),
            "public_gists": int(user.get("public_gists", 0)),
            "followers": int(user.get("followers", 0)),
            "total_stars": stars,
            "total_forks": forks,
            "total_bytes": total_bytes,
            "created_year": (user.get("created_at") or "2022")[:4],
            "languages": langs,
            "updated_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    except Exception:
        return fallback


def fmt_bytes(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.0f} KB"
    return f"{n} B"


# ---------------------------------------------------------------------------
# MODULE 01: IMESH // OS HERO WORKSTATION BANNER (900 x 292)
# ---------------------------------------------------------------------------
def render_hero_svg(metrics: dict[str, Any], total_contribs: int, theme: str) -> str:
    t = THEMES[theme]
    vol = fmt_bytes(metrics["total_bytes"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="292" viewBox="0 0 900 292" role="img" aria-label="IMESH OS — Imesh Sandeepa, Founder at Vexora IT Solutions">
  <defs>
    <clipPath id="hero-clip-{theme}">
      <rect x="0.5" y="0.5" width="899" height="291" rx="8" />
    </clipPath>
    <pattern id="hero-grid-{theme}" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="{t['grid']}" stroke-width="1" />
    </pattern>
  </defs>

  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .sysbar {{ font-size: 10px; font-weight: 700; letter-spacing: 1px; fill: {t['muted']}; }}
    .sysbar-hi {{ font-size: 10px; font-weight: 800; letter-spacing: 1px; fill: {t['ink']}; }}
    .name {{ font-size: 42px; font-weight: 900; letter-spacing: -1.1px; fill: {t['ink']}; }}
    .role-txt {{ font-size: 12px; font-weight: 700; letter-spacing: 1.1px; fill: {t['ink']}; }}
    .bio-txt {{ font-size: 13px; font-weight: 500; fill: {t['muted']}; }}
    .kpi-k {{ font-size: 9px; font-weight: 700; letter-spacing: 0.9px; fill: {t['subtle']}; }}
    .kpi-v {{ font-size: 16px; font-weight: 800; fill: {t['ink']}; }}
    .kpi-va {{ font-size: 16px; font-weight: 800; fill: {t['accent']}; }}
    .term-cmd {{ font-size: 10.5px; font-weight: 700; fill: {t['ink']}; }}
    .term-k {{ font-size: 10.5px; font-weight: 700; fill: {t['accent']}; }}
    .term-v {{ font-size: 10.5px; font-weight: 500; fill: {t['muted']}; }}
    @keyframes blinkSq {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0.2; }} }}
    .pulse {{ animation: blinkSq 1.4s steps(2, end) infinite; }}
    @keyframes r1 {{ 0%, 30% {{ opacity: 1; }} 33%, 97% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
    @keyframes r2 {{ 0%, 32% {{ opacity: 0; }} 35%, 63% {{ opacity: 1; }} 66%, 100% {{ opacity: 0; }} }}
    @keyframes r3 {{ 0%, 65% {{ opacity: 0; }} 68%, 96% {{ opacity: 1; }} 99%, 100% {{ opacity: 0; }} }}
    .cycle1 {{ animation: r1 9s linear infinite; }}
    .cycle2 {{ animation: r2 9s linear infinite; opacity: 0; }}
    .cycle3 {{ animation: r3 9s linear infinite; opacity: 0; }}
  </style>

  <g clip-path="url(#hero-clip-{theme})">
    <rect x="0" y="0" width="900" height="292" fill="{t['bg']}" />
    <rect x="0" y="34" width="548" height="258" fill="url(#hero-grid-{theme})" opacity="0.65" />
    <!-- Top OS Status Bar -->
    <rect x="0" y="0" width="900" height="34" fill="{t['surface']}" />
    <line x1="0" y1="34" x2="900" y2="34" stroke="{t['border']}" stroke-width="1" />
    <!-- Right Terminal Hardware Panel -->
    <rect x="548" y="34" width="352" height="258" fill="{t['surface']}" />
    <line x1="548" y1="34" x2="548" y2="292" stroke="{t['border']}" stroke-width="1" />
    <!-- Left flat structural crimson accent strip -->
    <rect x="0" y="0" width="5" height="292" fill="{t['accent']}" />
  </g>

  <!-- Outer 1px border -->
  <rect x="0.5" y="0.5" width="899" height="291" rx="8" fill="none" stroke="{t['border']}" stroke-width="1" />

  <!-- Top OS Bar Readouts -->
  <rect x="20" y="13" width="8" height="8" rx="1" fill="{t['accent']}" />
  <text x="36" y="21" class="mono sysbar-hi">IMESH // OS v2.6</text>
  <text x="168" y="21" class="mono sysbar">KELANIYA, LK  ·  06°57'N 79°55'E  ·  UTC+5:30</text>
  <rect x="708" y="13" width="6" height="6" rx="1" fill="{t['accent']}" class="pulse" />
  <text x="721" y="20.5" class="mono sysbar-hi">ONLINE · OPEN TO BUILD</text>

  <!-- Main Left Identity -->
  <text x="30" y="102" class="sans name">IMESH SANDEEPA<tspan fill="{t['accent']}">.</tspan></text>

  <!-- Live Cycling Role Ticker (crisp flat box) -->
  <rect x="30" y="118" width="486" height="28" rx="3" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="30" y="118" width="3" height="28" fill="{t['accent']}" />
  <text x="44" y="136" class="mono role-txt cycle1">&gt; FOUNDER @ VEXORA IT SOLUTIONS</text>
  <text x="44" y="136" class="mono role-txt cycle2">&gt; FULL-STACK ENGINEER · SAAS &amp; DESKTOP SYSTEMS</text>
  <text x="44" y="136" class="mono role-txt cycle3">&gt; WEB &amp; GRAPHIC DESIGNER · UI ARCHITECTURE</text>

  <text x="30" y="174" class="sans bio-txt">Building scalable SaaS platforms, zero-tracking Chrome extensions,</text>
  <text x="30" y="193" class="sans bio-txt">Python utilities, and sharp visual systems without noise.</text>

  <!-- Bottom Hardware KPI Switches -->
  <g transform="translate(30, 214)">
    <rect x="0" y="0" width="114" height="54" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="12" y="18" class="mono kpi-k">REPOSITORIES</text>
    <text x="12" y="42" class="mono kpi-v">{metrics['public_repos']}</text>

    <rect x="124" y="0" width="114" height="54" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="136" y="18" class="mono kpi-k">12M COMMITS</text>
    <text x="136" y="42" class="mono kpi-va">{total_contribs}</text>

    <rect x="248" y="0" width="114" height="54" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="260" y="18" class="mono kpi-k">CODEBASE</text>
    <text x="260" y="42" class="mono kpi-v">{vol}</text>

    <rect x="372" y="0" width="114" height="54" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="384" y="18" class="mono kpi-k">SINCE</text>
    <text x="384" y="42" class="mono kpi-v">{metrics['created_year']}</text>
  </g>

  <!-- Right Precision Terminal Module -->
  <rect x="570" y="54" width="308" height="156" rx="4" fill="{t['inset']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="570" y="54" width="308" height="24" rx="4" fill="{t['bg']}" />
  <line x1="570" y1="78" x2="878" y2="78" stroke="{t['border']}" stroke-width="1" />
  <text x="582" y="70" class="mono term-cmd">$ whoami --spec</text>
  <rect x="858" y="62" width="10" height="8" rx="1" fill="{t['accent']}" class="pulse" />

  <text x="582" y="100" class="mono term-k">org     </text><text x="646" y="100" class="mono term-v">Vexora IT Solutions (Founder)</text>
  <text x="582" y="121" class="mono term-k">focus   </text><text x="646" y="121" class="mono term-v">SaaS · Extensions · Utilities</text>
  <text x="582" y="142" class="mono term-k">code    </text><text x="646" y="142" class="mono term-v">JS · Python · Node · Postgres</text>
  <text x="582" y="163" class="mono term-k">design  </text><text x="646" y="163" class="mono term-v">UI/UX · PS · AI · CorelDRAW</text>
  <text x="582" y="184" class="mono term-k">deploy  </text><text x="646" y="184" class="mono term-v">DigitalOcean · Koyeb · Linux</text>
  <text x="582" y="201" class="mono kpi-k">STATUS: SHIPPING CLEAN SYSTEMS</text>

  <!-- Bottom-right Mechanical Telemetry Strip (equalizer bars + rotating reticle) -->
  <rect x="570" y="222" width="308" height="46" rx="4" fill="{t['inset']}" stroke="{t['border']}" stroke-width="1" />

  <!-- Flat hardware signal bars (zero glow) -->
  <g transform="translate(584, 232)">
    <rect x="0" y="14" width="5" height="12" rx="1" fill="{t['accent']}"><animate attributeName="height" values="8;24;12;20;8" dur="1.9s" repeatCount="indefinite"/><animate attributeName="y" values="18;2;14;6;18" dur="1.9s" repeatCount="indefinite"/></rect>
    <rect x="9" y="6" width="5" height="20" rx="1" fill="{t['ink']}"><animate attributeName="height" values="20;10;24;12;20" dur="1.5s" repeatCount="indefinite"/><animate attributeName="y" values="6;16;2;14;6" dur="1.5s" repeatCount="indefinite"/></rect>
    <rect x="18" y="10" width="5" height="16" rx="1" fill="{t['muted']}"><animate attributeName="height" values="14;22;6;18;14" dur="2.1s" repeatCount="indefinite"/><animate attributeName="y" values="12;4;20;8;12" dur="2.1s" repeatCount="indefinite"/></rect>
    <rect x="27" y="4" width="5" height="22" rx="1" fill="{t['ink']}"><animate attributeName="height" values="22;8;18;24;22" dur="1.7s" repeatCount="indefinite"/><animate attributeName="y" values="4;18;8;2;4" dur="1.7s" repeatCount="indefinite"/></rect>
    <rect x="36" y="12" width="5" height="14" rx="1" fill="{t['muted']}"><animate attributeName="height" values="10;20;14;6;10" dur="2.3s" repeatCount="indefinite"/><animate attributeName="y" values="16;6;12;20;16" dur="2.3s" repeatCount="indefinite"/></rect>
    <rect x="45" y="8" width="5" height="18" rx="1" fill="{t['accent']}"><animate attributeName="height" values="16;6;22;12;16" dur="1.6s" repeatCount="indefinite"/><animate attributeName="y" values="10;20;4;14;10" dur="1.6s" repeatCount="indefinite"/></rect>
  </g>

  <text x="650" y="242" class="mono term-cmd">SIGNAL // ACTIVE</text>
  <text x="650" y="257" class="mono kpi-k">AUTOMATED PROFILE ENGINE</text>

  <!-- Rotating geometric precision dial -->
  <g transform="translate(850, 245)">
    <circle cx="0" cy="0" r="14" fill="none" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 3">
      <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="18s" repeatCount="indefinite" />
    </circle>
    <rect x="-4" y="-4" width="8" height="8" fill="none" stroke="{t['ink']}" stroke-width="1">
      <animateTransform attributeName="transform" type="rotate" from="360 0 0" to="0 0 0" dur="14s" repeatCount="indefinite" />
    </rect>
    <rect x="-1.5" y="-1.5" width="3" height="3" fill="{t['accent']}" />
  </g>
</svg>
"""


# ---------------------------------------------------------------------------
# MODULE 03: 4 INDIVIDUALLY CLICKABLE BENTO PROJECT CARDS (440 x 182 each)
# ---------------------------------------------------------------------------
PROJECTS = [
    {
        "slug": "myslt",
        "index": "01",
        "category": "CHROME MV3 + WPF",
        "title": "MySLT Tracker",
        "line1": "Open-source browser extension & Windows desktop",
        "line2": "widget to track SLT broadband usage, add-ons &",
        "line3": "billing with 100% local storage & zero tracking.",
        "tags": ["CHROME MV3", "JAVASCRIPT", "WPF"],
        "icon": "gauge",
    },
    {
        "slug": "adobeshield",
        "index": "02",
        "category": "PYTHON DESKTOP",
        "title": "AdobeShield",
        "line1": "Desktop firewall control utility built with",
        "line2": "Python & ttkbootstrap to manage connectivity",
        "line3": "rules cleanly for Adobe Creative Cloud apps.",
        "tags": ["PYTHON", "TTKBOOTSTRAP", "FIREWALL"],
        "icon": "shield",
    },
    {
        "slug": "trainify",
        "index": "03",
        "category": "SAAS PLATFORM",
        "title": "Trainify",
        "line1": "Training management platform designed to",
        "line2": "organize learning schedules, streamline skill",
        "line3": "growth, and monitor task milestones clearly.",
        "tags": ["FULL-STACK", "WEB APP", "SAAS"],
        "icon": "grid",
    },
    {
        "slug": "sharebox",
        "index": "04",
        "category": "OFFLINE P2P",
        "title": "ShareBox",
        "line1": "Zero-internet local file sharing utility over",
        "line2": "Wi-Fi hotspot — transfer files across devices",
        "line3": "rapidly with no router or cloud middleman.",
        "tags": ["PYTHON", "LOCAL NET", "UTILITY"],
        "icon": "nodes",
    },
]


def _project_icon(kind: str, t: dict[str, Any]) -> str:
    if kind == "gauge":
        return (
            f'<rect x="0" y="0" width="44" height="44" rx="4" fill="{t["inset"]}" stroke="{t["border"]}" stroke-width="1"/>'
            f'<path d="M 10 30 A 12 12 0 1 1 34 30" fill="none" stroke="{t["muted"]}" stroke-width="2"/>'
            f'<path d="M 10 30 A 12 12 0 0 1 28 19" fill="none" stroke="{t["accent"]}" stroke-width="2"/>'
            f'<line x1="22" y1="28" x2="30" y2="18" stroke="{t["ink"]}" stroke-width="1.8"/>'
            f'<circle cx="22" cy="28" r="2.5" fill="{t["accent"]}"/>'
        )
    if kind == "shield":
        return (
            f'<rect x="0" y="0" width="44" height="44" rx="4" fill="{t["inset"]}" stroke="{t["border"]}" stroke-width="1"/>'
            f'<polygon points="22,9 33,14 33,24 22,35 11,24 11,14" fill="none" stroke="{t["ink"]}" stroke-width="1.6"/>'
            f'<line x1="22" y1="14" x2="22" y2="29" stroke="{t["accent"]}" stroke-width="1.6"/>'
            f'<line x1="15" y1="21" x2="29" y2="21" stroke="{t["accent"]}" stroke-width="1.6"/>'
        )
    if kind == "grid":
        return (
            f'<rect x="0" y="0" width="44" height="44" rx="4" fill="{t["inset"]}" stroke="{t["border"]}" stroke-width="1"/>'
            f'<rect x="10" y="10" width="10" height="10" rx="1" fill="{t["accent"]}"/>'
            f'<rect x="24" y="10" width="10" height="10" rx="1" fill="none" stroke="{t["ink"]}" stroke-width="1.5"/>'
            f'<rect x="10" y="24" width="10" height="10" rx="1" fill="none" stroke="{t["muted"]}" stroke-width="1.5"/>'
            f'<rect x="24" y="24" width="10" height="10" rx="1" fill="{t["ink"]}"/>'
        )
    return (
        f'<rect x="0" y="0" width="44" height="44" rx="4" fill="{t["inset"]}" stroke="{t["border"]}" stroke-width="1"/>'
        f'<line x1="14" y1="30" x2="22" y2="14" stroke="{t["muted"]}" stroke-width="1.4"/>'
        f'<line x1="30" y1="30" x2="22" y2="14" stroke="{t["muted"]}" stroke-width="1.4"/>'
        f'<line x1="14" y1="30" x2="30" y2="30" stroke="{t["muted"]}" stroke-width="1.4"/>'
        f'<circle cx="22" cy="14" r="3.5" fill="{t["accent"]}"/>'
        f'<circle cx="14" cy="30" r="3" fill="{t["ink"]}"/>'
        f'<circle cx="30" cy="30" r="3" fill="{t["ink"]}"/>'
    )


def render_project_card(proj: dict[str, Any], theme: str) -> str:
    t = THEMES[theme]
    chips: list[str] = []
    cx = 22
    for idx, tag in enumerate(proj["tags"]):
        w = max(62, len(tag) * 7 + 18)
        accent_bar = f'<rect x="{cx}" y="140" width="2.5" height="22" fill="{t["accent"]}"/>' if idx == 0 else ""
        chips.append(
            f'<rect x="{cx}" y="140" width="{w}" height="22" rx="3" fill="{t["inset"]}" stroke="{t["border"]}" stroke-width="1"/>'
            f"{accent_bar}"
            f'<text x="{cx + w / 2:.1f}" y="154.5" text-anchor="middle" class="mono tag">{tag}</text>'
        )
        cx += w + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="440" height="182" viewBox="0 0 440 182" role="img" aria-label="{html.escape(proj['title'])} — {html.escape(proj['category'])}">
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .idx {{ font-size: 10px; font-weight: 800; letter-spacing: 0.9px; fill: {t['accent']}; }}
    .cat {{ font-size: 10px; font-weight: 600; letter-spacing: 0.9px; fill: {t['subtle']}; }}
    .title {{ font-size: 19px; font-weight: 800; letter-spacing: -0.3px; fill: {t['ink']}; }}
    .desc {{ font-size: 12px; font-weight: 500; fill: {t['muted']}; }}
    .tag {{ font-size: 9.5px; font-weight: 700; letter-spacing: 0.6px; fill: {t['ink']}; }}
    .arrow {{ font-size: 14px; font-weight: 700; fill: {t['muted']}; }}
  </style>

  <rect x="0.5" y="0.5" width="439" height="181" rx="8" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="0.5" y="0.5" width="439" height="32" rx="8" fill="{t['bg']}" />
  <rect x="0.5" y="24" width="439" height="9" fill="{t['bg']}" />
  <line x1="0" y1="33" x2="440" y2="33" stroke="{t['border']}" stroke-width="1" />

  <text x="22" y="21" class="mono idx">{html.escape(proj['index'])}</text>
  <text x="44" y="21" class="mono cat">/  {html.escape(proj['category'])}</text>
  <text x="418" y="22" text-anchor="end" class="mono arrow">↗</text>

  <!-- Schematic Icon -->
  <g transform="translate(22, 48)">
    {_project_icon(proj['icon'], t)}
  </g>

  <text x="80" y="66" class="sans title">{html.escape(proj['title'])}</text>
  <text x="80" y="86" class="sans desc">{html.escape(proj['line1'])}</text>
  <text x="80" y="103" class="sans desc">{html.escape(proj['line2'])}</text>
  <text x="80" y="120" class="sans desc">{html.escape(proj['line3'])}</text>

  {''.join(chips)}
</svg>
"""


# ---------------------------------------------------------------------------
# MODULE 04: 3-PANEL LIVE TELEMETRY & 12-WEEK ANIMATED SPARKLINE (900 x 268)
# ---------------------------------------------------------------------------
def render_telemetry_svg(
    metrics: dict[str, Any],
    total_contribs: int,
    weekly_bars: list[int],
    theme: str,
) -> str:
    t = THEMES[theme]
    langs = metrics["languages"]
    vol = fmt_bytes(metrics["total_bytes"])

    # 12-week animated vertical bar chart (Panel B: x=316..594, y=68..184)
    max_wk = max(max(weekly_bars), 1)
    peak_idx = weekly_bars.index(max(weekly_bars))
    bars_svg: list[str] = []
    bar_base_y = 182.0
    max_bar_h = 104.0
    for i, val in enumerate(weekly_bars):
        bx = 324 + i * 22
        h = max(8.0, (val / max_wk) * max_bar_h)
        by = bar_base_y - h
        if i == peak_idx:
            fill = t["spark_peak"]
        elif val >= max_wk * 0.55:
            fill = t["spark_mid"]
        else:
            fill = t["spark_bar"]
        delay = f"{i * 0.06:.2f}s"
        bars_svg.append(
            f'<rect x="{bx}" y="{by:.1f}" width="14" height="{h:.1f}" rx="1.5" fill="{fill}">'
            f'<animate attributeName="height" from="4" to="{h:.1f}" dur="0.55s" begin="{delay}" fill="freeze" />'
            f'<animate attributeName="y" from="{bar_base_y - 4:.1f}" to="{by:.1f}" dur="0.55s" begin="{delay}" fill="freeze" />'
            f"</rect>"
        )

    # Language segmented horizontal bar (Panel C: x=626..874, width=248)
    seg_x = 626.0
    seg_w_total = 248.0
    gap = 2.0
    usable = seg_w_total - gap * max(0, len(langs) - 1)
    segs: list[str] = []
    rows_svg: list[str] = []
    curr = seg_x
    for idx, (name, pct) in enumerate(langs[:4]):
        sw = max(4.0, usable * (pct / 100.0))
        if idx == len(langs) - 1:
            sw = max(4.0, (seg_x + seg_w_total) - curr)
        color = t["bars"][idx % len(t["bars"])]
        segs.append(f'<rect x="{curr:.1f}" y="66" width="{sw:.1f}" height="10" rx="1.5" fill="{color}" />')
        curr += sw + gap

        ry = 104 + idx * 25
        rows_svg.append(
            f'<rect x="626" y="{ry - 9}" width="8" height="8" rx="1" fill="{color}" />'
            f'<text x="642" y="{ry - 1}" class="sans lang-n">{name}</text>'
            f'<text x="874" y="{ry - 1}" text-anchor="end" class="mono lang-p">{pct:.1f}%</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="268" viewBox="0 0 900 268" role="img" aria-label="GitHub Telemetry, 12-Week Activity and Language Distribution">
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .hdr {{ font-size: 10px; font-weight: 800; letter-spacing: 1.1px; fill: {t['subtle']}; }}
    .k {{ font-size: 9px; font-weight: 700; letter-spacing: 0.9px; fill: {t['muted']}; }}
    .v {{ font-size: 19px; font-weight: 800; fill: {t['ink']}; }}
    .va {{ font-size: 19px; font-weight: 800; fill: {t['accent']}; }}
    .lang-n {{ font-size: 12px; font-weight: 600; fill: {t['ink']}; }}
    .lang-p {{ font-size: 11.5px; font-weight: 700; fill: {t['muted']}; }}
    .foot {{ font-size: 9.5px; font-weight: 600; letter-spacing: 0.8px; fill: {t['subtle']}; }}
  </style>

  <rect x="0.5" y="0.5" width="899" height="267" rx="8" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1" />

  <!-- Panel dividers -->
  <line x1="296" y1="18" x2="296" y2="218" stroke="{t['border_soft']}" stroke-width="1" />
  <line x1="604" y1="18" x2="604" y2="218" stroke="{t['border_soft']}" stroke-width="1" />

  <!-- PANEL A: CORE KPIs -->
  <rect x="24" y="24" width="3" height="12" fill="{t['accent']}" />
  <text x="34" y="34" class="mono hdr">TELEMETRY // LIVE</text>

  <g transform="translate(24, 52)">
    <rect x="0" y="0" width="120" height="68" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="12" y="20" class="mono k">PUBLIC REPOS</text>
    <text x="12" y="52" class="mono v">{metrics['public_repos']}</text>

    <rect x="130" y="0" width="120" height="68" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="142" y="20" class="mono k">ORIGINAL</text>
    <text x="142" y="52" class="mono v">{metrics['original_repos']}</text>

    <rect x="0" y="78" width="120" height="68" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="12" y="98" class="mono k">CODE VOLUME</text>
    <text x="12" y="130" class="mono va">{vol}</text>

    <rect x="130" y="78" width="120" height="68" rx="4" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
    <text x="142" y="98" class="mono k">PUBLIC GISTS</text>
    <text x="142" y="130" class="mono v">{metrics['public_gists']}</text>
  </g>

  <!-- PANEL B: 12-WEEK ACTIVITY HISTOGRAM -->
  <rect x="318" y="24" width="3" height="12" fill="{t['accent']}" />
  <text x="328" y="34" class="mono hdr">12-WEEK PULSE ({total_contribs}/YR)</text>

  <!-- Subtle horizontal baseline grid -->
  <line x1="318" y1="80" x2="586" y2="80" stroke="{t['border_soft']}" stroke-width="1" stroke-dasharray="2 4" />
  <line x1="318" y1="131" x2="586" y2="131" stroke="{t['border_soft']}" stroke-width="1" stroke-dasharray="2 4" />
  <line x1="318" y1="182" x2="586" y2="182" stroke="{t['border']}" stroke-width="1" />

  {''.join(bars_svg)}

  <text x="324" y="202" class="mono k">W-12</text>
  <text x="452" y="202" text-anchor="middle" class="mono k">PEAK IN CRIMSON</text>
  <text x="582" y="202" text-anchor="end" class="mono k">NOW</text>

  <!-- PANEL C: CODEBASE DISTRIBUTION -->
  <rect x="626" y="24" width="3" height="12" fill="{t['accent']}" />
  <text x="636" y="34" class="mono hdr">CODEBASE MIX</text>

  {''.join(segs)}
  {''.join(rows_svg)}

  <!-- Footer bar -->
  <line x1="0" y1="228" x2="900" y2="228" stroke="{t['border_soft']}" stroke-width="1" />
  <text x="24" y="252" class="mono foot">MEMBER SINCE {metrics['created_year']}  ·  FORKS: {metrics['total_forks']}  ·  STARS: {metrics['total_stars']}  ·  FOLLOWERS: {metrics['followers']}</text>
  <text x="876" y="252" text-anchor="end" class="mono foot">AUTO-SYNCED VIA GITHUB ACTIONS · {metrics['updated_date']} UTC</text>
</svg>
"""


# ---------------------------------------------------------------------------
# MODULE 05: CAPABILITIES & CAREER TIMELINE BLUEPRINT (900 x 308)
# ---------------------------------------------------------------------------
def render_blueprint_svg(theme: str) -> str:
    t = THEMES[theme]
    tracks = [
        ("01", "FRONTEND & UI", "HTML5 · CSS3 · JavaScript · Tailwind · Bootstrap", 9),
        ("02", "BACKEND & SYSTEMS", "Node.js · Python · PostgreSQL · REST · Chrome MV3", 8),
        ("03", "DESIGN & VISUALS", "UI/UX · Photoshop · Illustrator · Lightroom · CorelDRAW", 9),
        ("04", "CLOUD & DEVOPS", "DigitalOcean · Koyeb · Git · GitHub Actions · Linux", 8),
    ]

    track_svg: list[str] = []
    for idx, (num, title, items, ticks) in enumerate(tracks):
        ty = 58 + idx * 58
        blocks = "".join(
            f'<rect x="{354 + k * 9}" y="{ty + 4}" width="6" height="9" rx="1" '
            f'fill="{t["accent"] if (k < ticks and idx == 0) else (t["ink"] if k < ticks else t["border_soft"])}" />'
            for k in range(10)
        )
        track_svg.append(
            f'<rect x="24" y="{ty - 6}" width="426" height="48" rx="4" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1" />'
            f'<text x="36" y="{ty + 12}" class="mono idx">{html.escape(num)}</text>'
            f'<text x="58" y="{ty + 12}" class="mono cap-t">{html.escape(title)}</text>'
            f"{blocks}"
            f'<text x="36" y="{ty + 31}" class="sans cap-s">{html.escape(items)}</text>'
        )

    milestones = [
        ("2026 — NOW", "Founder", "Vexora IT Solutions · SaaS & Full-Stack Systems", True),
        ("2025", "Graphic Design Intern", "National Productivity Secretariat · Branding & UI", False),
        ("2025", "NVQ Level 4 — Graphic Design", "Maradana Technical College · Visual Communication", False),
        ("CERTIFIED", "Professional Benchmarking", "Global Benchmarking Network · Industry Standards", False),
    ]

    ms_svg: list[str] = []
    for idx, (yr, role, org, active) in enumerate(milestones):
        my = 64 + idx * 58
        node_fill = t["accent"] if active else t["bg"]
        node_stroke = t["accent"] if active else t["ink"]
        pulse_cls = ' class="pulse"' if active else ""
        ms_svg.append(
            f'<rect x="492" y="{my}" width="10" height="10" rx="1.5" fill="{node_fill}" stroke="{node_stroke}" stroke-width="1.5"{pulse_cls} />'
            f'<text x="516" y="{my + 9}" class="mono yr" fill="{t["accent"] if active else t["subtle"]}">{html.escape(yr)}</text>'
            f'<text x="606" y="{my + 9}" class="sans m-role">{html.escape(role)}</text>'
            f'<text x="516" y="{my + 28}" class="sans m-org">{html.escape(org)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="308" viewBox="0 0 900 308" role="img" aria-label="System Capabilities and Career Timeline">
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .hdr {{ font-size: 10px; font-weight: 800; letter-spacing: 1.1px; fill: {t['subtle']}; }}
    .idx {{ font-size: 10px; font-weight: 800; fill: {t['accent']}; }}
    .cap-t {{ font-size: 11px; font-weight: 800; letter-spacing: 0.7px; fill: {t['ink']}; }}
    .cap-s {{ font-size: 11px; font-weight: 500; fill: {t['muted']}; }}
    .yr {{ font-size: 9.5px; font-weight: 800; letter-spacing: 0.7px; }}
    .m-role {{ font-size: 13px; font-weight: 800; fill: {t['ink']}; }}
    .m-org {{ font-size: 11px; font-weight: 500; fill: {t['muted']}; }}
    @keyframes blinkSq {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0.35; }} }}
    .pulse {{ animation: blinkSq 1.5s steps(2, end) infinite; }}
  </style>

  <rect x="0.5" y="0.5" width="899" height="307" rx="8" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1" />
  <line x1="472" y1="20" x2="472" y2="288" stroke="{t['border_soft']}" stroke-width="1" />

  <!-- Left Header -->
  <rect x="24" y="24" width="3" height="12" fill="{t['accent']}" />
  <text x="34" y="34" class="mono hdr">SYSTEM CAPABILITIES // STACK MATRIX</text>
  {''.join(track_svg)}

  <!-- Right Header -->
  <rect x="494" y="24" width="3" height="12" fill="{t['accent']}" />
  <text x="504" y="34" class="mono hdr">TRAJECTORY // EXPERIENCE &amp; CREDENTIALS</text>

  <!-- Vertical timeline rail -->
  <line x1="497" y1="69" x2="497" y2="243" stroke="{t['border']}" stroke-width="1.5" />
  {''.join(ms_svg)}
</svg>
"""


# ---------------------------------------------------------------------------
# MODULE 06: BESPOKE FLAT HARDWARE ACTION DOCK KEYCAPS
# ---------------------------------------------------------------------------
def render_dock_buttons() -> None:
    specs = [
        ("dock-arcade.svg", "▶ PLAY 60FPS ARCADE", 190, True),
        ("dock-portfolio.svg", "PORTFOLIO ↗", 122, False),
        ("dock-linkedin.svg", "LINKEDIN", 104, False),
        ("dock-instagram.svg", "INSTAGRAM", 112, False),
        ("dock-gmail.svg", "GMAIL", 84, False),
        ("dock-whatsapp.svg", "WHATSAPP", 106, False),
    ]
    for fname, label, w, primary in specs:
        bg = "#CC0000" if primary else "#161B22"
        border = "#991B1B" if primary else "#30363D"
        top_bar = "" if primary else f'<rect x="1" y="1" width="{w - 2}" height="2.5" rx="1" fill="#DC2626" />'
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="34" viewBox="0 0 {w} 34" role="img" aria-label="{label}">
  <rect x="0.5" y="0.5" width="{w - 1}" height="33" rx="4" fill="{bg}" stroke="{border}" stroke-width="1" />
  {top_bar}
  <text x="{w / 2:.1f}" y="21.5" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" font-size="11" font-weight="800" letter-spacing="0.8" fill="#FFFFFF">{label}</text>
</svg>
"""
        (ASSETS / fname).write_text(svg, encoding="utf-8")


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    days, total_contribs, weekly_bars = fetch_contributions()
    metrics = fetch_github_metrics()

    # 1. Breakout simulation from real GitHub contributions
    grid = build_grid_from_days(days)
    sim = simulate_breakout(grid)

    # Export contribution grid for the playable 60fps GitHub Pages Arcade!
    contrib_payload = {
        "username": USERNAME,
        "total_contributions": total_contribs,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows": len(grid),
        "cols": len(grid[0]),
        "grid": grid,
    }
    (DOCS / "contrib.json").write_text(json.dumps(contrib_payload, separators=(",", ":")), encoding="utf-8")

    # 2. Generate all dual-theme SVGs
    for theme in ("dark", "light"):
        (ASSETS / f"hero-{theme}.svg").write_text(
            render_hero_svg(metrics, total_contribs, theme), encoding="utf-8"
        )
        (ASSETS / f"breakout-{theme}.svg").write_text(
            render_breakout_svg(sim, total_contribs, theme), encoding="utf-8"
        )
        (ASSETS / f"telemetry-{theme}.svg").write_text(
            render_telemetry_svg(metrics, total_contribs, weekly_bars, theme), encoding="utf-8"
        )
        (ASSETS / f"blueprint-{theme}.svg").write_text(
            render_blueprint_svg(theme), encoding="utf-8"
        )
        for proj in PROJECTS:
            (ASSETS / f"proj-{proj['slug']}-{theme}.svg").write_text(
                render_project_card(proj, theme), encoding="utf-8"
            )

    # 3. Hardware dock buttons
    render_dock_buttons()

    print(
        f"BUILT IMESH // OS PROFILE: contribs={total_contribs}, breakout_hits={len(sim['hits'])}/{sim['active_total']}, "
        f"repos={metrics['public_repos']}, langs={metrics['languages']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
