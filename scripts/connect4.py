#!/usr/bin/env python3
"""
Interactive Connect Four engine for GitHub Profile README.
- Pure Python standard library (zero external dependencies)
- Depth-5 Minimax AI with Alpha-Beta pruning
- Dual-theme (dark & light) flat-editorial SVG renderer (zero glow/blur)
- Automatic README.md game section updater
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "game" / "state.json"
ASSETS_DIR = ROOT / "assets"
README_PATH = ROOT / "README.md"

REPO_SLUG = "imeshsan2008/imeshsan2008"
ROWS = 6
COLS = 7
EMPTY = 0
HUMAN = 1
AI = 2
AI_DEPTH = 5

START_MARKER = "<!-- CONNECT4:START -->"
END_MARKER = "<!-- CONNECT4:END -->"

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "surface": "#161B22",
        "surface_alt": "#0D1117",
        "border": "#30363D",
        "border_soft": "#21262D",
        "ink": "#E6EDF3",
        "muted": "#8B949E",
        "subtle": "#6E7681",
        "slot_fill": "#0D1117",
        "slot_stroke": "#30363D",
        "human": "#DC2626",
        "human_inner": "#F87171",
        "ai": "#E6EDF3",
        "ai_inner": "#8B949E",
        "ai_dot": "#0D1117",
        "accent": "#DC2626",
        "win_line": "#FFFFFF",
        "grid": "#21262D",
    },
    "light": {
        "bg": "#FFFFFF",
        "surface": "#F6F8FA",
        "surface_alt": "#FFFFFF",
        "border": "#D0D7DE",
        "border_soft": "#E5E9EE",
        "ink": "#1F2328",
        "muted": "#57606A",
        "subtle": "#656D76",
        "slot_fill": "#FFFFFF",
        "slot_stroke": "#C9D1D9",
        "human": "#CC0000",
        "human_inner": "#FCA5A5",
        "ai": "#1F2328",
        "ai_inner": "#656D76",
        "ai_dot": "#FFFFFF",
        "accent": "#CC0000",
        "win_line": "#1F2328",
        "grid": "#EAEEF2",
    },
}


def empty_board() -> list[list[int]]:
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def default_state(match: int = 1, stats: dict[str, int] | None = None, recent: list[str] | None = None) -> dict[str, Any]:
    return {
        "match": match,
        "board": empty_board(),
        "status": "playing",
        "winner": 0,
        "win_cells": [],
        "last_human_move": None,
        "last_ai_move": None,
        "last_player": None,
        "move_count": 0,
        "stats": stats or {"human_wins": 0, "ai_wins": 0, "draws": 0, "total_moves": 0},
        "recent_players": recent or [],
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return default_state()
    with STATE_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Ensure schema resilience
    base = default_state()
    base.update(data)
    return base


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with STATE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")


def valid_columns(board: list[list[int]]) -> list[int]:
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def drop_piece(board: list[list[int]], col: int, piece: int) -> int | None:
    if col < 0 or col >= COLS or board[0][col] != EMPTY:
        return None
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return r
    return None


def find_win(board: list[list[int]], piece: int) -> list[list[int]]:
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return [[r, c + i] for i in range(4)]
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return [[r + i, c] for i in range(4)]
    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return [[r + i, c + i] for i in range(4)]
    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return [[r - i, c + i] for i in range(4)]
    return []


def score_window(window: list[int], piece: int) -> int:
    opp = HUMAN if piece == AI else AI
    p_count = window.count(piece)
    o_count = window.count(opp)
    e_count = window.count(EMPTY)

    if p_count == 4:
        return 1000
    if p_count == 3 and e_count == 1:
        return 14
    if p_count == 2 and e_count == 2:
        return 4
    if o_count == 3 and e_count == 1:
        return -18
    if o_count == 2 and e_count == 2:
        return -3
    return 0


def evaluate_board(board: list[list[int]]) -> int:
    score = 0
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(AI) * 4
    score -= center_col.count(HUMAN) * 3

    for r in range(ROWS):
        for c in range(COLS - 3):
            score += score_window([board[r][c + i] for i in range(4)], AI)
    for c in range(COLS):
        for r in range(ROWS - 3):
            score += score_window([board[r + i][c] for i in range(4)], AI)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += score_window([board[r + i][c + i] for i in range(4)], AI)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            score += score_window([board[r - i][c + i] for i in range(4)], AI)
    return score


def minimax(
    board: list[list[int]],
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
) -> tuple[int | None, float]:
    valid = [c for c in (3, 2, 4, 1, 5, 0, 6) if board[0][c] == EMPTY]
    ai_won = bool(find_win(board, AI))
    human_won = bool(find_win(board, HUMAN))

    if ai_won:
        return None, 1_000_000 + depth
    if human_won:
        return None, -1_000_000 - depth
    if not valid:
        return None, 0
    if depth == 0:
        return None, evaluate_board(board)

    if maximizing:
        best_val = -math.inf
        best_col = valid[0]
        for col in valid:
            r = drop_piece(board, col, AI)
            assert r is not None
            _, val = minimax(board, depth - 1, alpha, beta, False)
            board[r][col] = EMPTY
            if val > best_val:
                best_val = val
                best_col = col
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break
        return best_col, best_val
    else:
        best_val = math.inf
        best_col = valid[0]
        for col in valid:
            r = drop_piece(board, col, HUMAN)
            assert r is not None
            _, val = minimax(board, depth - 1, alpha, beta, True)
            board[r][col] = EMPTY
            if val < best_val:
                best_val = val
                best_col = col
            beta = min(beta, best_val)
            if alpha >= beta:
                break
        return best_col, best_val


def choose_ai_move(board: list[list[int]]) -> int | None:
    valid = [c for c in (3, 2, 4, 1, 5, 0, 6) if board[0][c] == EMPTY]
    if not valid:
        return None

    # Immediate winning move
    for col in valid:
        r = drop_piece(board, col, AI)
        assert r is not None
        won = bool(find_win(board, AI))
        board[r][col] = EMPTY
        if won:
            return col

    # Immediate defensive block
    for col in valid:
        r = drop_piece(board, col, HUMAN)
        assert r is not None
        opp_won = bool(find_win(board, HUMAN))
        board[r][col] = EMPTY
        if opp_won:
            return col

    col, _ = minimax(board, AI_DEPTH, -math.inf, math.inf, True)
    return col if col is not None else valid[0]


def sanitize_player(player: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", player or "")
    return (cleaned[:22] or "visitor")


def add_recent_player(recent: list[str], player: str) -> list[str]:
    updated = [p for p in recent if p.lower() != player.lower()]
    updated.insert(0, player)
    return updated[:4]


def process_command(state: dict[str, Any], issue_title: str, player_raw: str) -> tuple[bool, str]:
    title = (issue_title or "").strip().lower()
    player = sanitize_player(player_raw)

    if title in ("c4:new", "c4:reset"):
        next_match = state["match"] + (1 if state["move_count"] > 0 or state["status"] != "playing" else 0)
        new_st = default_state(
            match=next_match,
            stats=state["stats"],
            recent=add_recent_player(state["recent_players"], player),
        )
        new_st["last_player"] = player
        state.clear()
        state.update(new_st)
        return True, f"Started **Match #{state['match']}** — fresh board ready! Click any column on the README to make the opening move."

    m = re.match(r"^c4:drop:([1-7])$", title)
    if not m:
        return False, "Unrecognized Connect Four command. Use `c4:drop:1` through `c4:drop:7`, or `c4:new` to start a new game."

    col = int(m.group(1)) - 1

    # Auto-reset if previous game already finished
    auto_started = False
    if state["status"] != "playing":
        new_st = default_state(
            match=state["match"] + 1,
            stats=state["stats"],
            recent=state["recent_players"],
        )
        state.clear()
        state.update(new_st)
        auto_started = True

    board = state["board"]
    human_row = drop_piece(board, col, HUMAN)
    if human_row is None:
        return False, f"Column **{col + 1}** is already full! Please pick another open column on the README."

    state["last_human_move"] = [human_row, col]
    state["last_ai_move"] = None
    state["last_player"] = player
    state["move_count"] += 1
    state["stats"]["total_moves"] += 1
    state["recent_players"] = add_recent_player(state["recent_players"], player)

    prefix = f"Started **Match #{state['match']}**! " if auto_started else ""

    # Check human win
    win_cells = find_win(board, HUMAN)
    if win_cells:
        state["status"] = "human_win"
        state["winner"] = HUMAN
        state["win_cells"] = win_cells
        state["stats"]["human_wins"] += 1
        return True, f"{prefix}@{player} dropped in **Column {col + 1}** — **Connect Four! Visitors win Match #{state['match']}!**"

    # Check draw before AI move
    if not valid_columns(board):
        state["status"] = "draw"
        state["winner"] = 0
        state["stats"]["draws"] += 1
        return True, f"{prefix}@{player} dropped in **Column {col + 1}** — **Board full! Match #{state['match']} ends in a draw.**"

    # AI turn
    ai_col = choose_ai_move(board)
    assert ai_col is not None
    ai_row = drop_piece(board, ai_col, AI)
    assert ai_row is not None
    state["last_ai_move"] = [ai_row, ai_col]
    state["move_count"] += 1

    ai_win = find_win(board, AI)
    if ai_win:
        state["status"] = "ai_win"
        state["winner"] = AI
        state["win_cells"] = ai_win
        state["stats"]["ai_wins"] += 1
        return True, (
            f"{prefix}@{player} dropped in **Column {col + 1}**. "
            f"Imesh AI countered in **Column {ai_col + 1}** and connected four — **AI wins Match #{state['match']}!** "
            f"Click **New Game** or any column on the README for a rematch."
        )

    if not valid_columns(board):
        state["status"] = "draw"
        state["winner"] = 0
        state["stats"]["draws"] += 1
        return True, (
            f"{prefix}@{player} dropped in **Column {col + 1}**, "
            f"Imesh AI countered in **Column {ai_col + 1}** — **Match #{state['match']} ends in a draw!**"
        )

    return True, (
        f"{prefix}@{player} dropped in **Column {col + 1}**. "
        f"Imesh AI countered in **Column {ai_col + 1}**. "
        f"The board on the README has been updated — your turn!"
    )


def render_board_svg(state: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    board = state["board"]
    win_cells = [tuple(p) for p in state.get("win_cells", [])]
    last_h = tuple(state["last_human_move"]) if state.get("last_human_move") else None
    last_a = tuple(state["last_ai_move"]) if state.get("last_ai_move") else None
    status = state.get("status", "playing")
    match_num = state.get("match", 1)
    stats = state.get("stats", {"human_wins": 0, "ai_wins": 0, "draws": 0, "total_moves": 0})
    recent = state.get("recent_players", [])

    # Board cell coordinates
    col_start_x = 68
    col_step_x = 66
    row_start_y = 94
    row_step_y = 53
    cell_r = 20

    # Column header markers
    col_headers: list[str] = []
    for c in range(COLS):
        cx = col_start_x + c * col_step_x
        col_open = board[0][c] == EMPTY or status != "playing"
        num_fill = t["ink"] if col_open else t["subtle"]
        arrow_fill = t["accent"] if col_open else t["subtle"]
        col_headers.append(
            f'<text x="{cx}" y="48" text-anchor="middle" class="mono col-num" fill="{num_fill}">0{c + 1}</text>'
        )
        if col_open:
            col_headers.append(
                f'<polygon points="{cx - 4},55 {cx + 4},55 {cx},61" fill="{arrow_fill}" />'
            )
        else:
            col_headers.append(
                f'<text x="{cx}" y="62" text-anchor="middle" class="mono col-x" fill="{arrow_fill}">×</text>'
            )

    # Grid background vertical guide hairlines
    guide_lines = []
    for c in range(COLS - 1):
        gx = col_start_x + c * col_step_x + col_step_x // 2
        guide_lines.append(
            f'<line x1="{gx}" y1="70" x2="{gx}" y2="386" stroke="{t["border_soft"]}" stroke-width="1" />'
        )

    # Slots and discs
    cells_svg: list[str] = []
    for r in range(ROWS):
        for c in range(COLS):
            cx = col_start_x + c * col_step_x
            cy = row_start_y + r * row_step_y
            val = board[r][c]
            # Base slot recess
            cells_svg.append(
                f'<circle cx="{cx}" cy="{cy}" r="{cell_r}" fill="{t["slot_fill"]}" stroke="{t["slot_stroke"]}" stroke-width="1" />'
            )
            if val in (HUMAN, AI):
                is_human = val == HUMAN
                fill = t["human"] if is_human else t["ai"]
                inner_stroke = t["human_inner"] if is_human else t["ai_inner"]
                is_last = (r, c) in (last_h, last_a)
                cls = ' class="drop-in"' if is_last else ""
                piece_parts = [
                    f'<g{cls}>',
                    f'<circle cx="{cx}" cy="{cy}" r="{cell_r - 1}" fill="{fill}" />',
                    f'<circle cx="{cx}" cy="{cy}" r="{cell_r - 6}" fill="none" stroke="{inner_stroke}" stroke-width="1" opacity="0.55" />',
                ]
                if is_last:
                    dot_fill = "#FFFFFF" if is_human else t["ai_dot"]
                    piece_parts.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{dot_fill}" />')
                piece_parts.append("</g>")
                cells_svg.append("".join(piece_parts))

            if (r, c) in win_cells:
                cells_svg.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{cell_r + 3}" fill="none" stroke="{t["accent"]}" stroke-width="2" />'
                )

    # Winning connecting line (flat, solid)
    win_line_svg = ""
    if len(win_cells) == 4:
        r0, c0 = win_cells[0]
        r3, c3 = win_cells[3]
        x1 = col_start_x + c0 * col_step_x
        y1 = row_start_y + r0 * row_step_y
        x2 = col_start_x + c3 * col_step_x
        y2 = row_start_y + r3 * row_step_y
        win_line_svg = (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{t["win_line"]}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="6 4" />'
        )

    # Status display strings
    if status == "human_win":
        status_label = "VISITORS WIN!"
        status_sub = "Click NEW GAME or any column for rematch"
        status_bar = t["accent"]
    elif status == "ai_win":
        status_label = "IMESH AI WINS"
        status_sub = "Outsmarted! Click NEW GAME for a rematch"
        status_bar = t["ink"]
    elif status == "draw":
        status_label = "DRAW MATCH"
        status_sub = "Deadlock! Click NEW GAME to play again"
        status_bar = t["muted"]
    else:
        status_label = "YOUR TURN"
        status_sub = "Click a column button below to drop"
        status_bar = t["accent"]

    # Last turn log lines
    last_player = html.escape(state["last_player"]) if state.get("last_player") else None
    if last_h and last_player:
        log_line_1 = f"@{last_player} → COL 0{last_h[1] + 1}"
    elif last_player and state["move_count"] == 0:
        log_line_1 = f"@{last_player} reset the board"
    else:
        log_line_1 = "Awaiting opening move..."

    if last_a:
        log_line_2 = f"IMESH AI → COL 0{last_a[1] + 1}"
    elif status == "human_win":
        log_line_2 = "AI defeated in 4-in-a-row"
    elif status == "draw":
        log_line_2 = "No open columns remaining"
    else:
        log_line_2 = "Engine ready · Minimax Depth 5"

    if recent:
        recent_str = "  ·  ".join(f"@{html.escape(p)}" for p in recent[:3])
        if len(recent_str) > 36:
            recent_str = recent_str[:33] + "..."
    else:
        recent_str = "Be the first to challenge the AI!"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="880" height="432" viewBox="0 0 880 432" role="img" aria-label="Interactive Connect Four board — Match #{match_num}">
  <defs>
    <clipPath id="c4-clip-{theme_name}">
      <rect x="0.5" y="0.5" width="879" height="431" rx="8" />
    </clipPath>
    <pattern id="c4-grid-{theme_name}" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="{t['grid']}" stroke-width="1" />
    </pattern>
  </defs>

  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .col-num {{ font-size: 11px; font-weight: 700; letter-spacing: 0.6px; }}
    .col-x {{ font-size: 12px; font-weight: 700; }}
    .h-title {{ font-size: 15px; font-weight: 800; letter-spacing: 1px; fill: {t['ink']}; }}
    .h-sub {{ font-size: 10.5px; font-weight: 600; letter-spacing: 0.8px; fill: {t['muted']}; }}
    .st-main {{ font-size: 16px; font-weight: 800; letter-spacing: 0.6px; fill: {t['ink']}; }}
    .st-sub {{ font-size: 11px; font-weight: 500; fill: {t['muted']}; }}
    .lbl {{ font-size: 9.5px; font-weight: 700; letter-spacing: 1px; fill: {t['subtle']}; }}
    .val {{ font-size: 20px; font-weight: 800; fill: {t['ink']}; }}
    .val-accent {{ font-size: 20px; font-weight: 800; fill: {t['accent']}; }}
    .log {{ font-size: 11px; font-weight: 600; fill: {t['ink']}; }}
    .log-muted {{ font-size: 11px; font-weight: 500; fill: {t['muted']}; }}
    .legend {{ font-size: 11px; font-weight: 600; fill: {t['ink']}; }}
    @keyframes dropIn {{
      0% {{ transform: translateY(-22px); opacity: 0.4; }}
      100% {{ transform: translateY(0); opacity: 1; }}
    }}
    .drop-in {{ animation: dropIn 0.35s ease-out both; }}
  </style>

  <g clip-path="url(#c4-clip-{theme_name})">
    <rect x="0" y="0" width="880" height="432" fill="{t['bg']}" />
    <rect x="0" y="0" width="880" height="432" fill="url(#c4-grid-{theme_name})" opacity="0.45" />
    <!-- Right telemetry console background -->
    <rect x="536" y="0" width="344" height="432" fill="{t['surface']}" />
    <line x1="536" y1="0" x2="536" y2="432" stroke="{t['border']}" stroke-width="1" />
  </g>

  <!-- Outer 1px border -->
  <rect x="0.5" y="0.5" width="879" height="431" rx="8" fill="none" stroke="{t['border']}" stroke-width="1" />

  <!-- Left Board Frame -->
  <rect x="24" y="24" width="484" height="384" rx="6" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1" />
  <line x1="24" y1="68" x2="508" y2="68" stroke="{t['border']}" stroke-width="1" />

  <!-- Column headers -->
  {''.join(col_headers)}

  <!-- Subtle column vertical guides -->
  {''.join(guide_lines)}

  <!-- Board slots & pieces -->
  {''.join(cells_svg)}
  {win_line_svg}

  <!-- Right Console Header -->
  <rect x="560" y="24" width="4" height="22" fill="{t['accent']}" />
  <text x="574" y="38" class="mono h-title">CONNECT FOUR</text>
  <text x="574" y="53" class="mono h-sub">MATCH #{match_num:02d}  ·  MOVES: {state['move_count']:02d}</text>
  <line x1="560" y1="68" x2="856" y2="68" stroke="{t['border']}" stroke-width="1" />

  <!-- Status Panel -->
  <rect x="560" y="84" width="296" height="62" rx="4" fill="{t['surface_alt']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="560" y="84" width="4" height="62" fill="{status_bar}" />
  <text x="576" y="110" class="mono st-main">{status_label}</text>
  <text x="576" y="131" class="sans st-sub">{status_sub}</text>

  <!-- Players Legend -->
  <text x="560" y="172" class="mono lbl">PLAYERS</text>
  <circle cx="569" cy="190" r="6" fill="{t['human']}" />
  <text x="583" y="194" class="mono legend">VISITOR</text>
  <text x="646" y="194" class="mono log-muted">(Crimson)</text>

  <circle cx="729" cy="190" r="6" fill="{t['ai']}" stroke="{t['border']}" stroke-width="1" />
  <text x="743" y="194" class="mono legend">IMESH AI</text>
  <text x="807" y="194" class="mono log-muted">(D5)</text>

  <!-- Scoreboard -->
  <text x="560" y="226" class="mono lbl">ALL-TIME SCOREBOARD</text>
  <g transform="translate(560, 236)">
    <rect x="0" y="0" width="92" height="58" rx="4" fill="{t['surface_alt']}" stroke="{t['border']}" stroke-width="1" />
    <text x="46" y="20" text-anchor="middle" class="mono lbl">VISITORS</text>
    <text x="46" y="45" text-anchor="middle" class="mono val-accent">{stats['human_wins']}</text>

    <rect x="102" y="0" width="92" height="58" rx="4" fill="{t['surface_alt']}" stroke="{t['border']}" stroke-width="1" />
    <text x="148" y="20" text-anchor="middle" class="mono lbl">DRAWS</text>
    <text x="148" y="45" text-anchor="middle" class="mono val">{stats['draws']}</text>

    <rect x="204" y="0" width="92" height="58" rx="4" fill="{t['surface_alt']}" stroke="{t['border']}" stroke-width="1" />
    <text x="250" y="20" text-anchor="middle" class="mono lbl">IMESH AI</text>
    <text x="250" y="45" text-anchor="middle" class="mono val">{stats['ai_wins']}</text>
  </g>

  <!-- Last Move Log -->
  <text x="560" y="318" class="mono lbl">LAST TURN</text>
  <rect x="560" y="326" width="296" height="46" rx="4" fill="{t['surface_alt']}" stroke="{t['border']}" stroke-width="1" />
  <text x="572" y="345" class="mono log">{log_line_1}</text>
  <text x="572" y="363" class="mono log-muted">{log_line_2}</text>

  <!-- Recent Challengers -->
  <text x="560" y="394" class="mono lbl">RECENT CHALLENGERS</text>
  <text x="560" y="410" class="mono log-muted">{recent_str}</text>
</svg>
"""
    return svg


