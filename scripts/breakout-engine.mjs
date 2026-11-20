#!/usr/bin/env node
/**
 * Real 2D Physics Contribution Breakout Engine & Flat SMIL SVG Compiler (Pure Node.js).
 * - Zero external dependencies, zero Python, 100% zero glow/blur.
 * - Simulates exact 2D ball-paddle-brick collisions against real GitHub commits.
 * - Compiles exact bounce trajectories, brick destructions, flat pixel debris pops,
 *   and live progress bar into dual-theme (dark & light) declarative SVGs.
 */

const WIDTH = 900;
const HEIGHT = 360;

const SCR_X = 24.0;
const SCR_Y = 56.0;
const SCR_W = 852.0;
const SCR_H = 250.0;
const SCR_RIGHT = SCR_X + SCR_W;
const SCR_BOTTOM = SCR_Y + SCR_H;

export const COLS = 53;
export const ROWS = 7;
const BRICK_W = 13.4;
const BRICK_H = 11.4;
const STEP_X = 15.6;
const STEP_Y = 14.0;
const GRID_W = (COLS - 1) * STEP_X + BRICK_W;
const GRID_X0 = SCR_X + (SCR_W - GRID_W) / 2.0;
const GRID_Y0 = SCR_Y + 14.0;

const PADDLE_W = 88.0;
const PADDLE_H = 8.0;
const PADDLE_Y = SCR_BOTTOM - 22.0;
const BALL_R = 5.0;
const SIM_DUR = 24.0;
const DT = 1.0 / 120.0;

const THEMES = {
  dark: {
    chassis: '#0D1117',
    bezel: '#161B22',
    screen: '#090C10',
    border: '#30363D',
    ink: '#E6EDF3',
    muted: '#8B949E',
    accent: '#DC2626',
    emptyCell: '#141920',
    emptyStroke: '#1E252E',
    levels: { 1: '#30363D', 2: '#586069', 3: '#C9D1D9', 4: '#DC2626' },
    paddle: '#E6EDF3',
    paddleCore: '#DC2626',
    ball: '#DC2626',
    ballCore: '#FFFFFF',
    trail: '#8B949E',
    rail: '#21262D',
  },
  light: {
    chassis: '#FFFFFF',
    bezel: '#F6F8FA',
    screen: '#FFFFFF',
    border: '#D0D7DE',
    ink: '#1F2328',
    muted: '#57606A',
    accent: '#CC0000',
    emptyCell: '#F3F5F7',
    emptyStroke: '#E5E9EE',
    levels: { 1: '#C9D1D9', 2: '#8C959F', 3: '#24292F', 4: '#CC0000' },
    paddle: '#1F2328',
    paddleCore: '#CC0000',
    ball: '#CC0000',
    ballCore: '#FFFFFF',
    trail: '#656D76',
    rail: '#E5E9EE',
  },
};

export function buildGridFromDays(days) {
  const grid = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
  if (!days || days.length === 0) {
    const pattern = [
      '0011100110011001111001110010010',
      '0001000101101001000001000010010',
      '0001000100001001110001110011110',
      '0001000100001001000000010010010',
      '0011100100001001111001110010010',
    ];
    for (let r = 0; r < pattern.length; r++) {
      for (let i = 0; i < pattern[r].length; i++) {
        if (pattern[r][i] === '1') {
          const c = 11 + i;
          if (c >= 0 && c < COLS) grid[r + 1][c] = i % 5 === 0 ? 4 : 3;
        }
      }
    }
    return grid;
  }

  const recent = days.slice(-(COLS * ROWS));
  const startIdx = COLS * ROWS - recent.length;
  for (let i = 0; i < recent.length; i++) {
    const idx = startIdx + i;
    const col = Math.floor(idx / ROWS);
    const row = idx % ROWS;
    if (col >= 0 && col < COLS && row >= 0 && row < ROWS) {
      grid[row][col] = Math.max(0, Math.min(4, Number(recent[i].level || 0)));
    }
  }
  return grid;
}

