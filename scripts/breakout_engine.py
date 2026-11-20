#!/usr/bin/env python3
"""
Real 2D Physics Contribution Breakout Engine & Flat SMIL SVG Compiler.
- Takes real GitHub contribution calendar cells (53 weeks x 7 days)
- Simulates exact 2D ball-paddle-brick collisions with smart brick-seeking AI paddle
- Compiles exact bounce trajectories, brick destructions, pixel debris pops, and live
  progress bar into crisp, 100% zero-glow dual-theme (dark & light) SVGs.
"""

from __future__ import annotations

import math
from typing import Any

WIDTH = 900
HEIGHT = 360

# Playfield inner screen bounds
SCR_X = 24.0
SCR_Y = 56.0
SCR_W = 852.0
SCR_H = 250.0
SCR_RIGHT = SCR_X + SCR_W
SCR_BOTTOM = SCR_Y + SCR_H

# Contribution brick wall layout (53 cols x 7 rows)
COLS = 53
ROWS = 7
BRICK_W = 13.4
BRICK_H = 11.4
STEP_X = 15.6
STEP_Y = 14.0
GRID_W = (COLS - 1) * STEP_X + BRICK_W
GRID_X0 = SCR_X + (SCR_W - GRID_W) / 2.0
GRID_Y0 = SCR_Y + 14.0

# Paddle & Ball specs
PADDLE_W = 88.0
PADDLE_H = 8.0
PADDLE_Y = SCR_BOTTOM - 22.0
BALL_R = 5.0
SIM_DUR = 24.0
DT = 1.0 / 120.0

THEMES = {
    "dark": {
        "chassis": "#0D1117",
        "bezel": "#161B22",
        "screen": "#090C10",
        "border": "#30363D",
        "border_soft": "#21262D",
        "ink": "#E6EDF3",
        "muted": "#8B949E",
        "subtle": "#6E7681",
        "accent": "#DC2626",
        "empty_cell": "#141920",
        "empty_stroke": "#1E252E",
        "levels": {
            1: "#30363D",
            2: "#586069",
            3: "#C9D1D9",
            4: "#DC2626",
        },
        "paddle": "#E6EDF3",
        "paddle_core": "#DC2626",
        "ball": "#DC2626",
        "ball_core": "#FFFFFF",
        "trail": "#8B949E",
        "rail": "#21262D",
    },
    "light": {
        "chassis": "#FFFFFF",
        "bezel": "#F6F8FA",
        "screen": "#FFFFFF",
        "border": "#D0D7DE",
        "border_soft": "#E5E9EE",
        "ink": "#1F2328",
        "muted": "#57606A",
        "subtle": "#656D76",
        "accent": "#CC0000",
        "empty_cell": "#F3F5F7",
        "empty_stroke": "#E5E9EE",
        "levels": {
            1: "#C9D1D9",
            2: "#8C959F",
            3: "#24292F",
            4: "#CC0000",
        },
        "paddle": "#1F2328",
        "paddle_core": "#CC0000",
        "ball": "#CC0000",
        "ball_core": "#FFFFFF",
        "trail": "#656D76",
        "rail": "#E5E9EE",
    },
}


def build_grid_from_days(days: list[dict[str, Any]]) -> list[list[int]]:
    """Map chronological contribution days into a 53x7 matrix (col-major like GitHub)."""
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    if not days:
        # Crisp geometric fallback pattern if offline
        pattern = [
            "0011100110011001111001110010010",
            "0001000101101001000001000010010",
            "0001000100001001110001110011110",
            "0001000100001001000000010010010",
            "0011100100001001111001110010010",
        ]
        for r, line in enumerate(pattern):
            for i, ch in enumerate(line):
                if ch == "1":
                    c = 11 + i
                    if 0 <= c < COLS:
                        grid[r + 1][c] = 4 if (i % 5 == 0) else 3
        return grid

    recent = days[-(COLS * ROWS) :]
    total = len(recent)
    start_idx = (COLS * ROWS) - total
    for i, item in enumerate(recent):
        idx = start_idx + i
        col = idx // ROWS
        row = idx % ROWS
        if 0 <= col < COLS and 0 <= row < ROWS:
            grid[row][col] = max(0, min(4, int(item.get("level", 0))))
    return grid