def render_button_svgs() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for col in range(1, COLS + 1):
        active_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="96" height="36" viewBox="0 0 96 36" role="img" aria-label="Drop in Column {col}">
  <rect x="0.5" y="0.5" width="95" height="35" rx="4" fill="#161B22" stroke="#30363D" stroke-width="1" />
  <rect x="1" y="1" width="94" height="3" rx="1" fill="#DC2626" />
  <text x="48" y="24" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" font-size="12" font-weight="700" letter-spacing="0.8" fill="#E6EDF3">▼ COL 0{col}</text>
</svg>
"""
        full_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="96" height="36" viewBox="0 0 96 36" role="img" aria-label="Column {col} Full">
  <rect x="0.5" y="0.5" width="95" height="35" rx="4" fill="#21262D" stroke="#30363D" stroke-width="1" />
  <text x="48" y="23" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" font-size="11.5" font-weight="600" letter-spacing="0.8" fill="#6E7681">× FULL</text>
</svg>
"""
        (ASSETS_DIR / f"btn-col-{col}.svg").write_text(active_svg, encoding="utf-8")
        (ASSETS_DIR / f"btn-col-{col}-full.svg").write_text(full_svg, encoding="utf-8")

    new_game_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="144" height="36" viewBox="0 0 144 36" role="img" aria-label="Start New Connect Four Game">
  <rect x="0.5" y="0.5" width="143" height="35" rx="4" fill="#CC0000" stroke="#991B1B" stroke-width="1" />
  <text x="72" y="22.5" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" font-size="11.5" font-weight="700" letter-spacing="1" fill="#FFFFFF">↻ NEW GAME</text>