function predictLandingX(bx, by, vx, vy) {
  if (vy <= 1.0) return SCR_X + SCR_W / 2.0;
  const tHit = (PADDLE_Y - BALL_R - by) / vy;
  if (tHit <= 0) return bx;
  const rawX = bx + vx * tHit;
  const left = SCR_X + BALL_R;
  const right = SCR_RIGHT - BALL_R;
  const span = right - left;
  const mod = (((rawX - left) % (2.0 * span)) + 2.0 * span) % (2.0 * span);
  return left + (mod > span ? 2.0 * span - mod : mod);
}

export function simulateBreakout(grid) {
  const bricks = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const level = grid[r][c];
      bricks.push({
        r,
        c,
        x: GRID_X0 + c * STEP_X,
        y: GRID_Y0 + r * STEP_Y,
        level,
        alive: level > 0,
        hitT: null,
      });
    }
  }

  const activeTotal = bricks.filter((b) => b.level > 0).length;
  let bx = SCR_X + SCR_W * 0.5;
  let by = PADDLE_Y - BALL_R - 1.0;
  let vx = 250.0;
  let vy = -360.0;
  let px = bx - PADDLE_W / 2.0;

  const ballFrames = [[0.0, bx, by]];
  const paddleFrames = [[0.0, px]];
  const hits = [];

  const steps = Math.floor(SIM_DUR / DT);
  let targetPx = px;
  let lastPaddleSample = 0.0;

  for (let step = 1; step <= steps; step++) {
    const t = step * DT;
    bx += vx * DT;
    by += vy * DT;

    let bounced = false;

    if (bx - BALL_R <= SCR_X) {
      bx = SCR_X + BALL_R;
      vx = Math.abs(vx);
      bounced = true;
    } else if (bx + BALL_R >= SCR_RIGHT) {
      bx = SCR_RIGHT - BALL_R;
      vx = -Math.abs(vx);
      bounced = true;
    }

    if (by - BALL_R <= SCR_Y) {
      by = SCR_Y + BALL_R;
      vy = Math.abs(vy);
      bounced = true;
    }

    // Brick AABB-circle collision
    let hitBrick = null;
    let minDist = Infinity;
    for (const b of bricks) {
      if (!b.alive) continue;
      const cx = Math.max(b.x, Math.min(bx, b.x + BRICK_W));
      const cy = Math.max(b.y, Math.min(by, b.y + BRICK_H));
      const dx = bx - cx;
      const dy = by - cy;
      const d2 = dx * dx + dy * dy;
      if (d2 <= BALL_R * BALL_R && d2 < minDist) {
        minDist = d2;
        hitBrick = b;
      }
    }

    if (hitBrick) {
      hitBrick.alive = false;
      hitBrick.hitT = t;
      hits.push({
        t,
        cx: hitBrick.x + BRICK_W / 2.0,
        cy: hitBrick.y + BRICK_H / 2.0,
        level: hitBrick.level,
      });
      const bcx = hitBrick.x + BRICK_W / 2.0;
      const bcy = hitBrick.y + BRICK_H / 2.0;
      const ox = BRICK_W / 2.0 + BALL_R - Math.abs(bx - bcx);
      const oy = BRICK_H / 2.0 + BALL_R - Math.abs(by - bcy);
      if (ox < oy) vx = -vx;
      else vy = -vy;
      if (Math.abs(vy) < 165.0) vy = Math.sign(vy || 1) * 190.0;
      bounced = true;
    }

    // Smart brick-seeking paddle tracking
    if (vy > 0) {
      const landX = predictLandingX(bx, by, vx, vy);
      const aliveBricks = bricks.filter((b) => b.alive);
      let aimShift = 0.0;
      if (aliveBricks.length > 0) {
        aliveBricks.sort((a, b) => {
          if (b.r !== a.r) return b.r - a.r;
          return Math.abs(a.x + BRICK_W / 2.0 - landX) - Math.abs(b.x + BRICK_W / 2.0 - landX);
        });
        const pick = aliveBricks[hits.length % Math.min(5, aliveBricks.length)];
        const targetBx = pick.x + BRICK_W / 2.0;
        const targetBy = pick.y + BRICK_H / 2.0;
        const dyUp = Math.max(40.0, PADDLE_Y - targetBy);
        const desiredAngle = Math.max(-1.05, Math.min(1.05, Math.atan2(targetBx - landX, dyUp)));
        const desiredRel = Math.max(-0.85, Math.min(0.85, desiredAngle / 1.08));
        aimShift = desiredRel * (PADDLE_W / 2.0);
      }
      targetPx = landX - PADDLE_W / 2.0 - aimShift;
    } else {
      targetPx = bx * 0.55 + (SCR_X + SCR_W / 2.0) * 0.45 - PADDLE_W / 2.0;
    }

    targetPx = Math.max(SCR_X + 6.0, Math.min(SCR_RIGHT - PADDLE_W - 6.0, targetPx));
    const maxMove = 560.0 * DT;
    const diff = targetPx - px;
    px += Math.abs(diff) > maxMove ? Math.sign(diff) * maxMove : diff;

    // Paddle rebound
    if (vy > 0 && by + BALL_R >= PADDLE_Y) {
      if (bx < px + 4.0) px = Math.max(SCR_X + 6.0, bx - 12.0);
      else if (bx > px + PADDLE_W - 4.0) px = Math.min(SCR_RIGHT - PADDLE_W - 6.0, bx - PADDLE_W + 12.0);

      by = PADDLE_Y - BALL_R;
      const relHit = Math.max(-0.88, Math.min(0.88, (bx - (px + PADDLE_W / 2.0)) / (PADDLE_W / 2.0)));
      const speed = 465.0;
      const angle = relHit * 1.08;
      vx = speed * Math.sin(angle);
      if (Math.abs(vx) < 75.0) vx = Math.sign(vx || 1) * 95.0;
      vy = -Math.sqrt(Math.max(210.0 * 210.0, speed * speed - vx * vx));
      bounced = true;
      paddleFrames.push([t, px]);
      lastPaddleSample = t;
    }

    if (bounced) ballFrames.push([t, bx, by]);
    if (t - lastPaddleSample >= 0.22) {
      paddleFrames.push([t, px]);
      lastPaddleSample = t;
    }
  }

  ballFrames.push([SIM_DUR, bx, by]);
  paddleFrames.push([SIM_DUR, px]);

  return { bricks, activeTotal, hits, ballFrames, paddleFrames };
}