def predict_landing_x(bx: float, by: float, vx: float, vy: float) -> float:
    """Analytically predict X where downward-moving ball crosses paddle top."""
    if vy <= 1.0:
        return SCR_X + SCR_W / 2.0
    t_hit = (PADDLE_Y - BALL_R - by) / vy
    if t_hit <= 0:
        return bx
    raw_x = bx + vx * t_hit
    left = SCR_X + BALL_R
    right = SCR_RIGHT - BALL_R
    span = right - left
    rel = (raw_x - left) % (2.0 * span)
    if rel > span:
        rel = 2.0 * span - rel
    return left + rel


def simulate_breakout(grid: list[list[int]]) -> dict[str, Any]:
    """Run deterministic 2D physics simulation smashing active contribution bricks."""
    bricks: list[dict[str, Any]] = []
    for r in range(ROWS):
        for c in range(COLS):
            lvl = grid[r][c]
            x = GRID_X0 + c * STEP_X
            y = GRID_Y0 + r * STEP_Y
            bricks.append(
                {
                    "id": f"b_{r}_{c}",
                    "r": r,
                    "c": c,
                    "x": x,
                    "y": y,
                    "level": lvl,
                    "alive": lvl > 0,
                    "hit_t": None,
                }
            )

    active_total = sum(1 for b in bricks if b["level"] > 0)

    bx = SCR_X + SCR_W * 0.5
    by = PADDLE_Y - BALL_R - 1.0
    vx = 250.0
    vy = -360.0
    px = bx - PADDLE_W / 2.0

    ball_frames: list[tuple[float, float, float]] = [(0.0, bx, by)]
    paddle_frames: list[tuple[float, float]] = [(0.0, px)]
    hit_events: list[dict[str, Any]] = []

    steps = int(SIM_DUR / DT)
    target_px = px
    last_paddle_sample = 0.0

    for step in range(1, steps + 1):
        t = step * DT
        bx += vx * DT
        by += vy * DT

        bounced = False

        # Left / right walls
        if bx - BALL_R <= SCR_X:
            bx = SCR_X + BALL_R
            vx = abs(vx)
            bounced = True
        elif bx + BALL_R >= SCR_RIGHT:
            bx = SCR_RIGHT - BALL_R
            vx = -abs(vx)
            bounced = True

        # Top ceiling
        if by - BALL_R <= SCR_Y:
            by = SCR_Y + BALL_R
            vy = abs(vy)
            bounced = True

        # Brick AABB collision
        hit_brick = None
        min_dist = 1e9
        for b in bricks:
            if not b["alive"]:
                continue
            cx = max(b["x"], min(bx, b["x"] + BRICK_W))
            cy = max(b["y"], min(by, b["y"] + BRICK_H))
            dx = bx - cx
            dy = by - cy
            d2 = dx * dx + dy * dy
            if d2 <= BALL_R * BALL_R and d2 < min_dist:
                min_dist = d2
                hit_brick = b

        if hit_brick is not None:
            hit_brick["alive"] = False
            hit_brick["hit_t"] = t
            hit_events.append(
                {
                    "t": t,
                    "cx": hit_brick["x"] + BRICK_W / 2.0,
                    "cy": hit_brick["y"] + BRICK_H / 2.0,
                    "level": hit_brick["level"],
                }
            )
            bcx = hit_brick["x"] + BRICK_W / 2.0
            bcy = hit_brick["y"] + BRICK_H / 2.0
            ox = (BRICK_W / 2.0 + BALL_R) - abs(bx - bcx)
            oy = (BRICK_H / 2.0 + BALL_R) - abs(by - bcy)
            if ox < oy:
                vx = -vx
            else:
                vy = -vy
            # Prevent flat horizontal stall
            if abs(vy) < 165.0:
                vy = math.copysign(190.0, vy if vy != 0 else 1.0)
            bounced = True

        # Smart paddle tracking: aim rebounds directly toward remaining active commit bricks
        if vy > 0:
            land_x = predict_landing_x(bx, by, vx, vy)
            alive_bricks = [b for b in bricks if b["alive"]]
            aim_shift = 0.0
            if alive_bricks:
                # Target an active brick, favoring ones closer to the bottom/accessible rows
                alive_bricks.sort(key=lambda b: (-b["r"], abs((b["x"] + BRICK_W / 2.0) - land_x)))
                pick = alive_bricks[len(hit_events) % min(5, len(alive_bricks))]
                target_bx = pick["x"] + BRICK_W / 2.0
                target_by = pick["y"] + BRICK_H / 2.0
                dy_up = max(40.0, PADDLE_Y - target_by)
                dx_need = target_bx - land_x
                desired_angle = max(-1.05, min(1.05, math.atan2(dx_need, dy_up)))
                desired_rel = max(-0.85, min(0.85, desired_angle / 1.08))
                aim_shift = desired_rel * (PADDLE_W / 2.0)
            target_px = land_x - PADDLE_W / 2.0 - aim_shift
        else:
            target_px = bx * 0.55 + (SCR_X + SCR_W / 2.0) * 0.45 - PADDLE_W / 2.0

        target_px = max(SCR_X + 6.0, min(SCR_RIGHT - PADDLE_W - 6.0, target_px))
        max_move = 560.0 * DT
        diff = target_px - px
        if abs(diff) > max_move:
            px += math.copysign(max_move, diff)
        else:
            px = target_px

        # Paddle rebound
        if vy > 0 and by + BALL_R >= PADDLE_Y:
            if bx < px + 4.0:
                px = max(SCR_X + 6.0, bx - 12.0)
            elif bx > px + PADDLE_W - 4.0:
                px = min(SCR_RIGHT - PADDLE_W - 6.0, bx - PADDLE_W + 12.0)

            by = PADDLE_Y - BALL_R
            rel_hit = ((bx - (px + PADDLE_W / 2.0)) / (PADDLE_W / 2.0))
            rel_hit = max(-0.88, min(0.88, rel_hit))
            speed = 465.0
            angle = rel_hit * 1.08
            vx = speed * math.sin(angle)
            if abs(vx) < 75.0:
                vx = math.copysign(95.0, vx if vx != 0 else 1.0)
            vy = -math.sqrt(max(210.0 * 210.0, speed * speed - vx * vx))
            bounced = True
            paddle_frames.append((t, px))
            last_paddle_sample = t

        if bounced:
            ball_frames.append((t, bx, by))

        if t - last_paddle_sample >= 0.22:
            paddle_frames.append((t, px))
            last_paddle_sample = t

    ball_frames.append((SIM_DUR, bx, by))
    paddle_frames.append((SIM_DUR, px))

    return {
        "bricks": bricks,
        "active_total": active_total,
        "hits": hit_events,
        "ball_frames": ball_frames,
        "paddle_frames": paddle_frames,
    }


