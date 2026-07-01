# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""The site theme: the nirs4all.org palette/fonts/hero/nav/footer CSS (shared across the family) plus
papers-specific component styles (pipeline steps, reference list, the live replay panel).

The ``:root`` palette, fonts, ``.section-*`` backdrops, glassmorphic nav, buttons, hero, KPI, panels,
tables, lightbox and footer are kept byte-for-byte aligned with ``nirs4all-datasets`` so the papers
site "claque" the same way. Self-contained: one inline ``<style>`` + the Google Fonts link; works
from ``file://``.
"""
from __future__ import annotations

FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,500;1,600'
    "&family=Inter:wght@400;500;600;700;800"
    '&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
)

_BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --teal:    #0d9488;
  --teal-d:  #0f766e;
  --teal-l:  #2dd4bf;
  --cyan:    #06b6d4;
  --cyan-d:  #0891b2;
  --indigo:  #4f46e5;
  --indigo-d:#4338ca;
  --green:   #10b981;
  --amber:   #d97706;

  --paper:    #faf7f0;
  --paper-2:  #f3efe5;
  --bg:       #ffffff;
  --bg-alt:   #f5f7fa;
  --bg-grid:  #f7f5ef;
  --bg-code:  #0b1220;
  --surface:  #ffffff;
  --border:   #e2e8f0;
  --border-warm: #e8e2d3;
  --text:     #0f172a;
  --text-2:   #475569;
  --text-3:   #64748b;

  --shadow:   0 4px 16px -4px rgba(17,24,39,0.08), 0 2px 4px -2px rgba(17,24,39,0.04);
  --shadow-lg: 0 20px 40px -12px rgba(17,24,39,0.10);
  --radius:   16px;
  --radius-sm: 10px;

  --font:    'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --display: 'IBM Plex Sans', 'Inter', -apple-system, system-ui, sans-serif;
  --mono:    'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;

  --k-pre:   #0d9488;
  --k-target:#d97706;
  --k-model: #4f46e5;
  --k-split: #64748b;
}

body {
  font-family: var(--font); background: var(--bg); color: var(--text);
  line-height: 1.7; overflow-x: hidden; -webkit-font-smoothing: antialiased;
}
a { color: var(--teal); text-decoration: none; transition: color .2s; }
a:hover { color: var(--teal-d); }
img { max-width: 100%; display: block; }
code, pre { font-family: var(--mono); }

.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
.section { padding: 96px 0; position: relative; }
.section-tight { padding: 64px 0; }
.section-alt { background: var(--bg-alt); }

.section-paper {
  background: var(--paper);
  background-image:
    linear-gradient(rgba(20,50,48,0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20,50,48,0.035) 1px, transparent 1px);
  background-size: 52px 52px;
  border-top: 1px solid var(--border-warm);
  border-bottom: 1px solid var(--border-warm);
}
.section-paper::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse 90% 60% at 50% 0%, rgba(13,148,136,0.08), transparent 70%);
}

.section-aurora {
  background: #fcfdff; position: relative; overflow: hidden;
  border-top: 1px solid var(--border);
}
.section-aurora::before {
  content: ''; position: absolute; inset: -20%; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 40% 35% at 15% 20%, rgba(13,148,136,0.22), transparent 70%),
    radial-gradient(ellipse 35% 30% at 85% 30%, rgba(6,182,212,0.18), transparent 70%),
    radial-gradient(ellipse 45% 35% at 50% 95%, rgba(16,185,129,0.14), transparent 72%);
  filter: blur(20px);
}
.section-aurora .container { position: relative; z-index: 1; }

.eyebrow {
  display: inline-flex; align-items: center; gap: 10px; font-family: var(--font);
  font-size: .72rem; font-weight: 600; letter-spacing: .18em; text-transform: uppercase;
  color: var(--teal-d); margin-bottom: 18px;
}
.eyebrow::before { content: ''; width: 28px; height: 1px; background: currentColor; }
.eyebrow-wrap { text-align: center; }
.eyebrow-wrap .eyebrow { justify-content: center; }
.section-title {
  font-family: var(--display); font-size: clamp(1.8rem, 4vw, 2.6rem); font-weight: 600;
  text-align: center; margin-bottom: 16px; letter-spacing: -.018em; line-height: 1.12;
}
.section-title em {
  font-style: italic; font-weight: 500;
  background: linear-gradient(120deg, var(--teal-d) 0%, var(--cyan) 60%, var(--green) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.section-sub {
  color: var(--text-2); text-align: center; max-width: 680px; margin: 0 auto 56px;
  font-size: 1.05rem; line-height: 1.8;
}

/* Navigation (glassmorphic) */
#nav {
  position: sticky; top: 0; left: 0; right: 0; z-index: 100;
  backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%);
  background: rgba(255,255,255,0.82);
  border-bottom: 1px solid rgba(15,23,42,0.06);
}
.nav-inner { display: flex; align-items: center; gap: 8px; height: 62px; }
.nav-logo {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--display); font-weight: 600; font-size: 1.12rem; color: var(--text); margin-right: auto;
}
.nav-logo .nav-mark {
  width: 28px; height: 28px; border-radius: 8px; display: block; flex: 0 0 auto;
  box-shadow: 0 4px 12px -3px rgba(194,37,92,.42);
}
.nav-logo .nav-name { white-space: nowrap; }
.nav-logo .nav-name b { font-weight: 700; }
.nav-logo .nav-ver { color: var(--text-3); font-weight: 500; font-family: var(--mono); font-size: .72rem; }
.nav-links { display: flex; gap: 2px; align-items: center; }
.nav-links a { padding: 7px 14px; border-radius: 8px; color: var(--text-2); font-size: .88rem; font-weight: 500; transition: all .2s; }
.nav-links a:hover, .nav-links a.active { color: var(--text); background: rgba(15,23,42,0.05); }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 11px 22px; border-radius: var(--radius-sm);
  font-weight: 600; font-size: .9rem; cursor: pointer; transition: all .2s; border: none; font-family: var(--font);
}
.btn-primary { background: var(--teal); color: #fff; }
.btn-primary:hover { background: var(--teal-d); color: #fff; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(13,148,136,.35); }
.btn-outline { background: rgba(255,255,255,.7); color: var(--text); border: 1px solid var(--border); }
.btn-outline:hover { border-color: var(--teal); background: rgba(13,148,136,.05); }

/* Hero */
#hero {
  position: relative;
  background:
    radial-gradient(ellipse 60% 55% at 85% 10%, rgba(13,148,136,0.14), transparent 70%),
    radial-gradient(ellipse 55% 50% at 12% 90%, rgba(6,182,212,0.16), transparent 72%),
    radial-gradient(ellipse 45% 40% at 50% 100%, rgba(16,185,129,0.10), transparent 75%),
    linear-gradient(180deg, #fbf9f3 0%, #f6f3ea 40%, #eef6f5 100%);
  min-height: 64vh; display: flex; align-items: center; overflow: hidden; isolation: isolate;
}
.hero-dots {
  position: absolute; inset: 0; z-index: 0; opacity: .6;
  background-image: radial-gradient(rgba(20,50,48,0.09) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, black 30%, transparent 90%);
  -webkit-mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, black 30%, transparent 90%);
}
.hero-spectra { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: calc(100% - 48px); max-width: 1200px; height: 40%; z-index: 1; pointer-events: none; }
.spectrum-line { fill: none; stroke-linecap: round; stroke-linejoin: round; }
.wave-dot { fill: currentColor; filter: drop-shadow(0 0 6px currentColor); }
.wave-connector { fill: none; stroke-dasharray: 1.5 4; stroke-linecap: round; mix-blend-mode: multiply; }

.hero-content { position: relative; z-index: 20; text-align: center; padding: 80px 0 64px; isolation: isolate; }
.hero-content > * { position: relative; z-index: 1; }
.hero-logo { display: block; width: min(460px, 80vw); height: auto; margin: 0 auto 30px; filter: drop-shadow(0 10px 22px rgba(194,37,92,.16)); }
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.85); border: 1px solid rgba(13,148,136,0.18);
  border-radius: 100px; padding: 6px 18px; font-size: .78rem; color: var(--text-2); margin-bottom: 28px;
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 24px -10px rgba(13,148,136,0.25); font-weight: 500; letter-spacing: .02em;
}
.hero-badge .dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; box-shadow: 0 0 0 3px rgba(16,185,129,0.18); }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }
.hero-tagline {
  font-family: var(--display); font-size: clamp(1.9rem, 5.2vw, 3.2rem); font-weight: 600;
  color: var(--text); margin-bottom: 14px; letter-spacing: -.025em; line-height: 1.05;
}
.hero-tagline em {
  font-style: italic; font-weight: 500;
  background: linear-gradient(120deg, var(--teal-d) 0%, var(--cyan) 55%, var(--green) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { font-size: clamp(.98rem, 2.2vw, 1.14rem); color: var(--text-2); max-width: 640px; margin: 0 auto 28px; line-height: 1.7; }
.hero-ctas { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; margin-bottom: 12px; position: relative; z-index: 12; }
.btn-pip {
  display: inline-flex; align-items: center; gap: 10px; background: rgba(11,18,32,0.92);
  border: 1px solid rgba(15,23,42,0.9); border-radius: var(--radius-sm); padding: 12px 20px; font-size: .88rem;
  cursor: pointer; transition: all .2s; color: rgba(255,255,255,0.95); font-family: var(--font);
  box-shadow: 0 10px 26px -10px rgba(11,18,32,0.5);
}
.btn-pip:hover { border-color: var(--teal); transform: translateY(-1px); box-shadow: 0 14px 32px -10px rgba(13,148,136,.5); }
.btn-pip code { color: #5eead4; font-size: .88rem; font-weight: 500; }

/* KPI strip */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin: 8px 0; }
.kpi {
  background: rgba(255,255,255,0.78); border: 1px solid var(--border-warm); border-radius: 14px;
  padding: 18px 20px; text-align: center; backdrop-filter: blur(8px);
  box-shadow: var(--shadow); transition: transform .2s, box-shadow .2s;
  position: relative; overflow: hidden;
}
.kpi::after { content: ''; position: absolute; right: -13px; top: -13px; width: 48px; height: 48px; border-radius: 50%; background: var(--accent, var(--teal)); opacity: .07; }
.kpi:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.kpi-v {
  font-family: var(--display); font-size: 1.7rem; font-weight: 700; line-height: 1;
  background: linear-gradient(120deg, var(--teal-d), var(--cyan)); -webkit-background-clip: text; background-clip: text; color: transparent;
}
.kpi-l { font-size: .72rem; color: var(--text-3); text-transform: uppercase; letter-spacing: .08em; margin-top: 8px; font-weight: 600; }

/* Code block */
.codeblock {
  background: var(--bg-code); border-radius: var(--radius); padding: 22px 24px; overflow-x: auto;
  box-shadow: var(--shadow-lg); position: relative;
}
.codeblock pre { margin: 0; font-size: .86rem; line-height: 1.7; color: #e2e8f0; }
.codeblock .c { color: #64748b; }
.codeblock .k { color: #5eead4; }
.codeblock .s { color: #fbbf24; }
.codeblock .topbar { display: flex; gap: 7px; margin-bottom: 14px; }
.codeblock .topbar i { width: 11px; height: 11px; border-radius: 50%; background: #334155; }

/* Catalog cards + filters */
.controls {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 0 0 22px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px 18px; box-shadow: var(--shadow);
}
.controls input, .controls select {
  font: inherit; font-size: .88rem; padding: 9px 12px; border: 1px solid var(--border); border-radius: 9px;
  background: #fff; color: var(--text);
}
.controls input[type=search] { min-width: 260px; flex: 1; }
.controls input:focus, .controls select:focus { outline: none; border-color: var(--teal); box-shadow: 0 0 0 3px rgba(13,148,136,.14); }
.controls .btn-reset { font: inherit; font-size: .85rem; padding: 9px 16px; border: 1px solid var(--border); border-radius: 9px; background: #fff; cursor: pointer; color: var(--text-2); }
.controls .btn-reset:hover { border-color: var(--teal); color: var(--teal-d); }
.controls .count { color: var(--text-3); font-size: .85rem; margin-left: auto; font-variant-numeric: tabular-nums; }

.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 18px; }
.p-card {
  display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow);
  transition: transform .2s, box-shadow .2s, border-color .2s; position: relative; overflow: hidden;
}
.p-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--teal); }
.p-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); border-color: var(--teal-l); }
.p-card h3 { font-family: var(--display); font-size: 1.08rem; font-weight: 600; line-height: 1.34; margin-bottom: 6px; }
.p-card h3 a { color: var(--text); }
.p-card h3 a:hover { color: var(--teal-d); }
.p-card .p-authors { font-size: .82rem; color: var(--text-3); margin-bottom: 10px; }
.p-card .p-venue { font-size: .76rem; color: var(--teal-d); text-transform: uppercase; letter-spacing: .05em; font-weight: 600; margin-bottom: 12px; }
.p-card .p-meta { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 4px 0 14px; font-size: .82rem; color: var(--text-3); }
.p-card .p-meta b { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }
.p-card .p-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; }

/* Badges */
.badge {
  display: inline-flex; align-items: center; gap: 5px; border-radius: 999px; padding: 3px 11px;
  font-size: .72rem; font-weight: 600; letter-spacing: .01em; border: 1px solid transparent;
}
.badge .b-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.badge.neutral { color: var(--text-2); background: var(--bg-alt); border-color: var(--border); }
.badge.warn { color: #b45309; background: rgba(217,119,6,.1); border-color: rgba(217,119,6,.3); }
.badge.info { color: var(--cyan-d); background: rgba(6,182,212,.1); border-color: rgba(6,182,212,.28); }
.badge.ok { color: #047857; background: rgba(16,185,129,.12); border-color: rgba(16,185,129,.3); }
.badge.accent { color: var(--indigo-d); background: rgba(79,70,229,.1); border-color: rgba(79,70,229,.28); }

.hidden { display: none !important; }
.empty { padding: 48px; text-align: center; color: var(--text-3); }

/* Panels */
.panel-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 20px; }
.panel {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); overflow: hidden;
}
.panel.wide { grid-column: 1 / -1; }
.panel > h2 {
  font-family: var(--display); font-size: 1.04rem; font-weight: 600; padding: 16px 20px;
  border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px;
}
.panel > h2 .h2-tag { margin-left: auto; font-size: .68rem; font-family: var(--mono); font-weight: 500; color: var(--text-3); text-transform: uppercase; letter-spacing: .06em; }
.panel-body { padding: 18px 20px; }

table.kv, table.data { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .87rem; }
table.kv th, table.kv td, table.data th, table.data td { text-align: left; padding: 8px 14px; border-top: 1px solid var(--border); vertical-align: top; }
table.kv tr:first-child th, table.kv tr:first-child td { border-top: none; }
table.kv th { color: var(--text-3); font-weight: 600; width: 38%; }
table.kv td { word-break: break-word; overflow-wrap: anywhere; }
table.data thead th { background: var(--bg-alt); color: var(--text-3); font-size: .74rem; text-transform: uppercase; letter-spacing: .05em; border-top: none; }
table.data tbody tr:hover { background: var(--bg-alt); }
table.data td.num, table.data th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.table-scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; background: #fff; }

/* Charts: enlarge on click */
.chart { cursor: zoom-in; position: relative; }
.chart svg { width: 100%; height: auto; display: block; }
.chart::after {
  content: "\\2922"; position: absolute; top: 8px; right: 8px; width: 22px; height: 22px;
  display: grid; place-items: center; border-radius: 6px; background: rgba(255,255,255,.9);
  border: 1px solid var(--border); color: var(--text-3); font-size: .82rem; opacity: 0; transition: opacity .15s;
}
.chart:hover::after, .chart:focus::after { opacity: 1; }
svg text { font-family: var(--font); }
svg text.numt { font-family: var(--mono); font-variant-numeric: tabular-nums; }

.dl-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.dl-btn {
  display: inline-flex; align-items: center; gap: 7px; padding: 9px 16px; border-radius: 9px;
  border: 1px solid var(--border); background: #fff; font-size: .84rem; font-weight: 600; color: var(--text);
}
.dl-btn:hover { border-color: var(--teal); color: var(--teal-d); background: rgba(13,148,136,.04); }
.dl-btn .ext { font-family: var(--mono); font-size: .72rem; color: var(--text-3); }
.dl-note { font-size: .84rem; color: var(--text-3); }

/* Footer */
footer { background: radial-gradient(ellipse 120% 80% at 50% -10%, #10233a 0%, #0b1626 60%, #070e1a 100%); color: rgba(255,255,255,0.7); padding: 56px 0 40px; }
footer .container { display: flex; flex-wrap: wrap; gap: 28px; justify-content: space-between; align-items: flex-start; }
footer a { color: var(--teal-l); }
footer a:hover { color: #fff; }
footer .f-brand { font-family: var(--display); font-weight: 600; font-size: 1.15rem; color: #fff; margin-bottom: 8px; }
footer .f-meta { font-size: .82rem; line-height: 1.8; max-width: 44ch; }
footer .f-links { display: flex; flex-direction: column; gap: 6px; font-size: .85rem; }
footer .f-note { width: 100%; border-top: 1px solid rgba(255,255,255,.08); margin-top: 32px; padding-top: 20px; font-size: .76rem; color: rgba(255,255,255,.45); }

/* Lightbox */
.lightbox { position: fixed; inset: 0; z-index: 999; display: none; place-items: center; background: rgba(8,15,26,.72); backdrop-filter: blur(3px); padding: 5vh 5vw; }
.lightbox.open { display: grid; }
.lightbox .lb-panel { background: #fff; border-radius: 18px; padding: 26px 28px; max-width: 1120px; width: 100%; max-height: 90vh; overflow: auto; box-shadow: var(--shadow-lg); }
.lightbox .lb-panel svg { width: 100%; height: auto; }
.lightbox .lb-close { position: absolute; top: 18px; right: 26px; font-size: 2rem; color: #fff; cursor: pointer; line-height: 1; }
"""