function fmtSeq(nums, dec = 1) {
  return nums.map((n) => n.toFixed(dec)).join(';');
}

function sampleBallAt(frames, tQuery) {
  if (tQuery <= 0) return [frames[0][1], frames[0][2]];
  const last = frames[frames.length - 1];
  if (tQuery >= last[0]) return [last[1], last[2]];
  for (let i = 0; i < frames.length - 1; i++) {
    const [t0, x0, y0] = frames[i];
    const [t1, x1, y1] = frames[i + 1];
    if (t0 <= tQuery && tQuery <= t1) {
      const u = (tQuery - t0) / Math.max(1e-6, t1 - t0);
      return [x0 + (x1 - x0) * u, y0 + (y1 - y0) * u];
    }
  }
  return [last[1], last[2]];
}

export function renderBreakoutSvg(sim, totalContributions, themeName) {
  const t = THEMES[themeName];
  const { bricks, hits, ballFrames, paddleFrames } = sim;
  const activeTotal = Math.max(1, sim.activeTotal);
  const brokenCount = hits.length;

  const ghostRects = [];
  const activeRects = [];
  for (const b of bricks) {
    const bx = b.x.toFixed(1);
    const by = b.y.toFixed(1);
    ghostRects.push(
      `<rect x="${bx}" y="${by}" width="${BRICK_W.toFixed(1)}" height="${BRICK_H.toFixed(1)}" rx="1.5" fill="${t.emptyCell}" stroke="${t.emptyStroke}" stroke-width="0.7" />`
    );
    if (b.level > 0) {
      const fill = t.levels[b.level];
      if (b.hitT !== null) {
        const kt = Math.max(0.002, Math.min(0.994, b.hitT / SIM_DUR));
        const kt2 = Math.min(0.998, kt + 0.003);
        activeRects.push(
          `<rect x="${bx}" y="${by}" width="${BRICK_W.toFixed(1)}" height="${BRICK_H.toFixed(1)}" rx="1.5" fill="${fill}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;${kt.toFixed(4)};${kt2.toFixed(4)};1" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" /></rect>`
        );
      } else {
        activeRects.push(
          `<rect x="${bx}" y="${by}" width="${BRICK_W.toFixed(1)}" height="${BRICK_H.toFixed(1)}" rx="1.5" fill="${fill}" />`
        );
      }
    }
  }

  const debrisSvg = [];
  const offsets = [[-13, -10], [13, -10], [-11, 11], [11, 11]];
  for (const ev of hits.slice(0, 36)) {
    const t0 = ev.t / SIM_DUR;
    const t1 = Math.min(0.996, (ev.t + 0.34) / SIM_DUR);
    const tPre = Math.max(0.0005, t0 - 0.001);
    const chipFill = ev.level === 4 ? t.accent : t.ink;
    const cx = ev.cx - 1.5;
    const cy = ev.cy - 1.5;
    for (const [dx, dy] of offsets) {
      debrisSvg.push(
        `<rect x="${cx.toFixed(1)}" y="${cy.toFixed(1)}" width="3" height="3" fill="${chipFill}" opacity="0">` +
          `<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;${tPre.toFixed(4)};${t0.toFixed(4)};${t1.toFixed(4)};1" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />` +
          `<animate attributeName="x" values="${cx.toFixed(1)};${cx.toFixed(1)};${(cx + dx).toFixed(1)};${(cx + dx).toFixed(1)}" keyTimes="0;${t0.toFixed(4)};${t1.toFixed(4)};1" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />` +
          `<animate attributeName="y" values="${cy.toFixed(1)};${cy.toFixed(1)};${(cy + dy).toFixed(1)};${(cy + dy).toFixed(1)}" keyTimes="0;${t0.toFixed(4)};${t1.toFixed(4)};1" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />` +
          `</rect>`
      );
    }
  }

  const ballKt = fmtSeq(ballFrames.map((f) => f[0] / SIM_DUR), 4);
  const ballXs = fmtSeq(ballFrames.map((f) => f[1]), 1);
  const ballYs = fmtSeq(ballFrames.map((f) => f[2]), 1);

  const trailSvgs = [];
  for (const [lag, rad, op] of [[0.055, 3.3, '0.45'], [0.11, 2.2, '0.22']]) {
    const tXs = [];
    const tYs = [];
    for (const [ft] of ballFrames) {
      const [sx, sy] = sampleBallAt(ballFrames, Math.max(0.0, ft - lag));
      tXs.push(sx);
      tYs.push(sy);
    }
    trailSvgs.push(
      `<circle cx="${tXs[0].toFixed(1)}" cy="${tYs[0].toFixed(1)}" r="${rad}" fill="${t.trail}" opacity="${op}">` +
        `<animate attributeName="cx" values="${fmtSeq(tXs, 1)}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />` +
        `<animate attributeName="cy" values="${fmtSeq(tYs, 1)}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />` +
        `</circle>`
    );
  }

  const padKt = fmtSeq(paddleFrames.map((f) => f[0] / SIM_DUR), 4);
  const padXs = fmtSeq(paddleFrames.map((f) => f[1]), 1);
  const padCoreXs = fmtSeq(paddleFrames.map((f) => f[1] + PADDLE_W / 2.0 - 11.0), 1);

  const progMaxW = 180.0;
  const progKtList = [0.0];
  const progWList = [2.0];
  hits.forEach((ev, idx) => {
    const kt = Math.max(0.002, Math.min(0.995, ev.t / SIM_DUR));
    const w = Math.max(2.0, Math.min(progMaxW, ((idx + 1) / activeTotal) * progMaxW));
    progKtList.push(kt);
    progWList.push(w);
  });
  progKtList.push(1.0);
  progWList.push(progWList[progWList.length - 1]);

  const grilleSlots = Array.from({ length: 6 }, (_, i) =>
    `<rect x="${24 + i * 5}" y="16" width="2" height="14" rx="0.5" fill="${t.border}" />`
  ).join('');

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}" role="img" aria-label="Live Physics Contribution Breakout Arcade — Smashing real GitHub commits">
  <defs>
    <clipPath id="brk-clip-${themeName}">
      <rect x="0.5" y="0.5" width="${WIDTH - 1}" height="${HEIGHT - 1}" rx="8" />
    </clipPath>
  </defs>

  <style>
    .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }
    .hdr-title { font-size: 11px; font-weight: 800; letter-spacing: 1.2px; fill: ${t.ink}; }
    .hdr-badge { font-size: 9.5px; font-weight: 800; letter-spacing: 1px; fill: ${t.ink}; }
    .hdr-sub { font-size: 10px; font-weight: 600; letter-spacing: 0.8px; fill: ${t.muted}; }
    .foot-tag { font-size: 9.5px; font-weight: 700; letter-spacing: 0.8px; fill: ${t.muted}; }
    .foot-cta { font-size: 10px; font-weight: 800; letter-spacing: 0.9px; fill: ${t.accent}; }
    @keyframes stepBlink {
      0%, 49% { opacity: 1; }
      50%, 100% { opacity: 0.25; }
    }
    .live-sq { animation: stepBlink 1.4s steps(2, end) infinite; }
  </style>

  <g clip-path="url(#brk-clip-${themeName})">
    <rect x="0" y="0" width="${WIDTH}" height="${HEIGHT}" fill="${t.chassis}" />
    <rect x="0" y="0" width="${WIDTH}" height="46" fill="${t.bezel}" />
    <line x1="0" y1="46" x2="${WIDTH}" y2="46" stroke="${t.border}" stroke-width="1" />
    <rect x="0" y="314" width="${WIDTH}" height="46" fill="${t.bezel}" />
    <line x1="0" y1="314" x2="${WIDTH}" y2="314" stroke="${t.border}" stroke-width="1" />
    <rect x="0" y="0" width="5" height="${HEIGHT}" fill="${t.accent}" />
  </g>

  <rect x="0.5" y="0.5" width="${WIDTH - 1}" height="${HEIGHT - 1}" rx="8" fill="none" stroke="${t.border}" stroke-width="1" />

  ${grilleSlots}
  <text x="64" y="21" class="mono hdr-title">IMESH-ARCADE // UNIT-01</text>
  <text x="64" y="35" class="mono hdr-sub">LIVE CONTRIBUTION BREAKOUT  ·  ${totalContributions} COMMITS / YR</text>

  <text x="454" y="20" class="mono hdr-sub">CLEAR PROGRESS (${brokenCount}/${activeTotal} BRICKS)</text>
  <rect x="454" y="27" width="${progMaxW.toFixed(0)}" height="7" rx="1.5" fill="${t.chassis}" stroke="${t.border}" stroke-width="1" />
  <rect x="454" y="27" width="2" height="7" rx="1.5" fill="${t.accent}">
    <animate attributeName="width" values="${fmtSeq(progWList, 1)}" keyTimes="${fmtSeq(progKtList, 4)}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
  </rect>

  <rect x="748" y="13" width="128" height="20" rx="3" fill="${t.chassis}" stroke="${t.border}" stroke-width="1" />
  <rect x="757" y="20" width="6" height="6" rx="1" fill="${t.accent}" class="live-sq" />
  <text x="770" y="26.5" class="mono hdr-badge">REAL PHYSICS</text>

  <rect x="${SCR_X.toFixed(0)}" y="${SCR_Y.toFixed(0)}" width="${SCR_W.toFixed(0)}" height="${SCR_H.toFixed(0)}" rx="4" fill="${t.screen}" stroke="${t.border}" stroke-width="1" />
  <line x1="${(SCR_X + 10).toFixed(0)}" y1="${(PADDLE_Y + PADDLE_H / 2.0).toFixed(1)}" x2="${(SCR_RIGHT - 10).toFixed(0)}" y2="${(PADDLE_Y + PADDLE_H / 2.0).toFixed(1)}" stroke="${t.rail}" stroke-width="1" stroke-dasharray="3 5" />

  ${ghostRects.join('')}
  ${activeRects.join('')}
  ${debrisSvg.join('')}
  ${trailSvgs.join('')}

  <circle cx="${ballFrames[0][1].toFixed(1)}" cy="${ballFrames[0][2].toFixed(1)}" r="${BALL_R.toFixed(1)}" fill="${t.ball}">
    <animate attributeName="cx" values="${ballXs}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
    <animate attributeName="cy" values="${ballYs}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
  </circle>
  <circle cx="${ballFrames[0][1].toFixed(1)}" cy="${ballFrames[0][2].toFixed(1)}" r="1.8" fill="${t.ballCore}">
    <animate attributeName="cx" values="${ballXs}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
    <animate attributeName="cy" values="${ballYs}" keyTimes="${ballKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
  </circle>

  <rect x="${paddleFrames[0][1].toFixed(1)}" y="${PADDLE_Y.toFixed(1)}" width="${PADDLE_W.toFixed(1)}" height="${PADDLE_H.toFixed(1)}" rx="2" fill="${t.paddle}">
    <animate attributeName="x" values="${padXs}" keyTimes="${padKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
  </rect>
  <rect x="${(paddleFrames[0][1] + PADDLE_W / 2.0 - 11.0).toFixed(1)}" y="${PADDLE_Y.toFixed(1)}" width="22" height="${PADDLE_H.toFixed(1)}" rx="1" fill="${t.paddleCore}">
    <animate attributeName="x" values="${padCoreXs}" keyTimes="${padKt}" dur="${SIM_DUR.toFixed(1)}s" repeatCount="indefinite" />
  </rect>

  <rect x="24" y="326" width="136" height="22" rx="3" fill="${t.chassis}" stroke="${t.border}" stroke-width="1" />
  <text x="92" y="340.5" text-anchor="middle" class="mono foot-tag">ENGINE: NODE.JS 2D</text>

  <rect x="168" y="326" width="154" height="22" rx="3" fill="${t.chassis}" stroke="${t.border}" stroke-width="1" />
  <text x="245" y="340.5" text-anchor="middle" class="mono foot-tag">DATA: LIVE COMMITS</text>

  <rect x="330" y="326" width="120" height="22" rx="3" fill="${t.chassis}" stroke="${t.border}" stroke-width="1" />
  <text x="390" y="340.5" text-anchor="middle" class="mono foot-tag">SYNC: AUTO DAILY</text>

  <text x="874" y="341" text-anchor="end" class="mono foot-cta">CLICK TO PLAY 60FPS ARCADE ON PORTFOLIO ↗</text>
</svg>
`;
}

if (process.argv.includes('--self-test')) {
  const grid = buildGridFromDays([]);
  const sim = simulateBreakout(grid);
  if (sim.hits.length < 10) throw new Error(`Expected >=10 brick hits, got ${sim.hits.length}`);
  for (const th of ['dark', 'light']) {
    const svg = renderBreakoutSvg(sim, 287, th);
    for (const banned of ['feGaussianBlur', 'feDropShadow', 'drop-shadow', 'box-shadow', 'radialGradient']) {
      if (svg.includes(banned)) throw new Error(`Banned glow token found: ${banned}`);
    }
  }
  console.log(`BREAKOUT ENGINE (JS) SELF-TEST PASSED! (hits=${sim.hits.length}, keyframes=${sim.ballFrames.length})`);
}