def _fmt_seq(nums: list[float], dec: int = 1) -> str:
    fmt = f"{{:.{dec}f}}"
    return ";".join(fmt.format(n) for n in nums)


def _sample_ball_at(frames: list[tuple[float, float, float]], t_query: float) -> tuple[float, float]:
    if t_query <= 0:
        return frames[0][1], frames[0][2]
    if t_query >= frames[-1][0]:
        return frames[-1][1], frames[-1][2]
    for i in range(len(frames) - 1):
        t0, x0, y0 = frames[i]
        t1, x1, y1 = frames[i + 1]
        if t0 <= t_query <= t1:
            span = max(1e-6, t1 - t0)
            u = (t_query - t0) / span
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return frames[-1][1], frames[-1][2]


def render_breakout_svg(
    sim: dict[str, Any],
    total_contributions: int,
    theme_name: str,
) -> str:
    t = THEMES[theme_name]
    bricks = sim["bricks"]
    hits = sim["hits"]
    ball_frames = sim["ball_frames"]
    paddle_frames = sim["paddle_frames"]
    active_total = max(1, sim["active_total"])
    broken_count = len(hits)

    # Build brick rectangles (empty ghost grid + active animated bricks)
    ghost_rects: list[str] = []
    active_rects: list[str] = []
    for b in bricks:
        bx = f"{b['x']:.1f}"
        by = f"{b['y']:.1f}"
        if b["level"] == 0:
            ghost_rects.append(
                f'<rect x="{bx}" y="{by}" width="{BRICK_W:.1f}" height="{BRICK_H:.1f}" rx="1.5" '
                f'fill="{t["empty_cell"]}" stroke="{t["empty_stroke"]}" stroke-width="0.7" />'
            )
        else:
            # Always draw faint ghost slot beneath so destruction reveals calendar slot
            ghost_rects.append(
                f'<rect x="{bx}" y="{by}" width="{BRICK_W:.1f}" height="{BRICK_H:.1f}" rx="1.5" '
                f'fill="{t["empty_cell"]}" stroke="{t["empty_stroke"]}" stroke-width="0.7" />'
            )
            fill = t["levels"][b["level"]]
            if b["hit_t"] is not None:
                kt = max(0.002, min(0.994, b["hit_t"] / SIM_DUR))
                kt2 = min(0.998, kt + 0.003)
                active_rects.append(
                    f'<rect x="{bx}" y="{by}" width="{BRICK_W:.1f}" height="{BRICK_H:.1f}" rx="1.5" fill="{fill}">'
                    f'<animate attributeName="opacity" values="1;1;0;0" '
                    f'keyTimes="0;{kt:.4f};{kt2:.4f};1" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
                    f"</rect>"
                )
            else:
                active_rects.append(
                    f'<rect x="{bx}" y="{by}" width="{BRICK_W:.1f}" height="{BRICK_H:.1f}" rx="1.5" fill="{fill}" />'
                )

    # Pixel shatter debris (strictly flat 3x3 squares, zero blur/glow; cap at 36 bursts for compact SVG)
    debris_svg: list[str] = []
    offsets = [(-13, -10), (13, -10), (-11, 11), (11, 11)]
    for ev in hits[:36]:
        t0 = ev["t"] / SIM_DUR
        t1 = min(0.996, (ev["t"] + 0.34) / SIM_DUR)
        t_pre = max(0.0005, t0 - 0.001)
        t_post = min(0.999, t1 + 0.001)
        chip_fill = t["accent"] if ev["level"] == 4 else t["ink"]
        cx = ev["cx"] - 1.5
        cy = ev["cy"] - 1.5
        for dx, dy in offsets:
            debris_svg.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="3" height="3" fill="{chip_fill}" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;0;0" '
                f'keyTimes="0;{t_pre:.4f};{t0:.4f};{t1:.4f};1" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
                f'<animate attributeName="x" values="{cx:.1f};{cx:.1f};{cx + dx:.1f};{cx + dx:.1f}" '
                f'keyTimes="0;{t0:.4f};{t1:.4f};1" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
                f'<animate attributeName="y" values="{cy:.1f};{cy:.1f};{cy + dy:.1f};{cy + dy:.1f}" '
                f'keyTimes="0;{t0:.4f};{t1:.4f};1" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
                f"</rect>"
            )

    # Ball trajectory SMIL sequences
    ball_kt = _fmt_seq([f[0] / SIM_DUR for f in ball_frames], 4)
    ball_xs = _fmt_seq([f[1] for f in ball_frames], 1)
    ball_ys = _fmt_seq([f[2] for f in ball_frames], 1)

    # Crisp flat 2-dot geometric motion trail (lagged 0.055s & 0.11s)
    trail_svgs: list[str] = []
    for lag, rad, op in ((0.055, 3.3, "0.45"), (0.11, 2.2, "0.22")):
        t_xs = []
        t_ys = []
        for ft, _, _ in ball_frames:
            sx, sy = _sample_ball_at(ball_frames, max(0.0, ft - lag))
            t_xs.append(sx)
            t_ys.append(sy)
        trail_svgs.append(
            f'<circle cx="{t_xs[0]:.1f}" cy="{t_ys[0]:.1f}" r="{rad}" fill="{t["trail"]}" opacity="{op}">'
            f'<animate attributeName="cx" values="{_fmt_seq(t_xs, 1)}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
            f'<animate attributeName="cy" values="{_fmt_seq(t_ys, 1)}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />'
            f"</circle>"
        )

    # Paddle SMIL sequences
    pad_kt = _fmt_seq([f[0] / SIM_DUR for f in paddle_frames], 4)
    pad_xs = _fmt_seq([f[1] for f in paddle_frames], 1)
    pad_core_xs = _fmt_seq([f[1] + PADDLE_W / 2.0 - 11.0 for f in paddle_frames], 1)

    # Live progress bar in top hardware bezel (synced to actual brick hits)
    prog_max_w = 180.0
    prog_kt_list = [0.0]
    prog_w_list = [2.0]
    for idx, ev in enumerate(hits, start=1):
        kt = max(0.002, min(0.995, ev["t"] / SIM_DUR))
        w = max(2.0, min(prog_max_w, (idx / active_total) * prog_max_w))
        prog_kt_list.append(kt)
        prog_w_list.append(w)
    prog_kt_list.append(1.0)
    prog_w_list.append(prog_w_list[-1])

    # Speaker grille decorative slots (Braun/TE flat industrial touch)
    grille_slots = "".join(
        f'<rect x="{24 + i * 5}" y="16" width="2" height="14" rx="0.5" fill="{t["border"]}" />'
        for i in range(6)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Live Physics Contribution Breakout Arcade — Smashing real GitHub commits">
  <defs>
    <clipPath id="brk-clip-{theme_name}">
      <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" />
    </clipPath>
  </defs>

  <style>
    .mono {{ font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }}
    .hdr-title {{ font-size: 11px; font-weight: 800; letter-spacing: 1.2px; fill: {t['ink']}; }}
    .hdr-badge {{ font-size: 9.5px; font-weight: 800; letter-spacing: 1px; fill: {t['ink']}; }}
    .hdr-sub {{ font-size: 10px; font-weight: 600; letter-spacing: 0.8px; fill: {t['muted']}; }}
    .foot-tag {{ font-size: 9.5px; font-weight: 700; letter-spacing: 0.8px; fill: {t['muted']}; }}
    .foot-cta {{ font-size: 10px; font-weight: 800; letter-spacing: 0.9px; fill: {t['accent']}; }}
    @keyframes stepBlink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0.25; }}
    }}
    .live-sq {{ animation: stepBlink 1.4s steps(2, end) infinite; }}
  </style>

  <g clip-path="url(#brk-clip-{theme_name})">
    <!-- Outer hardware chassis -->
    <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{t['chassis']}" />
    <!-- Top bezel strip -->
    <rect x="0" y="0" width="{WIDTH}" height="46" fill="{t['bezel']}" />
    <line x1="0" y1="46" x2="{WIDTH}" y2="46" stroke="{t['border']}" stroke-width="1" />
    <!-- Bottom hardware deck -->
    <rect x="0" y="314" width="{WIDTH}" height="46" fill="{t['bezel']}" />
    <line x1="0" y1="314" x2="{WIDTH}" y2="314" stroke="{t['border']}" stroke-width="1" />
    <!-- Left flat crimson structural edge -->
    <rect x="0" y="0" width="5" height="{HEIGHT}" fill="{t['accent']}" />
  </g>

  <!-- Outer hairline border -->
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="none" stroke="{t['border']}" stroke-width="1" />

  <!-- Top Bezel Hardware Details -->
  {grille_slots}
  <text x="64" y="21" class="mono hdr-title">IMESH-ARCADE // UNIT-01</text>
  <text x="64" y="35" class="mono hdr-sub">LIVE CONTRIBUTION BREAKOUT  ·  {total_contributions} COMMITS / YR</text>

  <!-- Live synced clear-meter bar -->
  <text x="454" y="20" class="mono hdr-sub">CLEAR PROGRESS ({broken_count}/{active_total} BRICKS)</text>
  <rect x="454" y="27" width="{prog_max_w:.0f}" height="7" rx="1.5" fill="{t['chassis']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="454" y="27" width="2" height="7" rx="1.5" fill="{t['accent']}">
    <animate attributeName="width" values="{_fmt_seq(prog_w_list, 1)}" keyTimes="{_fmt_seq(prog_kt_list, 4)}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
  </rect>

  <!-- Top-right live badge -->
  <rect x="748" y="13" width="128" height="20" rx="3" fill="{t['chassis']}" stroke="{t['border']}" stroke-width="1" />
  <rect x="757" y="20" width="6" height="6" rx="1" fill="{t['accent']}" class="live-sq" />
  <text x="770" y="26.5" class="mono hdr-badge">REAL PHYSICS</text>

  <!-- Main Flat Playfield Screen -->
  <rect x="{SCR_X:.0f}" y="{SCR_Y:.0f}" width="{SCR_W:.0f}" height="{SCR_H:.0f}" rx="4" fill="{t['screen']}" stroke="{t['border']}" stroke-width="1" />

  <!-- Subtle paddle guide rail -->
  <line x1="{SCR_X + 10:.0f}" y1="{PADDLE_Y + PADDLE_H / 2.0:.1f}" x2="{SCR_RIGHT - 10:.0f}" y2="{PADDLE_Y + PADDLE_H / 2.0:.1f}" stroke="{t['rail']}" stroke-width="1" stroke-dasharray="3 5" />

  <!-- Ghost contribution grid -->
  {''.join(ghost_rects)}

  <!-- Real GitHub commit bricks -->
  {''.join(active_rects)}

  <!-- Flat pixel shatter chips -->
  {''.join(debris_svg)}

  <!-- Geometric motion trail -->
  {''.join(trail_svgs)}

  <!-- Ball (crisp flat crimson + white core dot, zero glow) -->
  <circle cx="{ball_frames[0][1]:.1f}" cy="{ball_frames[0][2]:.1f}" r="{BALL_R:.1f}" fill="{t['ball']}">
    <animate attributeName="cx" values="{ball_xs}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
    <animate attributeName="cy" values="{ball_ys}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
  </circle>
  <circle cx="{ball_frames[0][1]:.1f}" cy="{ball_frames[0][2]:.1f}" r="1.8" fill="{t['ball_core']}">
    <animate attributeName="cx" values="{ball_xs}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
    <animate attributeName="cy" values="{ball_ys}" keyTimes="{ball_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
  </circle>

  <!-- Autonomous AI Paddle -->
  <rect x="{paddle_frames[0][1]:.1f}" y="{PADDLE_Y:.1f}" width="{PADDLE_W:.1f}" height="{PADDLE_H:.1f}" rx="2" fill="{t['paddle']}">
    <animate attributeName="x" values="{pad_xs}" keyTimes="{pad_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
  </rect>
  <rect x="{paddle_frames[0][1] + PADDLE_W / 2.0 - 11.0:.1f}" y="{PADDLE_Y:.1f}" width="22" height="{PADDLE_H:.1f}" rx="1" fill="{t['paddle_core']}">
    <animate attributeName="x" values="{pad_core_xs}" keyTimes="{pad_kt}" dur="{SIM_DUR:.1f}s" repeatCount="indefinite" />
  </rect>

  <!-- Bottom Hardware Deck -->
  <rect x="24" y="326" width="132" height="22" rx="3" fill="{t['chassis']}" stroke="{t['border']}" stroke-width="1" />
  <text x="90" y="340.5" text-anchor="middle" class="mono foot-tag">ENGINE: PYTHON 2D</text>

  <rect x="164" y="326" width="154" height="22" rx="3" fill="{t['chassis']}" stroke="{t['border']}" stroke-width="1" />
  <text x="241" y="340.5" text-anchor="middle" class="mono foot-tag">DATA: LIVE COMMITS</text>

  <rect x="326" y="326" width="120" height="22" rx="3" fill="{t['chassis']}" stroke="{t['border']}" stroke-width="1" />
  <text x="386" y="340.5" text-anchor="middle" class="mono foot-tag">SYNC: AUTO DAILY</text>

  <text x="874" y="341" text-anchor="end" class="mono foot-cta">CLICK TO PLAY 60FPS ARCADE (3 GAMES · NO LOGIN) ↗</text>
</svg>
"""


def run_self_test() -> None:
    import xml.etree.ElementTree as ET

    grid = build_grid_from_days([])
    sim = simulate_breakout(grid)
    assert len(sim["hits"]) >= 8, f"Expected >=8 brick hits in fallback sim, got {len(sim['hits'])}"
    assert len(sim["ball_frames"]) >= 15
    for th in ("dark", "light"):
        svg = render_breakout_svg(sim, 286, th)
        ET.fromstring(svg)
        for banned in ("feGaussianBlur", "feDropShadow", "drop-shadow", "box-shadow", "radialGradient"):
            assert banned not in svg, f"Found banned glow token {banned}"
    print(f"BREAKOUT ENGINE SELF-TEST PASSED! (hits={len(sim['hits'])}, keyframes={len(sim['ball_frames'])})")


if __name__ == "__main__":
    run_self_test()
