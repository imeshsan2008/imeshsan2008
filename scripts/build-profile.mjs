#!/usr/bin/env node
/**
 * Master Profile OS Builder for imeshsan2008 (100% Pure Node.js — Zero Python, Zero npm deps).
 * Generates all 22 dual-theme (dark & light) zero-glow Swiss-Industrial SVGs + assets/contrib.json:
 *   1. Hero Workstation OS Banner (hero-dark/light.svg)
 *   2. Live Physics Contribution Breakout Console (breakout-dark/light.svg) + assets/contrib.json
 *   3. 4 Individually Clickable Project Bento Cards (proj-*-dark/light.svg)
 *   4. 3-Panel Live Telemetry & 12-Week Animated Pulse (telemetry-dark/light.svg)
 *   5. Capabilities & Connected Career Timeline Blueprint (blueprint-dark/light.svg)
 *   6. Custom Flat Hardware Action Dock Keycaps (dock-*.svg)
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildGridFromDays, renderBreakoutSvg, simulateBreakout } from './breakout-engine.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const ASSETS = path.join(ROOT, 'assets');
const USERNAME = process.env.GITHUB_USERNAME || 'imeshsan2008';
const TOKEN = process.env.GITHUB_TOKEN || '';

const THEMES = {
  dark: {
    bg: '#0D1117',
    surface: '#161B22',
    inset: '#090C10',
    border: '#30363D',
    borderSoft: '#21262D',
    ink: '#E6EDF3',
    muted: '#8B949E',
    subtle: '#6E7681',
    accent: '#DC2626',
    grid: '#1B212A',
    bars: ['#DC2626', '#E6EDF3', '#8B949E', '#484F58'],
    sparkBar: '#30363D',
    sparkMid: '#6E7681',
    sparkPeak: '#DC2626',
  },
  light: {
    bg: '#FFFFFF',
    surface: '#F6F8FA',
    inset: '#F3F5F7',
    border: '#D0D7DE',
    borderSoft: '#E5E9EE',
    ink: '#1F2328',
    muted: '#57606A',
    subtle: '#656D76',
    accent: '#CC0000',
    grid: '#EAEEF2',
    bars: ['#CC0000', '#1F2328', '#656D76', '#B0B8C1'],
    sparkBar: '#D0D7DE',
    sparkMid: '#656D76',
    sparkPeak: '#CC0000',
  },
};

function esc(str) {
  return String(str)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function fmtBytes(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${Math.round(n / 1_000)} KB`;
  return `${n} B`;
}

async function httpGetText(url, { accept = null, useAuth = false } = {}) {
  const headers = { 'User-Agent': `${USERNAME}-profile-os-js` };
  if (accept) headers.Accept = accept;
  if (useAuth && TOKEN) headers.Authorization = `Bearer ${TOKEN}`;
  const res = await fetch(url, { headers, signal: AbortSignal.timeout(15000) });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

async function ghJson(url) {
  return JSON.parse(await httpGetText(url, { accept: 'application/vnd.github+json', useAuth: true }));
}

async function fetchContributions() {
  try {
    const raw = await httpGetText(`https://github.com/users/${USERNAME}/contributions`);
    const matches = [...raw.matchAll(/data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"/g)];
    const days = matches
      .map((m) => ({ date: m[1], level: Number(m[2]) }))
      .sort((a, b) => a.date.localeCompare(b.date));

    const totalM = raw.match(/([\d,]+)\s+contributions?\s+in the last year/);
    const total = totalM
      ? Number(totalM[1].replaceAll(',', ''))
      : days.reduce((acc, d) => acc + d.level * 2, 0);

    const last84 = days.slice(-84);
    const weekly = [];
    for (let i = 0; i < last84.length; i += 7) {
      weekly.push(last84.slice(i, i + 7).reduce((s, d) => s + d.level, 0));
    }
    while (weekly.length < 12) weekly.unshift(0);
    return { days, total, weekly: weekly.slice(-12) };
  } catch {
    return { days: [], total: 287, weekly: [2, 4, 1, 5, 3, 6, 4, 2, 7, 5, 3, 4] };
  }
}

async function fetchGithubMetrics() {
  const fallback = {
    publicRepos: 26,
    originalRepos: 25,
    publicGists: 12,
    followers: 2,
    totalStars: 0,
    totalForks: 2,
    totalBytes: 4_512_752,
    createdYear: '2022',
    languages: [
      ['JavaScript', 62.7],
      ['HTML', 18.1],
      ['CSS', 16.6],
      ['Other', 2.6],
    ],
    updatedDate: new Date().toISOString().slice(0, 10),
  };

  try {
    const user = await ghJson(`https://api.github.com/users/${USERNAME}`);
    const repos = [];
    let page = 1;
    while (true) {
      const batch = await ghJson(`https://api.github.com/users/${USERNAME}/repos?per_page=100&type=owner&page=${page}`);
      if (!batch.length) break;
      repos.push(...batch);
      if (batch.length < 100) break;
      page++;
    }

    const orig = repos.filter((r) => !r.fork);
    const totalStars = repos.reduce((s, r) => s + Number(r.stargazers_count || 0), 0);
    const totalForks = repos.reduce((s, r) => s + Number(r.forks_count || 0), 0);

    const langBytes = {};
    let scanned = 0;
    let rateLimited = false;
    for (const r of orig) {
      if (!r.languages_url) continue;
      try {
        const ldata = await ghJson(r.languages_url);
        scanned++;
        for (const [k, v] of Object.entries(ldata)) {
          langBytes[k] = (langBytes[k] || 0) + Number(v);
        }
      } catch {
        rateLimited = true;
        break;
      }
    }

    let totalBytes = Object.values(langBytes).reduce((a, b) => a + b, 0);
    let languages = fallback.languages;
    if (!rateLimited && scanned >= Math.max(1, Math.floor(orig.length * 0.8)) && totalBytes > 0) {
      const sorted = Object.entries(langBytes).sort((a, b) => b[1] - a[1]);
      const top3 = sorted.slice(0, 3).map(([k, v]) => [k, Math.round((v / totalBytes) * 1000) / 10]);
      const rest = sorted.slice(3).reduce((s, [, v]) => s + v, 0);
      if (rest > 0) {
        const sum3 = top3.reduce((s, [, p]) => s + p, 0);
        top3.push(['Other', Math.round(Math.max(0.1, 100 - sum3) * 10) / 10]);
      }
      languages = top3;
    } else {
      totalBytes = fallback.totalBytes;
    }

    return {
      publicRepos: Number(user.public_repos ?? repos.length),
      originalRepos: orig.length,
      publicGists: Number(user.public_gists ?? 0),
      followers: Number(user.followers ?? 0),
      totalStars,
      totalForks,
      totalBytes,
      createdYear: String(user.created_at || '2022').slice(0, 4),
      languages,
      updatedDate: new Date().toISOString().slice(0, 10),
    };
  } catch {
    return fallback;
  }
}

function renderHeroSvg(metrics, totalContribs, theme) {
  const t = THEMES[theme];
  const vol = fmtBytes(metrics.totalBytes);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="292" viewBox="0 0 900 292" role="img" aria-label="IMESH OS — Imesh Sandeepa, Founder at Vexora IT Solutions">
  <defs>
    <clipPath id="hero-clip-${theme}">
      <rect x="0.5" y="0.5" width="899" height="291" rx="8" />
    </clipPath>
    <pattern id="hero-grid-${theme}" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="${t.grid}" stroke-width="1" />
    </pattern>
  </defs>

  <style>
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }
    .sysbar { font-size: 10px; font-weight: 700; letter-spacing: 1px; fill: ${t.muted}; }
    .sysbar-hi { font-size: 10px; font-weight: 800; letter-spacing: 1px; fill: ${t.ink}; }
    .name { font-size: 42px; font-weight: 900; letter-spacing: -1.1px; fill: ${t.ink}; }
    .role-txt { font-size: 12px; font-weight: 700; letter-spacing: 1.1px; fill: ${t.ink}; }
    .bio-txt { font-size: 13px; font-weight: 500; fill: ${t.muted}; }
    .kpi-k { font-size: 9px; font-weight: 700; letter-spacing: 0.9px; fill: ${t.subtle}; }
    .kpi-v { font-size: 16px; font-weight: 800; fill: ${t.ink}; }
    .kpi-va { font-size: 16px; font-weight: 800; fill: ${t.accent}; }
    .term-cmd { font-size: 10.5px; font-weight: 700; fill: ${t.ink}; }
    .term-k { font-size: 10.5px; font-weight: 700; fill: ${t.accent}; }
    .term-v { font-size: 10.5px; font-weight: 500; fill: ${t.muted}; }
    @keyframes blinkSq { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0.2; } }
    .pulse { animation: blinkSq 1.4s steps(2, end) infinite; }
    @keyframes r1 { 0%, 30% { opacity: 1; } 33%, 97% { opacity: 0; } 100% { opacity: 1; } }
    @keyframes r2 { 0%, 32% { opacity: 0; } 35%, 63% { opacity: 1; } 66%, 100% { opacity: 0; } }
    @keyframes r3 { 0%, 65% { opacity: 0; } 68%, 96% { opacity: 1; } 99%, 100% { opacity: 0; } }
    .cycle1 { animation: r1 9s linear infinite; }
    .cycle2 { animation: r2 9s linear infinite; opacity: 0; }
    .cycle3 { animation: r3 9s linear infinite; opacity: 0; }
  </style>

  <g clip-path="url(#hero-clip-${theme})">
    <rect x="0" y="0" width="900" height="292" fill="${t.bg}" />
    <rect x="0" y="34" width="548" height="258" fill="url(#hero-grid-${theme})" opacity="0.65" />
    <rect x="0" y="0" width="900" height="34" fill="${t.surface}" />
    <line x1="0" y1="34" x2="900" y2="34" stroke="${t.border}" stroke-width="1" />
    <rect x="548" y="34" width="352" height="258" fill="${t.surface}" />
    <line x1="548" y1="34" x2="548" y2="292" stroke="${t.border}" stroke-width="1" />
    <rect x="0" y="0" width="5" height="292" fill="${t.accent}" />
  </g>

  <rect x="0.5" y="0.5" width="899" height="291" rx="8" fill="none" stroke="${t.border}" stroke-width="1" />

  <rect x="20" y="13" width="8" height="8" rx="1" fill="${t.accent}" />
  <text x="36" y="21" class="mono sysbar-hi">IMESH // OS v2.6</text>
  <text x="168" y="21" class="mono sysbar">KELANIYA, LK  ·  06°57'N 79°55'E  ·  UTC+5:30</text>
  <rect x="708" y="13" width="6" height="6" rx="1" fill="${t.accent}" class="pulse" />
  <text x="721" y="20.5" class="mono sysbar-hi">ONLINE · OPEN TO BUILD</text>

  <text x="30" y="102" class="sans name">IMESH SANDEEPA<tspan fill="${t.accent}">.</tspan></text>

  <rect x="30" y="118" width="486" height="28" rx="3" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
  <rect x="30" y="118" width="3" height="28" fill="${t.accent}" />
  <text x="44" y="136" class="mono role-txt cycle1">&gt; FOUNDER @ VEXORA IT SOLUTIONS</text>
  <text x="44" y="136" class="mono role-txt cycle2">&gt; FULL-STACK ENGINEER · SAAS &amp; DESKTOP SYSTEMS</text>
  <text x="44" y="136" class="mono role-txt cycle3">&gt; WEB &amp; GRAPHIC DESIGNER · UI ARCHITECTURE</text>

  <text x="30" y="174" class="sans bio-txt">Building scalable SaaS platforms, zero-tracking Chrome extensions,</text>
  <text x="30" y="193" class="sans bio-txt">desktop utilities, and sharp visual systems without noise.</text>

  <g transform="translate(30, 214)">
    <rect x="0" y="0" width="114" height="54" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="12" y="18" class="mono kpi-k">REPOSITORIES</text>
    <text x="12" y="42" class="mono kpi-v">${metrics.publicRepos}</text>

    <rect x="124" y="0" width="114" height="54" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="136" y="18" class="mono kpi-k">12M COMMITS</text>
    <text x="136" y="42" class="mono kpi-va">${totalContribs}</text>

    <rect x="248" y="0" width="114" height="54" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="260" y="18" class="mono kpi-k">CODEBASE</text>
    <text x="260" y="42" class="mono kpi-v">${vol}</text>

    <rect x="372" y="0" width="114" height="54" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="384" y="18" class="mono kpi-k">SINCE</text>
    <text x="384" y="42" class="mono kpi-v">${metrics.createdYear}</text>
  </g>

  <rect x="570" y="54" width="308" height="156" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1" />
  <rect x="570" y="54" width="308" height="24" rx="4" fill="${t.bg}" />
  <line x1="570" y1="78" x2="878" y2="78" stroke="${t.border}" stroke-width="1" />
  <text x="582" y="70" class="mono term-cmd">$ whoami --spec</text>
  <rect x="858" y="62" width="10" height="8" rx="1" fill="${t.accent}" class="pulse" />

  <text x="582" y="100" class="mono term-k">org     </text><text x="646" y="100" class="mono term-v">Vexora IT Solutions (Founder)</text>
  <text x="582" y="121" class="mono term-k">focus   </text><text x="646" y="121" class="mono term-v">SaaS · Extensions · Utilities</text>
  <text x="582" y="142" class="mono term-k">code    </text><text x="646" y="142" class="mono term-v">JS · Node · Python · Postgres</text>
  <text x="582" y="163" class="mono term-k">design  </text><text x="646" y="163" class="mono term-v">UI/UX · PS · AI · CorelDRAW</text>
  <text x="582" y="184" class="mono term-k">deploy  </text><text x="646" y="184" class="mono term-v">DigitalOcean · Koyeb · Linux</text>
  <text x="582" y="201" class="mono kpi-k">STATUS: SHIPPING CLEAN SYSTEMS</text>

  <rect x="570" y="222" width="308" height="46" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1" />
  <g transform="translate(584, 232)">
    <rect x="0" y="14" width="5" height="12" rx="1" fill="${t.accent}"><animate attributeName="height" values="8;24;12;20;8" dur="1.9s" repeatCount="indefinite"/><animate attributeName="y" values="18;2;14;6;18" dur="1.9s" repeatCount="indefinite"/></rect>
    <rect x="9" y="6" width="5" height="20" rx="1" fill="${t.ink}"><animate attributeName="height" values="20;10;24;12;20" dur="1.5s" repeatCount="indefinite"/><animate attributeName="y" values="6;16;2;14;6" dur="1.5s" repeatCount="indefinite"/></rect>
    <rect x="18" y="10" width="5" height="16" rx="1" fill="${t.muted}"><animate attributeName="height" values="14;22;6;18;14" dur="2.1s" repeatCount="indefinite"/><animate attributeName="y" values="12;4;20;8;12" dur="2.1s" repeatCount="indefinite"/></rect>
    <rect x="27" y="4" width="5" height="22" rx="1" fill="${t.ink}"><animate attributeName="height" values="22;8;18;24;22" dur="1.7s" repeatCount="indefinite"/><animate attributeName="y" values="4;18;8;2;4" dur="1.7s" repeatCount="indefinite"/></rect>
    <rect x="36" y="12" width="5" height="14" rx="1" fill="${t.muted}"><animate attributeName="height" values="10;20;14;6;10" dur="2.3s" repeatCount="indefinite"/><animate attributeName="y" values="16;6;12;20;16" dur="2.3s" repeatCount="indefinite"/></rect>
    <rect x="45" y="8" width="5" height="18" rx="1" fill="${t.accent}"><animate attributeName="height" values="16;6;22;12;16" dur="1.6s" repeatCount="indefinite"/><animate attributeName="y" values="10;20;4;14;10" dur="1.6s" repeatCount="indefinite"/></rect>
  </g>

  <text x="650" y="242" class="mono term-cmd">SIGNAL // ACTIVE</text>
  <text x="650" y="257" class="mono kpi-k">PURE NODE.JS PROFILE ENGINE</text>

  <g transform="translate(850, 245)">
    <circle cx="0" cy="0" r="14" fill="none" stroke="${t.border}" stroke-width="1" stroke-dasharray="3 3">
      <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="18s" repeatCount="indefinite" />
    </circle>
    <rect x="-4" y="-4" width="8" height="8" fill="none" stroke="${t.ink}" stroke-width="1">
      <animateTransform attributeName="transform" type="rotate" from="360 0 0" to="0 0 0" dur="14s" repeatCount="indefinite" />
    </rect>
    <rect x="-1.5" y="-1.5" width="3" height="3" fill="${t.accent}" />
  </g>
</svg>
`;
}

const PROJECTS = [
  {
    slug: 'myslt',
    index: '01',
    category: 'CHROME MV3 + WPF',
    title: 'MySLT Tracker',
    line1: 'Open-source browser extension & Windows desktop',
    line2: 'widget to track SLT broadband usage, add-ons &',
    line3: 'billing with 100% local storage & zero tracking.',
    tags: ['CHROME MV3', 'JAVASCRIPT', 'WPF'],
    icon: 'gauge',
  },
  {
    slug: 'adobeshield',
    index: '02',
    category: 'DESKTOP UTILITY',
    title: 'AdobeShield',
    line1: 'Desktop firewall control utility designed to',
    line2: 'manage internet access & firewall rules cleanly',
    line3: 'for Adobe Creative Cloud desktop applications.',
    tags: ['DESKTOP', 'FIREWALL', 'UTILITY'],
    icon: 'shield',
  },
  {
    slug: 'trainify',
    index: '03',
    category: 'SAAS PLATFORM',
    title: 'Trainify',
    line1: 'Training management platform designed to',
    line2: 'organize learning schedules, streamline skill',
    line3: 'growth, and monitor task milestones clearly.',
    tags: ['FULL-STACK', 'WEB APP', 'SAAS'],
    icon: 'grid',
  },
  {
    slug: 'sharebox',
    index: '04',
    category: 'OFFLINE P2P',
    title: 'ShareBox',
    line1: 'Zero-internet local file sharing utility over',
    line2: 'Wi-Fi hotspot — transfer files across devices',
    line3: 'rapidly with no router or cloud middleman.',
    tags: ['LOCAL NET', 'HOTSPOT', 'P2P'],
    icon: 'nodes',
  },
];

function projectIcon(kind, t) {
  if (kind === 'gauge') {
    return (
      `<rect x="0" y="0" width="44" height="44" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1"/>` +
      `<path d="M 10 30 A 12 12 0 1 1 34 30" fill="none" stroke="${t.muted}" stroke-width="2"/>` +
      `<path d="M 10 30 A 12 12 0 0 1 28 19" fill="none" stroke="${t.accent}" stroke-width="2"/>` +
      `<line x1="22" y1="28" x2="30" y2="18" stroke="${t.ink}" stroke-width="1.8"/>` +
      `<circle cx="22" cy="28" r="2.5" fill="${t.accent}"/>`
    );
  }
  if (kind === 'shield') {
    return (
      `<rect x="0" y="0" width="44" height="44" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1"/>` +
      `<polygon points="22,9 33,14 33,24 22,35 11,24 11,14" fill="none" stroke="${t.ink}" stroke-width="1.6"/>` +
      `<line x1="22" y1="14" x2="22" y2="29" stroke="${t.accent}" stroke-width="1.6"/>` +
      `<line x1="15" y1="21" x2="29" y2="21" stroke="${t.accent}" stroke-width="1.6"/>`
    );
  }
  if (kind === 'grid') {
    return (
      `<rect x="0" y="0" width="44" height="44" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1"/>` +
      `<rect x="10" y="10" width="10" height="10" rx="1" fill="${t.accent}"/>` +
      `<rect x="24" y="10" width="10" height="10" rx="1" fill="none" stroke="${t.ink}" stroke-width="1.5"/>` +
      `<rect x="10" y="24" width="10" height="10" rx="1" fill="none" stroke="${t.muted}" stroke-width="1.5"/>` +
      `<rect x="24" y="24" width="10" height="10" rx="1" fill="${t.ink}"/>`
    );
  }
  return (
    `<rect x="0" y="0" width="44" height="44" rx="4" fill="${t.inset}" stroke="${t.border}" stroke-width="1"/>` +
    `<line x1="14" y1="30" x2="22" y2="14" stroke="${t.muted}" stroke-width="1.4"/>` +
    `<line x1="30" y1="30" x2="22" y2="14" stroke="${t.muted}" stroke-width="1.4"/>` +
    `<line x1="14" y1="30" x2="30" y2="30" stroke="${t.muted}" stroke-width="1.4"/>` +
    `<circle cx="22" cy="14" r="3.5" fill="${t.accent}"/>` +
    `<circle cx="14" cy="30" r="3" fill="${t.ink}"/>` +
    `<circle cx="30" cy="30" r="3" fill="${t.ink}"/>`
  );
}

function renderProjectCard(proj, theme) {
  const t = THEMES[theme];
  const chips = [];
  let cx = 22;
  proj.tags.forEach((tag, idx) => {
    const w = Math.max(62, tag.length * 7 + 18);
    const bar = idx === 0 ? `<rect x="${cx}" y="140" width="2.5" height="22" fill="${t.accent}"/>` : '';
    chips.push(
      `<rect x="${cx}" y="140" width="${w}" height="22" rx="3" fill="${t.inset}" stroke="${t.border}" stroke-width="1"/>` +
        bar +
        `<text x="${(cx + w / 2).toFixed(1)}" y="154.5" text-anchor="middle" class="mono tag">${esc(tag)}</text>`
    );
    cx += w + 8;
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="440" height="182" viewBox="0 0 440 182" role="img" aria-label="${esc(proj.title)} — ${esc(proj.category)}">
  <style>
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }
    .idx { font-size: 10px; font-weight: 800; letter-spacing: 0.9px; fill: ${t.accent}; }
    .cat { font-size: 10px; font-weight: 600; letter-spacing: 0.9px; fill: ${t.subtle}; }
    .title { font-size: 19px; font-weight: 800; letter-spacing: -0.3px; fill: ${t.ink}; }
    .desc { font-size: 12px; font-weight: 500; fill: ${t.muted}; }
    .tag { font-size: 9.5px; font-weight: 700; letter-spacing: 0.6px; fill: ${t.ink}; }
    .arrow { font-size: 14px; font-weight: 700; fill: ${t.muted}; }
  </style>

  <rect x="0.5" y="0.5" width="439" height="181" rx="8" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
  <rect x="0.5" y="0.5" width="439" height="32" rx="8" fill="${t.bg}" />
  <rect x="0.5" y="24" width="439" height="9" fill="${t.bg}" />
  <line x1="0" y1="33" x2="440" y2="33" stroke="${t.border}" stroke-width="1" />

  <text x="22" y="21" class="mono idx">${esc(proj.index)}</text>
  <text x="44" y="21" class="mono cat">/  ${esc(proj.category)}</text>
  <text x="418" y="22" text-anchor="end" class="mono arrow">↗</text>

  <g transform="translate(22, 48)">${projectIcon(proj.icon, t)}</g>

  <text x="80" y="66" class="sans title">${esc(proj.title)}</text>
  <text x="80" y="86" class="sans desc">${esc(proj.line1)}</text>
  <text x="80" y="103" class="sans desc">${esc(proj.line2)}</text>
  <text x="80" y="120" class="sans desc">${esc(proj.line3)}</text>

  ${chips.join('')}
</svg>
`;
}

function renderTelemetrySvg(metrics, totalContribs, weeklyBars, theme) {
  const t = THEMES[theme];
  const langs = metrics.languages;
  const vol = fmtBytes(metrics.totalBytes);

  const maxWk = Math.max(...weeklyBars, 1);
  const peakIdx = weeklyBars.indexOf(Math.max(...weeklyBars));
  const barBaseY = 182.0;
  const maxBarH = 104.0;
  const barsSvg = weeklyBars.map((val, i) => {
    const bx = 324 + i * 22;
    const h = Math.max(8.0, (val / maxWk) * maxBarH);
    const by = barBaseY - h;
    const fill = i === peakIdx ? t.sparkPeak : val >= maxWk * 0.55 ? t.sparkMid : t.sparkBar;
    const delay = `${(i * 0.06).toFixed(2)}s`;
    return (
      `<rect x="${bx}" y="${by.toFixed(1)}" width="14" height="${h.toFixed(1)}" rx="1.5" fill="${fill}">` +
      `<animate attributeName="height" from="4" to="${h.toFixed(1)}" dur="0.55s" begin="${delay}" fill="freeze" />` +
      `<animate attributeName="y" from="${(barBaseY - 4).toFixed(1)}" to="${by.toFixed(1)}" dur="0.55s" begin="${delay}" fill="freeze" />` +
      `</rect>`
    );
  });

  const segX = 626.0;
  const segWTotal = 248.0;
  const gap = 2.0;
  const usable = segWTotal - gap * Math.max(0, langs.length - 1);
  const segs = [];
  const rowsSvg = [];
  let curr = segX;
  langs.slice(0, 4).forEach(([name, pct], idx) => {
    let sw = Math.max(4.0, usable * (pct / 100.0));
    if (idx === langs.length - 1) sw = Math.max(4.0, segX + segWTotal - curr);
    const color = t.bars[idx % t.bars.length];
    segs.push(`<rect x="${curr.toFixed(1)}" y="66" width="${sw.toFixed(1)}" height="10" rx="1.5" fill="${color}" />`);
    curr += sw + gap;

    const ry = 104 + idx * 25;
    rowsSvg.push(
      `<rect x="626" y="${ry - 9}" width="8" height="8" rx="1" fill="${color}" />` +
        `<text x="642" y="${ry - 1}" class="sans lang-n">${esc(name)}</text>` +
        `<text x="874" y="${ry - 1}" text-anchor="end" class="mono lang-p">${pct.toFixed(1)}%</text>`
    );
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="268" viewBox="0 0 900 268" role="img" aria-label="GitHub Telemetry, 12-Week Activity and Language Distribution">
  <style>
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }
    .hdr { font-size: 10px; font-weight: 800; letter-spacing: 1.1px; fill: ${t.subtle}; }
    .k { font-size: 9px; font-weight: 700; letter-spacing: 0.9px; fill: ${t.muted}; }
    .v { font-size: 19px; font-weight: 800; fill: ${t.ink}; }
    .va { font-size: 19px; font-weight: 800; fill: ${t.accent}; }
    .lang-n { font-size: 12px; font-weight: 600; fill: ${t.ink}; }
    .lang-p { font-size: 11.5px; font-weight: 700; fill: ${t.muted}; }
    .foot { font-size: 9.5px; font-weight: 600; letter-spacing: 0.8px; fill: ${t.subtle}; }
  </style>

  <rect x="0.5" y="0.5" width="899" height="267" rx="8" fill="${t.bg}" stroke="${t.border}" stroke-width="1" />
  <line x1="296" y1="18" x2="296" y2="218" stroke="${t.borderSoft}" stroke-width="1" />
  <line x1="604" y1="18" x2="604" y2="218" stroke="${t.borderSoft}" stroke-width="1" />

  <rect x="24" y="24" width="3" height="12" fill="${t.accent}" />
  <text x="34" y="34" class="mono hdr">TELEMETRY // LIVE</text>

  <g transform="translate(24, 52)">
    <rect x="0" y="0" width="120" height="68" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="12" y="20" class="mono k">PUBLIC REPOS</text>
    <text x="12" y="52" class="mono v">${metrics.publicRepos}</text>

    <rect x="130" y="0" width="120" height="68" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="142" y="20" class="mono k">ORIGINAL</text>
    <text x="142" y="52" class="mono v">${metrics.originalRepos}</text>

    <rect x="0" y="78" width="120" height="68" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="12" y="98" class="mono k">CODE VOLUME</text>
    <text x="12" y="130" class="mono va">${vol}</text>

    <rect x="130" y="78" width="120" height="68" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />
    <text x="142" y="98" class="mono k">PUBLIC GISTS</text>
    <text x="142" y="130" class="mono v">${metrics.publicGists}</text>
  </g>

  <rect x="318" y="24" width="3" height="12" fill="${t.accent}" />
  <text x="328" y="34" class="mono hdr">12-WEEK PULSE (${totalContribs}/YR)</text>

  <line x1="318" y1="80" x2="586" y2="80" stroke="${t.borderSoft}" stroke-width="1" stroke-dasharray="2 4" />
  <line x1="318" y1="131" x2="586" y2="131" stroke="${t.borderSoft}" stroke-width="1" stroke-dasharray="2 4" />
  <line x1="318" y1="182" x2="586" y2="182" stroke="${t.border}" stroke-width="1" />
  ${barsSvg.join('')}

  <text x="324" y="202" class="mono k">W-12</text>
  <text x="452" y="202" text-anchor="middle" class="mono k">PEAK IN CRIMSON</text>
  <text x="582" y="202" text-anchor="end" class="mono k">NOW</text>

  <rect x="626" y="24" width="3" height="12" fill="${t.accent}" />
  <text x="636" y="34" class="mono hdr">CODEBASE MIX</text>
  ${segs.join('')}
  ${rowsSvg.join('')}

  <line x1="0" y1="228" x2="900" y2="228" stroke="${t.borderSoft}" stroke-width="1" />
  <text x="24" y="252" class="mono foot">MEMBER SINCE ${metrics.createdYear}  ·  FORKS: ${metrics.totalForks}  ·  STARS: ${metrics.totalStars}  ·  FOLLOWERS: ${metrics.followers}</text>
  <text x="876" y="252" text-anchor="end" class="mono foot">AUTO-SYNCED VIA NODE.JS ACTIONS · ${metrics.updatedDate} UTC</text>
</svg>
`;
}

function renderBlueprintSvg(theme) {
  const t = THEMES[theme];
  const tracks = [
    ['01', 'FRONTEND & UI', 'HTML5 · CSS3 · JavaScript · Tailwind · Bootstrap', 9],
    ['02', 'BACKEND & SYSTEMS', 'Node.js · Python · PostgreSQL · REST · Chrome MV3', 8],
    ['03', 'DESIGN & VISUALS', 'UI/UX · Photoshop · Illustrator · Lightroom · CorelDRAW', 9],
    ['04', 'CLOUD & DEVOPS', 'DigitalOcean · Koyeb · Git · GitHub Actions · Linux', 8],
  ];

  const trackSvg = tracks.map(([num, title, items, ticks], idx) => {
    const ty = 58 + idx * 58;
    const blocks = Array.from({ length: 10 }, (_, k) => {
      const fill = k < ticks && idx === 0 ? t.accent : k < ticks ? t.ink : t.borderSoft;
      return `<rect x="${354 + k * 9}" y="${ty + 4}" width="6" height="9" rx="1" fill="${fill}" />`;
    }).join('');
    return (
      `<rect x="24" y="${ty - 6}" width="426" height="48" rx="4" fill="${t.surface}" stroke="${t.border}" stroke-width="1" />` +
      `<text x="36" y="${ty + 12}" class="mono idx">${esc(num)}</text>` +
      `<text x="58" y="${ty + 12}" class="mono cap-t">${esc(title)}</text>` +
      blocks +
      `<text x="36" y="${ty + 31}" class="sans cap-s">${esc(items)}</text>`
    );
  });

  const milestones = [
    ['2026 — NOW', 'Founder', 'Vexora IT Solutions · SaaS & Full-Stack Systems', true],
    ['2025', 'Graphic Design Intern', 'National Productivity Secretariat · Branding & UI', false],
    ['2025', 'NVQ Level 4 — Graphic Design', 'Maradana Technical College · Visual Communication', false],
    ['CERTIFIED', 'Professional Benchmarking', 'Global Benchmarking Network · Industry Standards', false],
  ];

  const msSvg = milestones.map(([yr, role, org, active], idx) => {
    const my = 64 + idx * 58;
    const fill = active ? t.accent : t.bg;
    const stroke = active ? t.accent : t.ink;
    const cls = active ? ' class="pulse"' : '';
    return (
      `<rect x="492" y="${my}" width="10" height="10" rx="1.5" fill="${fill}" stroke="${stroke}" stroke-width="1.5"${cls} />` +
      `<text x="516" y="${my + 9}" class="mono yr" fill="${active ? t.accent : t.subtle}">${esc(yr)}</text>` +
      `<text x="606" y="${my + 9}" class="sans m-role">${esc(role)}</text>` +
      `<text x="516" y="${my + 28}" class="sans m-org">${esc(org)}</text>`
    );
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="308" viewBox="0 0 900 308" role="img" aria-label="System Capabilities and Career Timeline">
  <style>
    .sans { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace; }
    .hdr { font-size: 10px; font-weight: 800; letter-spacing: 1.1px; fill: ${t.subtle}; }
    .idx { font-size: 10px; font-weight: 800; fill: ${t.accent}; }
    .cap-t { font-size: 11px; font-weight: 800; letter-spacing: 0.7px; fill: ${t.ink}; }
    .cap-s { font-size: 11px; font-weight: 500; fill: ${t.muted}; }
    .yr { font-size: 9.5px; font-weight: 800; letter-spacing: 0.7px; }
    .m-role { font-size: 13px; font-weight: 800; fill: ${t.ink}; }
    .m-org { font-size: 11px; font-weight: 500; fill: ${t.muted}; }
    @keyframes blinkSq { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0.35; } }
    .pulse { animation: blinkSq 1.5s steps(2, end) infinite; }
  </style>

  <rect x="0.5" y="0.5" width="899" height="307" rx="8" fill="${t.bg}" stroke="${t.border}" stroke-width="1" />
  <line x1="472" y1="20" x2="472" y2="288" stroke="${t.borderSoft}" stroke-width="1" />

  <rect x="24" y="24" width="3" height="12" fill="${t.accent}" />
  <text x="34" y="34" class="mono hdr">SYSTEM CAPABILITIES // STACK MATRIX</text>
  ${trackSvg.join('')}

  <rect x="494" y="24" width="3" height="12" fill="${t.accent}" />
  <text x="504" y="34" class="mono hdr">TRAJECTORY // EXPERIENCE &amp; CREDENTIALS</text>

  <line x1="497" y1="69" x2="497" y2="243" stroke="${t.border}" stroke-width="1.5" />
  ${msSvg.join('')}
</svg>
`;
}

function renderDockButtons() {
  const specs = [
    ['dock-arcade.svg', '▶ PLAY 60FPS ARCADE', 190, true],
    ['dock-portfolio.svg', 'PORTFOLIO ↗', 122, false],
    ['dock-linkedin.svg', 'LINKEDIN', 104, false],
    ['dock-instagram.svg', 'INSTAGRAM', 112, false],
    ['dock-gmail.svg', 'GMAIL', 84, false],
    ['dock-whatsapp.svg', 'WHATSAPP', 106, false],
  ];
  for (const [fname, label, w, primary] of specs) {
    const bg = primary ? '#CC0000' : '#161B22';
    const border = primary ? '#991B1B' : '#30363D';
    const topBar = primary ? '' : `<rect x="1" y="1" width="${w - 2}" height="2.5" rx="1" fill="#DC2626" />`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="34" viewBox="0 0 ${w} 34" role="img" aria-label="${esc(label)}">
  <rect x="0.5" y="0.5" width="${w - 1}" height="33" rx="4" fill="${bg}" stroke="${border}" stroke-width="1" />
  ${topBar}
  <text x="${(w / 2).toFixed(1)}" y="21.5" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" font-size="11" font-weight="800" letter-spacing="0.8" fill="#FFFFFF">${esc(label)}</text>
</svg>
`;
    fs.writeFileSync(path.join(ASSETS, fname), svg, 'utf8');
  }
}

async function main() {
  fs.mkdirSync(ASSETS, { recursive: true });

  const [{ days, total: totalContribs, weekly }, metrics] = await Promise.all([
    fetchContributions(),
    fetchGithubMetrics(),
  ]);

  const grid = buildGridFromDays(days);
  const sim = simulateBreakout(grid);

  // Export live contribution grid JSON for Portfolio Arcade (CORS-friendly via raw.githubusercontent.com)
  const contribPayload = {
    username: USERNAME,
    total_contributions: totalContribs,
    updated_at: new Date().toISOString(),
    rows: grid.length,
    cols: grid[0].length,
    grid,
  };
  fs.writeFileSync(path.join(ASSETS, 'contrib.json'), JSON.stringify(contribPayload), 'utf8');

  for (const theme of ['dark', 'light']) {
    fs.writeFileSync(path.join(ASSETS, `hero-${theme}.svg`), renderHeroSvg(metrics, totalContribs, theme), 'utf8');
    fs.writeFileSync(
      path.join(ASSETS, `breakout-${theme}.svg`),
      renderBreakoutSvg(sim, totalContribs, theme),
      'utf8'
    );
    fs.writeFileSync(
      path.join(ASSETS, `telemetry-${theme}.svg`),
      renderTelemetrySvg(metrics, totalContribs, weekly, theme),
      'utf8'
    );
    fs.writeFileSync(path.join(ASSETS, `blueprint-${theme}.svg`), renderBlueprintSvg(theme), 'utf8');
    for (const proj of PROJECTS) {
      fs.writeFileSync(path.join(ASSETS, `proj-${proj.slug}-${theme}.svg`), renderProjectCard(proj, theme), 'utf8');
    }
  }

  renderDockButtons();

  console.log(
    `BUILT IMESH // OS (PURE NODE.JS): contribs=${totalContribs}, breakout_hits=${sim.hits.length}/${sim.activeTotal}, ` +
      `repos=${metrics.publicRepos}, langs=${JSON.stringify(metrics.languages)}`
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
