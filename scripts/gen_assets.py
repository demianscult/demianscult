"""Noir / cyber asset generator for the demianscult profile.

Palette: deep black, graphite, cold silver, crimson. All art is original and
self-contained (no external images or fonts) so it renders inside GitHub's
<img> sandbox.
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape as e

ROOT = Path(__file__).resolve().parent.parent / "assets"
for d in ("", "headers", "cards"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)

import base64
FONTS = Path(__file__).resolve().parent / "fonts"


def _face(family, file, weight):
    b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}")


FACES = "".join([
    _face("JBM", "JetBrainsMono-Regular.woff", 400),
    _face("JBM", "JetBrainsMono-Bold.woff", 700),
    _face("Gloock", "Gloock-Regular.woff", 400),
])
MONO = ("JBM,'JetBrains Mono','SFMono-Regular',Menlo,Consolas,"
        "'Liberation Mono',monospace")
SERIF = "Gloock,'Playfair Display',Didot,Georgia,serif"
BG = "#07070a"
PANEL = "#0c0b0f"
LINE = "#26222b"
SILVER = "#d9d6de"
MUTED = "#8c8794"
DIM = "#4a4552"
RED = "#e11d2e"
RED_SOFT = "#ff4d5e"
RED_DEEP = "#7a0d17"

STYLE = f"""<style>
{FACES}
text{{font-family:{MONO}}}
.serif{{font-family:{SERIF};font-weight:400}}
.blink{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>"""


def write(rel, svg):
    (ROOT / rel).write_text(svg, encoding="utf-8")
    print("wrote", rel)


# --------------------------------------------------------------------------
# skyline: gothic spires + antenna towers, procedurally generated
# --------------------------------------------------------------------------
def skyline(rng, x0, x1, base, hmin, hmax, fill, windows=None, spires=True):
    out, x = [], x0
    while x < x1:
        w = rng.randint(26, 70)
        h = rng.randint(hmin, hmax)
        top = base - h
        out.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h + 2}" fill="{fill}"/>')
        r = rng.random()
        if spires and r < 0.22:      # gothic spire
            cx = x + w / 2
            sh = rng.randint(40, 95)
            out.append(f'<path d="M{x + 4} {top}L{cx} {top - sh}L{x + w - 4} {top}Z" fill="{fill}"/>')
            out.append(f'<path d="M{cx - 6} {top - 8}L{cx} {top - sh - 14}L{cx + 6} {top - 8}Z" fill="{fill}"/>')
        elif r < 0.42:               # antenna
            ax = x + rng.randint(6, max(7, w - 6))
            ah = rng.randint(18, 50)
            out.append(f'<rect x="{ax}" y="{top - ah}" width="2" height="{ah}" fill="{fill}"/>')
            out.append(f'<circle cx="{ax + 1}" cy="{top - ah}" r="2" fill="{RED}">'
                       f'<animate attributeName="opacity" values="1;0.15;1" dur="{rng.uniform(1.6, 3.2):.1f}s" repeatCount="indefinite"/></circle>')
        elif r < 0.55:               # stepped roof
            out.append(f'<rect x="{x + 6}" y="{top - 14}" width="{w - 12}" height="16" fill="{fill}"/>')
        if windows:
            for wy in range(top + 10, base - 8, 13):
                for wx in range(x + 6, x + w - 6, 9):
                    if rng.random() < windows:
                        c = RED if rng.random() < 0.25 else "#c9c4d0"
                        o = rng.uniform(0.25, 0.75)
                        out.append(f'<rect x="{wx}" y="{wy}" width="3" height="5" fill="{c}" opacity="{o:.2f}"/>')
        x += w + rng.randint(0, 6)
    return "\n".join(out)


def rain(rng, w, h, n, dur):
    lines = []
    for _ in range(n):
        x = rng.uniform(0, w + 120)
        y = rng.uniform(-h, h)
        l = rng.uniform(10, 26)
        o = rng.uniform(0.08, 0.28)
        lines.append(f'<path d="M{x:.0f} {y:.0f}l-5 {l:.0f}" stroke="#cfd3dc" stroke-opacity="{o:.2f}" stroke-width="1"/>')
    body = "\n".join(lines)
    return (f'<g><animateTransform attributeName="transform" type="translate" '
            f'from="0 0" to="-40 {h}" dur="{dur}s" repeatCount="indefinite"/>'
            f'{body}<g transform="translate(40 {-h})">{body}</g></g>')



# --------------------------------------------------------------------------
# typed title: a boot command, then the title "types" letter by letter.
# CSS-only, so renderers without animation simply show the finished frame.
# --------------------------------------------------------------------------
def _advances(text, size, spacing):
    from fontTools.ttLib import TTFont
    f = TTFont(FONTS / "Gloock-Regular.woff")
    upm = f["head"].unitsPerEm
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return [hmtx[cmap[ord(ch)]][0] * size / upm + spacing for ch in text]


def _steps(name, offsets, total, t0, step, prop):
    """keyframes that jump to each offset in turn (step-end)."""
    n = len(offsets)
    dur = step * n
    frames = [f"0%{{{prop(offsets[0] - total)}}}"]
    for i, off in enumerate(offsets[1:], start=1):
        frames.append(f"{i / n * 100:.3f}%{{{prop(off - total)}}}")
    frames.append(f"100%{{{prop(0)}}}")
    css = f"@keyframes {name}{{{''.join(frames)}}}"
    anim = f"animation:{name} {dur:.2f}s step-end {t0:.2f}s both"
    return css, anim


def typed_title(title, tx, ty, fs):
    ls = 8
    adv = _advances(title, fs, ls)
    total = sum(adv) - ls
    x0 = tx - total / 2
    bounds = [0.0]
    for a in adv:
        bounds.append(bounds[-1] + a)
    bounds[-1] = total + 2

    cmd = "> ./evel_system --boot"
    cfs, cls_ = 13, 6
    cw = cfs * 0.6 + cls_
    ctot = cw * len(cmd)
    cx0 = tx - ctot / 2
    cbounds = [cw * i for i in range(len(cmd) + 1)]

    tr = lambda v: f"transform:translateX({v:.1f}px)"
    k_cmd, a_cmd = _steps("cmd", cbounds, ctot, 0.3, 0.05, tr)
    t_start = 0.3 + 0.05 * len(cmd) + 0.35
    k_ttl, a_ttl = _steps("ttl", bounds, total + 2, t_start, 0.13, tr)
    t_end = t_start + 0.13 * len(bounds)
    css = f"""<style>
{k_cmd}{k_ttl}
.rv-cmd{{{a_cmd}}}
.rv-ttl{{{a_ttl}}}
.caret{{{a_ttl},caretblink 1s steps(1) {t_end:.2f}s infinite}}
@keyframes caretblink{{50%{{opacity:0}}}}
.late{{animation:fadein .8s ease {t_end + 0.1:.2f}s both}}
@keyframes fadein{{from{{opacity:0}}to{{opacity:1}}}}
</style>"""
    layer = lambda dx, fill, extra="": (
        f'<text x="{x0 + dx:.1f}" y="{ty}" font-size="{fs}" class="serif" fill="{fill}" letter-spacing="{ls}" {extra}>{title}</text>')
    return f"""{css}
  <defs>
    <clipPath id="rvc"><rect class="rv-cmd" x="{cx0 - 4:.1f}" y="{ty - 135}" width="{ctot + 4:.1f}" height="40"/></clipPath>
    <clipPath id="rvt"><rect class="rv-ttl" x="{x0 - 30:.1f}" y="{ty - 100}" width="{total + 32:.1f}" height="130"/></clipPath>
  </defs>
  <g clip-path="url(#rvc)">
    <text x="{cx0:.1f}" y="{ty - 108}" font-size="{cfs}" fill="{MUTED}" letter-spacing="{cls_}"><tspan fill="{RED}">&gt;</tspan> ./evel_system --boot</text>
  </g>
  <rect class="late" x="300" y="{ty - 92}" width="600" height="1" fill="{RED}" opacity="0.5"/>
  <g clip-path="url(#rvt)">
    {layer(0, RED, 'filter="url(#glow)" opacity="0.55"')}
    {layer(-4, "#46e0ff", 'opacity="0.35" clip-path="url(#slice1)"')}
    {layer(5, RED_SOFT, 'opacity="0.8" clip-path="url(#slice2)"')}
    {layer(0, SILVER)}
  </g>
  <rect class="caret" x="{x0 + total + 10:.1f}" y="{ty - 74}" width="12" height="78" fill="{RED}" opacity="0.9"/>
  <g class="late">
    <rect x="300" y="{ty + 26}" width="600" height="1" fill="{RED}" opacity="0.5"/>
    <text x="{tx}" y="{ty + 58}" text-anchor="middle" font-size="17" fill="{SILVER}" letter-spacing="3">security labs <tspan fill="{RED}">/</tspan> automation <tspan fill="{RED}">/</tspan> linux <tspan fill="{RED}">/</tspan> experiments</text>
  </g>"""

# --------------------------------------------------------------------------
# banner
# --------------------------------------------------------------------------
def banner():
    W, H = 1200, 440
    rng = random.Random(1997)
    far = skyline(rng, -20, W + 20, 380, 60, 170, "#121117", windows=0.05)
    mid = skyline(rng, -30, W + 30, 400, 40, 120, "#0b0a0e", windows=0.09)
    near = skyline(rng, -40, W + 40, 440, 20, 70, "#050507", spires=False)
    rain_fx = rain(random.Random(7), W, H, 140, 1.1)

    title = "evel system"
    ty, tx, fs = 222, 600, 104

    title_block = typed_title(title, tx, ty, fs)

    def hud_corner(x, y, sx, sy):
        return f'<path d="M{x} {y + 22 * sy}V{y}H{x + 22 * sx}" fill="none" stroke="{RED}" stroke-width="2"/>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Evel System — security labs · automation · linux · experiments</title>
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#050506"/>
    <stop offset="0.55" stop-color="#140a0e"/>
    <stop offset="1" stop-color="#2a0910"/>
  </linearGradient>
  <radialGradient id="moon" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{RED_SOFT}" stop-opacity="0.55"/>
    <stop offset="0.35" stop-color="{RED}" stop-opacity="0.18"/>
    <stop offset="1" stop-color="{RED}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="fog" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{RED}" stop-opacity="0"/>
    <stop offset="1" stop-color="{RED}" stop-opacity="0.16"/>
  </linearGradient>
  <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{RED}" stop-opacity="0"/>
    <stop offset="0.5" stop-color="{RED}" stop-opacity="0.10"/>
    <stop offset="1" stop-color="{RED}" stop-opacity="0"/>
  </linearGradient>
  <pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" fill-opacity="0.28"/></pattern>
  <filter id="glow" x="-20%" y="-50%" width="140%" height="200%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <clipPath id="slice1"><rect x="0" y="{ty - 62}" width="{W}" height="18">
    <animate attributeName="y" values="{ty - 62};{ty - 30};{ty - 50};{ty - 62}" dur="5s" repeatCount="indefinite"/></rect></clipPath>
  <clipPath id="slice2"><rect x="0" y="{ty - 22}" width="{W}" height="10">
    <animate attributeName="y" values="{ty - 22};{ty - 70};{ty - 10};{ty - 22}" dur="3.7s" repeatCount="indefinite"/></rect></clipPath>
  {STYLE}
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  <circle cx="900" cy="150" r="230" fill="url(#moon)"/>
  <circle cx="900" cy="150" r="58" fill="none" stroke="{RED}" stroke-opacity="0.5"/>
  <circle cx="900" cy="150" r="76" fill="none" stroke="{RED}" stroke-opacity="0.18" stroke-dasharray="2 7"/>
  <g opacity="0.95">{far}</g>
  <rect y="250" width="{W}" height="190" fill="url(#fog)"/>
  <g>{mid}</g>
  {rain_fx}
  <g>{near}</g>

{title_block}

  <!-- HUD -->
  {hud_corner(22, 22, 1, 1)}{hud_corner(W - 22, 22, -1, 1)}{hud_corner(22, H - 22, 1, -1)}{hud_corner(W - 22, H - 22, -1, -1)}
  <text x="44" y="42" font-size="11" fill="{MUTED}" letter-spacing="2">REC <tspan fill="{RED}" class="blink">●</tspan></text>
  <text x="{W - 44}" y="42" text-anchor="end" font-size="11" fill="{MUTED}" letter-spacing="2">NODE: LAB-01 · LINK SECURE</text>
  <text x="44" y="{H - 34}" font-size="11" fill="{MUTED}" letter-spacing="2">&gt; whoami <tspan fill="{SILVER}">demianscult</tspan><tspan fill="{RED}" class="blink"> _</tspan></text>
  <text x="{W - 44}" y="{H - 34}" text-anchor="end" font-size="11" fill="{MUTED}" letter-spacing="2">CS STUDENT · BR</text>

  <!-- moving scan sweep -->
  <rect x="0" y="-80" width="{W}" height="80" fill="url(#sweep)">
    <animate attributeName="y" values="-80;{H};-80" dur="9s" repeatCount="indefinite"/>
  </rect>
  <rect width="{W}" height="{H}" fill="url(#scan)"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{LINE}"/>
</svg>
'''
    write("banner.svg", svg)


# --------------------------------------------------------------------------
# section headers
# --------------------------------------------------------------------------
HEADERS = [
    ("about", "01", "ABOUT", "who is behind the terminal"),
    ("interests", "02", "AREAS OF INTEREST", "four fronts"),
    ("stack", "03", "TECH STACK", "tools in the kit"),
    ("linux", "04", "LINUX RANKING", "evaluating distros · for now"),
    ("projects", "05", "FEATURED PROJECTS", "selected files"),
    ("cyberlab", "06", "CYBERSECURITY LAB", "rooms · ctfs · write-ups"),
    ("now", "07", "CURRENTLY EXPLORING", "live log"),
    ("analytics", "08", "GITHUB ANALYTICS", "signal"),
    ("connect", "09", "CONNECT", "open channel"),
]


def header(slug, idx, title, sub):
    W, H = 1200, 76
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{e(title.title())}">
{STYLE}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" fill="{PANEL}" stroke="{LINE}"/>
<rect x="0" y="16" width="5" height="44" fill="{RED}"/>
<text x="24" y="28" font-size="12" fill="{RED}" letter-spacing="4">// {idx}</text>
<text x="24" y="60" font-size="26" class="serif" fill="{SILVER}" letter-spacing="3">{e(title)}</text>
<path d="M{40 + len(title) * 19} 52H{W - 200}" stroke="{LINE}"/>
<path d="M{W - 200} 52l10 -10H{W - 20}" fill="none" stroke="{RED_DEEP}"/>
<text x="{W - 20}" y="26" text-anchor="end" font-size="11" fill="{DIM}" letter-spacing="2">{e(sub)}</text>
</svg>
'''
    write(f"headers/{slug}.svg", svg)


# --------------------------------------------------------------------------
# areas of interest — 4 dossier panels
# --------------------------------------------------------------------------
PILLARS = [
    ("01", "CYBERSECURITY", ["labs & CTFs · write-ups", "web & network security", "blue team · linux/windows sec", "OSINT & forensics"]),
    ("02", "AUTOMATION & SCRIPTING", ["scripts for repetitive work", "personal utilities", "integrations between tools", "small apps with real use"]),
    ("03", "LINUX & HOMELAB", ["arch · mint · bazzite · parrot", "podman & docker", "virtualization", "networks & infrastructure"]),
    ("04", "TECHNOLOGY & EXPERIMENTS", ["local LLMs with ollama", "agents & RAG", "prototypes and tools", "whatever comes next"]),
]


def glyph(i, cx, cy):
    s = RED
    if i == 0:   # shield / crosshair
        return (f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{s}"/>'
                f'<circle cx="{cx}" cy="{cy}" r="4" fill="{s}"/>'
                f'<path d="M{cx - 24} {cy}h12M{cx + 12} {cy}h12M{cx} {cy - 24}v12M{cx} {cy + 12}v12" stroke="{s}"/>')
    if i == 1:   # gears-ish loop arrows
        return (f'<path d="M{cx - 16} {cy}a16 16 0 0 1 28 -10" fill="none" stroke="{s}"/>'
                f'<path d="M{cx + 12} {cy - 18}l0 8l-8 0" fill="none" stroke="{s}"/>'
                f'<path d="M{cx + 16} {cy}a16 16 0 0 1 -28 10" fill="none" stroke="{s}"/>'
                f'<path d="M{cx - 12} {cy + 18}l0 -8l8 0" fill="none" stroke="{s}"/>')
    if i == 2:   # terminal prompt
        return (f'<rect x="{cx - 22}" y="{cy - 16}" width="44" height="32" rx="3" fill="none" stroke="{s}"/>'
                f'<path d="M{cx - 14} {cy - 5}l7 6l-7 6" fill="none" stroke="{s}"/>'
                f'<path d="M{cx - 2} {cy + 7}h12" stroke="{s}"/>')
    return (f'<path d="M{cx} {cy - 20}L{cx + 18} {cy + 12}H{cx - 18}Z" fill="none" stroke="{s}"/>'
            f'<circle cx="{cx}" cy="{cy + 2}" r="5" fill="none" stroke="{s}"/>')


def interests():
    W, H = 1200, 330
    pw, ph, gap = 591, 157, 18
    parts = []
    for i, (idx, title, items) in enumerate(PILLARS):
        x = (i % 2) * (pw + gap)
        y = (i // 2) * (ph + 16)
        lines = "".join(
            f'<text x="{x + 104}" y="{y + 84 + k * 19}" font-size="13" fill="{MUTED}"><tspan fill="{RED}">›</tspan> {e(t)}</text>'
            for k, t in enumerate(items))
        parts.append(f'''
<rect x="{x + 0.5}" y="{y + 0.5}" width="{pw - 1}" height="{ph - 1}" rx="8" fill="{PANEL}" stroke="{LINE}"/>
<path d="M{x + pw - 40} {y + 14}H{x + pw - 14}V{y + 40}" fill="none" stroke="{RED}" stroke-opacity="0.8" stroke-width="1.5"/>
{glyph(i, x + 52, y + 80)}
<text x="{x + 104}" y="{y + 28}" font-size="11" fill="{RED}" letter-spacing="3">{idx}</text>
<text x="{x + 104}" y="{y + 58}" font-size="21" class="serif" fill="{SILVER}" letter-spacing="1.5">{e(title)}</text>
{lines}''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Cybersecurity, Automation and Scripting, Linux and Homelab, Technology and Experiments">
{STYLE}{"".join(parts)}
</svg>
'''
    write("interests.svg", svg)


# --------------------------------------------------------------------------
# project cards — "case file" style
# --------------------------------------------------------------------------
CARDS = [
    ("intelligent-tool-agent", "FILE 01", "AUTOMATION · AI SAFETY",
     ["Local ReAct agent that picks and runs tools", "from natural-language commands."],
     ["tool calling without eval(): AST math,", "sandboxed file access, loop guard"],
     "python · ollama · pydantic · streamlit · pytest"),
    ("tryhackme-grand-larceny-auto", "FILE 02", "CYBERSECURITY · WRITE-UP",
     ["Write-ups for TryHackMe's Grand Larceny", "Auto I & II challenges."],
     ["reversed a .NET game build; scripted an API", "flow to exploit an unsigned claim field"],
     "python · monodis/CIL · http apis · linux"),
    ("rag-knowledge-assistant", "FILE 03", "EXPERIMENTS · LOCAL AI",
     ["Private RAG assistant that answers from", "your own PDF and text files."],
     ["cited sources, SHA-256 dedup and a", "relevance guardrail against hallucination"],
     "python · fastapi · chromadb · ollama"),
    ("llm-evaluation-lab", "FILE 04", "EXPERIMENTS · BENCHMARKING",
     ["Benchmark lab comparing small local LLMs", "across 7 task categories."],
     ["latency, tokens/s, JSON compliance", "and safe-refusal rate"],
     "python · ollama · pandas · scikit-learn"),
]


def card(name, fid, tag, desc, goal, stack):
    W, H = 600, 260
    d = "".join(f'<text x="30" y="{122 + i * 20}" font-size="14" fill="{SILVER}" opacity="0.88">{e(l)}</text>' for i, l in enumerate(desc))
    g = (f'<text x="30" y="{178}" font-size="12" fill="{RED}" letter-spacing="1">OBJ ›</text>'
         + "".join(f'<text x="86" y="{178 + i * 18}" font-size="12.5" fill="{MUTED}">{e(l)}</text>' for i, l in enumerate(goal)))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{e(name)}: {e(' '.join(desc))}">
{STYLE}
<defs><linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="{RED}" stop-opacity="0.22"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient></defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="{PANEL}" stroke="{LINE}"/>
<rect x="1" y="1" width="{W - 2}" height="46" rx="7" fill="url(#hl)"/>
<path d="M1 47H{W - 1}" stroke="{LINE}"/>
<text x="30" y="30" font-size="11" fill="{RED}" letter-spacing="3">{fid}</text>
<text x="110" y="30" font-size="11" fill="{MUTED}" letter-spacing="2">{e(tag)}</text>
<g transform="translate({W - 120} 15)">
  <rect width="92" height="20" fill="none" stroke="{RED}" stroke-opacity="0.75" transform="rotate(-4 46 10)"/>
  <text x="46" y="14" text-anchor="middle" font-size="10" font-weight="700" fill="{RED}" letter-spacing="3" transform="rotate(-4 46 10)">OPEN ↗</text>
</g>
<text x="30" y="88" font-size="21" font-weight="700" fill="{SILVER}">{e(name)}</text>
{d}
{g}
<path d="M30 {H - 44}H{W - 30}" stroke="{LINE}" stroke-dasharray="3 4"/>
<text x="30" y="{H - 18}" font-size="12" fill="{RED_SOFT}" opacity="0.9">{e(stack)}</text>
</svg>
'''
    write(f"cards/{name}.svg", svg)


# --------------------------------------------------------------------------
# now.log — terminal that types itself, line by line
# --------------------------------------------------------------------------
NOW = [
    ("lab", "web security on PortSwigger · TryHackMe rooms + write-ups"),
    ("homelab", "containers with Podman and Docker"),
    ("systems", "Arch · Mint · Bazzite · Parrot OS"),
    ("ai", "local LLMs with Ollama: agents, RAG and evaluation"),
]


def now():
    W, H = 1200, 70 + 30 * (len(NOW) + 2)
    rows = [f'<text x="28" y="78" font-size="15" fill="{MUTED}"><tspan fill="{RED}">demianscult@lab</tspan>:~$ <tspan fill="{SILVER}">cat ~/now.log</tspan></text>']
    clips = []
    for i, (tag, txt) in enumerate(NOW):
        y = 110 + i * 30
        begin = 0.6 + i * 0.9
        rows.append(f'<text class="type" style="animation-delay:{begin:.1f}s" x="28" y="{y}" font-size="15" fill="{SILVER}">'
                    f'<tspan fill="{RED}">[{e(tag)}]</tspan><tspan x="160">{e(txt)}</tspan></text>')
    yc = 110 + len(NOW) * 30
    rows.append(f'<text x="28" y="{yc}" font-size="15" fill="{MUTED}">$<tspan fill="{RED}" class="blink"> █</tspan></text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Currently exploring: {e('; '.join(t for _, t in NOW))}">
{STYLE}
<style>.type{{animation:type .9s steps(40) both}}@keyframes type{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 0 0 0)}}}}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{PANEL}" stroke="{LINE}"/>
<path d="M1 40H{W - 1}" stroke="{LINE}"/>
<circle cx="26" cy="20" r="5" fill="{RED}"/><circle cx="44" cy="20" r="5" fill="none" stroke="{DIM}"/><circle cx="62" cy="20" r="5" fill="none" stroke="{DIM}"/>
<text x="{W / 2}" y="25" text-anchor="middle" font-size="12" fill="{DIM}" letter-spacing="2">~/now.log — tty1</text>
{"".join(rows)}
</svg>
'''
    write("now.svg", svg)


# --------------------------------------------------------------------------
# footer — skyline strip
# --------------------------------------------------------------------------
def footer():
    W, H = 1200, 120
    rng = random.Random(404)
    city = skyline(rng, -20, W + 20, 120, 15, 70, "#0b0a0e", windows=0.06)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="end of transmission">
{STYLE}
<defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset="1" stop-color="{RED}" stop-opacity="0.22"/></linearGradient>
<clipPath id="k"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#k)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect width="{W}" height="{H}" fill="url(#f)"/>
{city}
<text x="{W / 2}" y="30" text-anchor="middle" font-size="12" fill="{MUTED}" letter-spacing="6">// END OF TRANSMISSION <tspan fill="{RED}" class="blink">●</tspan></text>
</g>
</svg>
'''
    write("footer.svg", svg)


# --------------------------------------------------------------------------
# tech stack — "periodic table" tiles, no third-party logos
# --------------------------------------------------------------------------
STACK = [
    ("languages", [("Py", "Python"), ("Sh", "Bash"), ("Sq", "SQL"), ("Js", "JavaScript"), ("Ts", "TypeScript")]),
    ("build & automation", [("St", "Streamlit"), ("Fa", "FastAPI"), ("Pd", "Pydantic"), ("Pt", "pytest"), ("Re", "React"), ("Nd", "Node.js")]),
    ("data & ai", [("Ol", "Ollama"), ("Ch", "ChromaDB"), ("Pa", "pandas"), ("Pg", "PostgreSQL"), ("Mg", "MongoDB"), ("Rd", "Redis")]),
    ("systems & infra", [("Lx", "Linux"), ("Gt", "Git"), ("Gh", "GitHub"), ("Dk", "Docker"), ("Pm", "Podman")]),
    ("security · offense", [("Nm", "Nmap"), ("Bp", "Burp Suite"), ("Ms", "Metasploit"), ("Sm", "sqlmap"), ("Gb", "Gobuster"), ("Hy", "Hydra")]),
    ("security · analysis", [("Ws", "Wireshark"), ("Td", "tcpdump"), ("Gd", "Ghidra"), ("Jn", "John"), ("Hc", "Hashcat"), ("Au", "Autopsy")]),
]


def stack():
    W = 1200
    tw, th, gap, rowgap, x0 = 140, 100, 12, 18, 262
    pad = 28
    H = len(STACK) * (th + rowgap) - rowgap + 2 * pad
    parts, n = [], 0
    for r, (cat, items) in enumerate(STACK):
        y = r * (th + rowgap) + pad
        parts.append(f'<text x="{pad}" y="{y + 34}" font-size="11" fill="{RED}" letter-spacing="3">// {r + 1:02d}</text>'
                     f'<text x="{pad}" y="{y + 60}" font-size="20" class="serif" fill="{SILVER}">{e(cat)}</text>'
                     f'<path d="M{pad} {y + 74}H{x0 - 30}" stroke="{LINE}"/>')
        for i, (sym, name) in enumerate(items):
            n += 1
            x = x0 + i * (tw + gap)
            parts.append(f'''<g>
<rect x="{x + 0.5}" y="{y + 0.5}" width="{tw - 1}" height="{th - 1}" rx="6" fill="{PANEL}" stroke="{LINE}"/>
<path d="M{x + tw - 22} {y + 8}H{x + tw - 8}V{y + 22}" fill="none" stroke="{RED}" stroke-opacity="0.8"/>
<text x="{x + 12}" y="{y + 20}" font-size="10" fill="{DIM}">{n:02d}</text>
<text x="{x + 14}" y="{y + 64}" font-size="38" class="serif" fill="{SILVER}">{sym}</text>
<text x="{x + 14}" y="{y + 86}" font-size="11.5" fill="{MUTED}">{e(name)}</text>
</g>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Tech stack: {e('; '.join(c + ': ' + ', '.join(nm for _, nm in it) for c, it in STACK))}">
{STYLE}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>
{"".join(parts)}
</svg>
'''
    write("stack.svg", svg)


# --------------------------------------------------------------------------
# linux ranking — personal distro ranking, edit freely
# --------------------------------------------------------------------------
DISTROS = [
    ("01", "Arch Linux", "current favorite", "rolling release · diy"),
    ("02", "Parrot OS", "on this laptop", "debian-based · security"),
    ("03", "Bazzite", "used", "fedora atomic · gaming"),
    ("04", "Linux Mint", "used", "ubuntu-based · desktop"),
]
RADAR = [
    ("Kali Linux", "know a bit"),
    ("Ubuntu", "next to test"),
]


def distros():
    W = 1200
    rh, top, pad = 70, 58, 28
    IW = W - 2 * pad
    H = top + len(DISTROS) * rh + 96 + 2 * pad
    rows = []
    for i, (rank, name, tag, note) in enumerate(DISTROS):
        y = top + i * rh
        lead = i == 0
        rows.append(f'''<g>
<rect x="0.5" y="{y + 0.5}" width="{IW - 1}" height="{rh - 11}" rx="6" fill="{'#140a0e' if lead else PANEL}" stroke="{RED if lead else LINE}" stroke-opacity="{0.8 if lead else 1}"/>
<text x="26" y="{y + 42}" font-size="34" class="serif" fill="{RED if lead else DIM}">{rank}</text>
<path d="M92 {y + 14}V{y + rh - 25}" stroke="{LINE}"/>
<text x="116" y="{y + 40}" font-size="26" class="serif" fill="{SILVER}">{e(name)}</text>
<g transform="translate(430 {y + 18})"><rect width="{len(tag) * 8.4 + 22:.0f}" height="24" rx="3" fill="none" stroke="{RED}" stroke-opacity="{0.9 if lead else 0.5}"/>
<text x="11" y="16.5" font-size="11.5" fill="{RED_SOFT if lead else MUTED}" letter-spacing="1">{e(tag.upper())}</text></g>
<text x="{IW - 28}" y="{y + 36}" text-anchor="end" font-size="13" fill="{MUTED}">{e(note)}</text>
</g>''')
    ry = top + len(DISTROS) * rh + 18
    radar = "".join(
        f'<text x="{116 + i * 330}" y="{ry + 40}" font-size="20" class="serif" fill="{SILVER}">{e(n)}'
        f'<tspan font-family="JBM,monospace" font-size="11.5" fill="{MUTED}" dx="14" letter-spacing="1">{e(t.upper())}</tspan></text>'
        for i, (n, t) in enumerate(RADAR))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Linux ranking: {e(', '.join(f'{r}. {n}' for r, n, _, _ in DISTROS))}. Also: {e(', '.join(f'{n} ({t})' for n, t in RADAR))}">
{STYLE}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>
<g transform="translate({pad} {pad})">
<text x="0" y="22" font-size="14" fill="{MUTED}"><tspan fill="{RED}">evel@lab</tspan>:~$ <tspan fill="{SILVER}">rank --distros --personal</tspan></text>
<text x="{IW}" y="22" text-anchor="end" font-size="11" fill="{DIM}" letter-spacing="2">SUBJECT TO CHANGE AS I TEST MORE</text>
{"".join(rows)}
<path d="M0 {ry}H{IW}" stroke="{LINE}" stroke-dasharray="3 5"/>
<text x="26" y="{ry + 38}" font-size="11" fill="{RED}" letter-spacing="3">RADAR</text>
{radar}
</g>
</svg>
'''
    write("linux.svg", svg)


# --------------------------------------------------------------------------
# training grounds — platforms and communities
# --------------------------------------------------------------------------
PLATFORMS = [
    ("TryHackMe", "labs · rooms · ctfs"),
    ("PortSwigger", "web security academy"),
    ("HackerOne", "bug bounty · hacker101"),
    ("OffSec", "offensive security training"),
    ("EC-Council", "courses · certifications"),
    ("WiCyS", "women in cybersecurity"),
]


def platforms():
    W, cols, pad, gap = 1200, 3, 28, 14
    cw = (W - 2 * pad - (cols - 1) * gap) / cols
    ch = 92
    rows = (len(PLATFORMS) + cols - 1) // cols
    top = 46
    H = top + rows * (ch + gap) - gap + 2 * pad
    parts = []
    for i, (name, role) in enumerate(PLATFORMS):
        x = pad + (i % cols) * (cw + gap)
        y = pad + top + (i // cols) * (ch + gap)
        parts.append(f'''<g>
<rect x="{x + 0.5:.1f}" y="{y + 0.5}" width="{cw - 1:.1f}" height="{ch - 1}" rx="6" fill="{PANEL}" stroke="{LINE}"/>
<rect x="{x:.1f}" y="{y + 18}" width="3" height="{ch - 36}" fill="{RED}"/>
<text x="{x + 24:.1f}" y="{y + 26}" font-size="10" fill="{DIM}" letter-spacing="2">{i + 1:02d}</text>
<text x="{x + 24:.1f}" y="{y + 55}" font-size="26" class="serif" fill="{SILVER}">{e(name)}</text>
<text x="{x + 24:.1f}" y="{y + 76}" font-size="11.5" fill="{MUTED}" letter-spacing="1">{e(role.upper())}</text>
<path d="M{x + cw - 30:.1f} {y + 14}H{x + cw - 14:.1f}V{y + 30}" fill="none" stroke="{RED}" stroke-opacity="0.8"/>
</g>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Training grounds: {e(', '.join(n for n, _ in PLATFORMS))}">
{STYLE}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>
<text x="{pad}" y="{pad + 22}" font-size="14" fill="{MUTED}"><tspan fill="{RED}">evel@lab</tspan>:~$ <tspan fill="{SILVER}">ls ~/training_grounds</tspan></text>
{"".join(parts)}
</svg>
'''
    write("platforms.svg", svg)


if __name__ == "__main__":
    banner()
    for h in HEADERS:
        header(*h)
    interests()
    stack()
    distros()
    platforms()
    for c in CARDS:
        card(*c)
    now()
    footer()