# Papers-specific components: paper hero, pipeline steps, methods narrative, references, replay panel.
_PAPERS_CSS = """
/* Paper hero */
.paper-hero { padding: 56px 0 30px; }
.back { display: inline-flex; align-items: center; gap: 6px; font-size: .85rem; color: var(--text-3); margin-bottom: 18px; }
.back:hover { color: var(--teal-d); }
.paper-badges { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 14px; }
.paper-title { font-family: var(--display); font-size: clamp(1.7rem, 4vw, 2.5rem); font-weight: 600; letter-spacing: -.02em; line-height: 1.12; max-width: 26ch; }
.paper-authors { color: var(--text-2); margin: 14px 0 4px; font-size: 1rem; }
.paper-authors a { color: var(--text-2); }
.paper-affil { color: var(--text-3); font-size: .82rem; }
.paper-venue { color: var(--teal-d); font-size: .82rem; font-weight: 600; margin-top: 10px; text-transform: uppercase; letter-spacing: .05em; }
.paper-abstract { color: var(--text-2); max-width: 74ch; margin: 18px 0 0; font-size: 1.02rem; line-height: 1.8; }
.paper-kw { display: flex; flex-wrap: wrap; gap: 7px; margin: 16px 0 0; }
.kw { display: inline-block; background: rgba(13,148,136,.08); color: var(--teal-d); border-radius: 6px; padding: 2px 10px; font-size: .76rem; }
.status-pill { text-transform: capitalize; }

/* Pipeline steps */
.pipe { display: flex; flex-direction: column; gap: 0; }
.pipe-step { display: flex; gap: 16px; align-items: flex-start; position: relative; padding: 4px 0; }
.pipe-rail { display: flex; flex-direction: column; align-items: center; flex: 0 0 auto; }
.pipe-num {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  font-family: var(--mono); font-size: .82rem; font-weight: 600; color: #fff; flex: 0 0 auto;
  box-shadow: 0 4px 10px -3px rgba(15,23,42,.3);
}
.pipe-line { width: 2px; flex: 1 1 auto; min-height: 18px; background: var(--border); margin: 4px 0; }
.pipe-step:last-child .pipe-line { display: none; }
.pipe-body {
  flex: 1; background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 13px 16px; margin-bottom: 14px; box-shadow: var(--shadow); border-left: 3px solid var(--k-pre);
}
.pipe-body.k-preprocessing { border-left-color: var(--k-pre); }
.pipe-body.k-target { border-left-color: var(--k-target); }
.pipe-body.k-model { border-left-color: var(--k-model); }
.pipe-body.k-split { border-left-color: var(--k-split); }
.pipe-head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.pipe-name { font-family: var(--display); font-weight: 600; font-size: 1rem; }
.pipe-kind { font-size: .66rem; text-transform: uppercase; letter-spacing: .07em; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.pipe-kind.k-preprocessing { color: var(--teal-d); background: rgba(13,148,136,.1); }
.pipe-kind.k-target { color: var(--amber); background: rgba(217,119,6,.1); }
.pipe-kind.k-model { color: var(--indigo-d); background: rgba(79,70,229,.1); }
.pipe-kind.k-split { color: var(--text-2); background: var(--bg-alt); }
.cite-sup a { font-size: .72rem; color: var(--teal-d); font-weight: 600; vertical-align: super; }
.pipe-fqn { font-family: var(--mono); font-size: .74rem; color: var(--text-3); margin-top: 4px; word-break: break-all; }
.pipe-params { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.pipe-params code { font-family: var(--mono); font-size: .74rem; color: var(--text-2); background: var(--bg-alt); border: 1px solid var(--border); border-radius: 6px; padding: 2px 8px; }
.pipe-note { font-size: .78rem; color: var(--text-3); margin-top: 6px; font-style: italic; }
.pipe-desc { font-size: .85rem; color: var(--text-2); margin-top: 7px; line-height: 1.55; }

/* Methods narrative + references */
.methods-narrative p { color: var(--text-2); margin-bottom: 12px; max-width: 80ch; }
.methods-narrative sup a { color: var(--teal-d); font-weight: 600; }
.reflist { list-style: none; counter-reset: ref; display: flex; flex-direction: column; gap: 12px; }
.reflist li { display: flex; gap: 12px; font-size: .9rem; line-height: 1.6; }
.ref-num { flex: 0 0 auto; font-family: var(--mono); font-weight: 600; color: var(--teal-d); min-width: 26px; }
.ref-body { color: var(--text-2); }
.ref-body .ref-title { color: var(--text); font-weight: 500; }
.ref-body a { font-family: var(--mono); font-size: .8rem; }
.ref-principle { display: block; color: var(--text-3); font-size: .84rem; margin-top: 3px; }
.ref-uncited { color: var(--text-3); }

/* Metrics table */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap: 12px; }
.metric-cell { border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; background: linear-gradient(180deg,#fff,var(--bg-alt)); }
.metric-cell .m-v { font-family: var(--display); font-weight: 700; font-size: 1.5rem; color: var(--text); }
.metric-cell .m-n { font-size: .76rem; color: var(--text-3); text-transform: uppercase; letter-spacing: .05em; font-weight: 600; margin-top: 4px; }
.metric-cell .m-p { font-size: .72rem; color: var(--teal-d); font-weight: 600; }

/* Replay panel */
.replay-wrap { border: 1px solid rgba(13,148,136,.25); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); }
.replay-wrap > h2 { background: linear-gradient(120deg, rgba(13,148,136,.08), rgba(6,182,212,.06)); }
.replay-controls { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 16px; }
.replay-status { font-size: .85rem; color: var(--text-3); font-family: var(--mono); }
.replay-status.busy { color: var(--amber); }
.replay-status.done { color: #047857; }
.replay-status.err { color: #b91c1c; }
.replay-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 760px) { .replay-grid { grid-template-columns: 1fr; } }
.replay-chart { border: 1px solid var(--border); border-radius: 12px; background: linear-gradient(180deg,#fff,#fbfdff); padding: 8px 10px; }
.replay-metrics { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0 4px; }
.replay-pill { display: inline-flex; flex-direction: column; border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; background: #fff; min-width: 84px; }
.replay-pill b { font-family: var(--display); font-size: 1.2rem; color: var(--text); }
.replay-pill span { font-size: .68rem; text-transform: uppercase; letter-spacing: .05em; color: var(--text-3); font-weight: 600; }
.replay-note { font-size: .82rem; color: var(--text-3); margin-top: 14px; line-height: 1.6; }
.replay-engine { display:inline-flex; align-items:center; gap:6px; font-size:.72rem; font-family:var(--mono); color:var(--text-3); }
.replay-engine i { width:7px; height:7px; border-radius:50%; background:var(--green); display:inline-block; }
.replay-source { font-size:.78rem; color:var(--text-3); font-family:var(--mono); margin:2px 0 10px; min-height:1em; }

/* Bring-your-own-data */
.byod { margin: 16px 0 4px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg-alt); padding: 2px 16px; }
.byod summary { cursor: pointer; font-family: var(--display); font-weight: 600; font-size: .92rem; padding: 12px 0; display: flex; align-items: center; gap: 8px; }
.byod-body { padding: 4px 0 16px; }
.byod-drop { margin: 12px 0; border: 1.5px dashed var(--border); border-radius: 10px; background: #fff; padding: 18px; text-align: center; transition: border-color .15s, background .15s; }
.byod-drop.over { border-color: var(--teal); background: rgba(13,148,136,.05); }
.byod-drop label { display: block; color: var(--text-2); font-size: .85rem; margin-top: 8px; cursor: pointer; }
.byod-drop input[type=file] { font-size: .82rem; color: var(--text-2); }
.byod-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; }

/* Copy-to-clipboard button (on code blocks) */
.copy-wrap { position: relative; }
.copy-btn {
  position: absolute; top: 10px; right: 12px; z-index: 2; cursor: pointer;
  font-family: var(--mono); font-size: .72rem; font-weight: 600; color: #94a3b8;
  background: rgba(148,163,184,.12); border: 1px solid rgba(148,163,184,.25);
  border-radius: 7px; padding: 4px 10px; transition: all .15s;
}
.copy-btn:hover { color: #5eead4; border-color: rgba(94,234,212,.4); background: rgba(94,234,212,.1); }
.copy-btn.done { color: #34d399; border-color: rgba(52,211,153,.4); }

/* In-page TOC (sticky on the paper page) */
.toc { position: sticky; top: 70px; align-self: start; font-size: .85rem; }
.toc h4 { font-family: var(--display); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: var(--text-3); margin-bottom: 10px; }
.toc a { display: block; padding: 5px 12px; color: var(--text-2); border-left: 2px solid var(--border); transition: all .15s; }
.toc a:hover { color: var(--teal-d); border-left-color: var(--teal); background: rgba(13,148,136,.04); }
.paper-layout { display: grid; grid-template-columns: 1fr; gap: 20px; }
@media (min-width: 1040px) { .paper-layout { grid-template-columns: 200px 1fr; } }
.panel-anchor { scroll-margin-top: 74px; }
.h-anchor { color: var(--text-3); opacity: 0; margin-left: 8px; font-weight: 400; transition: opacity .15s; }
.panel > h2:hover .h-anchor { opacity: 1; }
@media (max-width: 1039px) { .toc { display: none; } }

/* License clarity block */
.license-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 12px; }
.license-cell { border: 1px solid var(--border); border-radius: 12px; padding: 12px 15px; background: var(--bg-alt); }
.license-cell .l-k { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; color: var(--text-3); font-weight: 700; }
.license-cell .l-v { font-family: var(--mono); font-size: .86rem; color: var(--text); margin-top: 4px; word-break: break-word; }

.build-stamp { text-align: center; font-size: .74rem; color: var(--text-3); font-family: var(--mono); margin-top: 8px; }

@media (max-width: 640px) {
  .nav-links a:not(.active) { display: none; }
}

@media print {
  #nav, footer, .replay-controls, .copy-btn, .toc, .hero-dots, .hero-spectra, #lb, .h-anchor { display: none !important; }
  .section, .section-paper, .section-aurora, #hero { padding: 12px 0 !important; background: #fff !important; }
  .section-paper::before, .section-aurora::before { display: none !important; }
  .codeblock { background: #f6f8fa !important; box-shadow: none !important; border: 1px solid #d0d7de; }
  .codeblock pre, .codeblock .k, .codeblock .c, .codeblock .s { color: #111 !important; }
  .panel, .viz-card, .pipe-body, .metric-cell { box-shadow: none !important; break-inside: avoid; }
  details { open: true; }
  a { color: #111 !important; text-decoration: underline; }
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""

CSS = _BASE_CSS + _PAPERS_CSS


SITE_URL = "https://papers.nirs4all.org"


def page(*, title: str, rel: str, body: str, scripts: str = "", description: str = "", canonical: str = "", head_extra: str = "") -> str:
    """The base HTML shell. ``rel`` is the path prefix to site root ("" or "../") for ``file://`` use.

    ``canonical`` is the page's path under the site root (e.g. ``"catalog.html"`` or
    ``"paper/<slug>.html"``); it sets the canonical / ``og:url``. ``head_extra`` injects per-page
    ``<head>`` markup (scholarly ``citation_*`` meta + JSON-LD).
    """
    desc = description or "Reproduction documents for nirs4all papers — methods, bibliography, and a live in-browser pipeline replay."
    url = f"{SITE_URL}/{canonical.lstrip('/')}" if canonical else f"{SITE_URL}/"
    from .escape import esc

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0d9488">
<link rel="canonical" href="{esc(url)}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="{SITE_URL}/sitemap.xml">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="icon" type="image/x-icon" href="{rel}brand/favicon.ico">
<link rel="icon" type="image/svg+xml" href="{rel}brand/icon.svg">
<link rel="apple-touch-icon" href="{rel}brand/icon-180.png">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE_URL}/brand/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/brand/og.png">
{head_extra}
{FONTS_LINK}
<style>{CSS}</style>
</head>
<body>
{body}
{scripts}
{LIGHTBOX}
{COPY_JS}
{GOATCOUNTER}
</body>
</html>
"""