</svg>
"""
    (ASSETS_DIR / "btn-new.svg").write_text(new_game_svg, encoding="utf-8")


def build_readme_block(state: dict[str, Any]) -> str:
    board = state["board"]
    status = state.get("status", "playing")
    btn_links: list[str] = []

    for c in range(COLS):
        col_num = c + 1
        playable = board[0][c] == EMPTY or status != "playing"
        if playable:
            body = quote_plus(
                f'Click "Submit new issue" below to drop your piece into Column {col_num}. '
                f"GitHub Actions will run the Minimax AI and update the README board in ~15 seconds!"
            )
            url = f"https://github.com/{REPO_SLUG}/issues/new?title=c4:drop:{col_num}&body={body}"
            btn_links.append(
                f'  <a href="{url}"><img src="./assets/btn-col-{col_num}.svg" alt="Drop Column {col_num}" height="34" /></a>'
            )
        else:
            btn_links.append(
                f'  <img src="./assets/btn-col-{col_num}-full.svg" alt="Column {col_num} Full" height="34" />'
            )

    new_body = quote_plus(
        'Click "Submit new issue" below to reset the Connect Four board and start a fresh match!'
    )
    new_url = f"https://github.com/{REPO_SLUG}/issues/new?title=c4:new&body={new_body}"

    lines = [
        START_MARKER,
        '<div align="center">',
        "  <picture>",
        '    <source media="(prefers-color-scheme: dark)" srcset="./assets/connect4-dark.svg" />',
        '    <source media="(prefers-color-scheme: light)" srcset="./assets/connect4-light.svg" />',
        '    <img src="./assets/connect4-dark.svg" alt="Interactive Connect Four Board" width="100%" />',
        "  </picture>",
        "  <br /><br />",
        "  <p>",
        *btn_links,
        "  </p>",
        "  <p>",
        f'    <a href="{new_url}"><img src="./assets/btn-new.svg" alt="New Game" height="34" /></a>',
        "  </p>",
        "</div>",
        END_MARKER,
    ]
    return "\n".join(lines)


def update_readme(state: dict[str, Any]) -> None:
    if not README_PATH.exists():
        return
    content = README_PATH.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        return
    new_block = build_readme_block(state)
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    updated = pattern.sub(lambda _: new_block, content, count=1)
    README_PATH.write_text(updated, encoding="utf-8")


def render_all(state: dict[str, Any]) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "connect4-dark.svg").write_text(render_board_svg(state, "dark"), encoding="utf-8")
    (ASSETS_DIR / "connect4-light.svg").write_text(render_board_svg(state, "light"), encoding="utf-8")
    render_button_svgs()
    update_readme(state)


def write_github_output(changed: bool, message: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"changed={'true' if changed else 'false'}\n")
        fh.write("comment<<EOF\n")
        fh.write(f"{message}\n")
        fh.write("EOF\n")


def run_self_test() -> None:
    import xml.etree.ElementTree as ET

    # 1. Gravity & full column check
    b = empty_board()
    for expected_row in range(ROWS - 1, -1, -1):
        assert drop_piece(b, 0, HUMAN) == expected_row
    assert drop_piece(b, 0, HUMAN) is None

    # 2. Horizontal, vertical, and diagonal win detection
    bh = empty_board()
    for c in range(4):
        drop_piece(bh, c, HUMAN)
    assert len(find_win(bh, HUMAN)) == 4

    bd = empty_board()
    # Diagonal: (5,0), (4,1), (3,2), (2,3)
    drop_piece(bd, 0, HUMAN)
    drop_piece(bd, 1, AI); drop_piece(bd, 1, HUMAN)
    drop_piece(bd, 2, AI); drop_piece(bd, 2, AI); drop_piece(bd, 2, HUMAN)
    drop_piece(bd, 3, AI); drop_piece(bd, 3, AI); drop_piece(bd, 3, AI); drop_piece(bd, 3, HUMAN)
    assert len(find_win(bd, HUMAN)) == 4

    # 3. AI immediate block & immediate win
    bb = empty_board()
    for c in (0, 1, 2):
        drop_piece(bb, c, HUMAN)
    assert choose_ai_move(bb) == 3, "AI failed to block horizontal 3-in-a-row"

    bw = empty_board()
    for c in (0, 1, 2):
        drop_piece(bw, c, AI)
    assert choose_ai_move(bw) == 3, "AI failed to take immediate winning move"

    # 4. Command processing & XML validity of rendered SVGs (including XSS/special chars)
    st = default_state()
    changed, msg = process_command(st, "c4:drop:4", "test_<user>&1")
    assert changed and st["move_count"] == 2
    for theme in ("dark", "light"):
        svg_text = render_board_svg(st, theme)
        ET.fromstring(svg_text)
        assert "feGaussianBlur" not in svg_text and "drop-shadow" not in svg_text

    # 5. Reset command
    changed, _ = process_command(st, "c4:new", "tester")
    assert changed and st["move_count"] == 0 and st["match"] == 2

    print("ALL CONNECT4 SELF-TESTS PASSED!")


def main() -> int:
    parser = argparse.ArgumentParser(description="Connect Four README game engine")
    parser.add_argument("--render-only", action="store_true", help="Render SVGs and README block from current state")
    parser.add_argument("--issue-title", type=str, default="", help="GitHub issue title command")
    parser.add_argument("--player", type=str, default="visitor", help="GitHub username of mover")
    parser.add_argument("--self-test", action="store_true", help="Run built-in unit tests without modifying files")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0

    state = load_state()

    if args.render_only:
        save_state(state)
        render_all(state)
        print(f"Rendered Connect Four Match #{state['match']} (moves={state['move_count']}).")
        return 0

    changed, message = process_command(state, args.issue_title, args.player)
    if changed:
        save_state(state)
        render_all(state)
    write_github_output(changed, message)
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