GOATCOUNTER = """<script data-goatcounter="https://nirs4all.goatcounter.com/count" data-goatcounter-settings='{"path": "/papers"}' async src="//gc.zgo.at/count.js"></script>"""

# Copy-to-clipboard: any [data-copy="<id>"] button copies that element's text (with a "copied!" flash).
COPY_JS = """<script>(function(){document.addEventListener('click',function(e){var b=e.target.closest('.copy-btn');if(!b)return;
var t=document.getElementById(b.getAttribute('data-copy'));if(!t)return;var txt=t.innerText||t.textContent;
function ok(){var o=b.textContent;b.textContent='copied!';b.classList.add('done');setTimeout(function(){b.textContent=o;b.classList.remove('done');},1200);}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(ok,function(){});}
else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');ok();}catch(_){}document.body.removeChild(ta);}});})();</script>"""

LIGHTBOX = """<div id="lb" class="lightbox" aria-hidden="true"><span class="lb-close" aria-label="close">×</span><div class="lb-panel"></div></div>
<script>(function(){var lb=document.getElementById('lb'),p=lb.querySelector('.lb-panel');
function close(){lb.classList.remove('open');p.innerHTML='';}
document.addEventListener('click',function(e){var c=e.target.closest('.chart');
  if(c){var s=c.querySelector('svg');if(s){p.innerHTML=s.outerHTML;lb.classList.add('open');}return;}
  if(e.target===lb||e.target.closest('.lb-close'))close();});
document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});})();</script>"""
