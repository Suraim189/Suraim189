#!/usr/bin/env python3
"""Generates assets/terminal.svg, assets/languages.svg and assets/contributions-3d.svg
for the profile README. Standard library only + GitHub GraphQL API (GITHUB_TOKEN)."""
import datetime as dt
import json
import math
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "Suraim189")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("OUT_DIR", "assets")

BG, CARD, TEXT, MUTED = "#1a1b27", "#24283b", "#c0caf5", "#565f89"
BLUE, PURPLE, PINK, GREEN, ORANGE = "#7aa2f7", "#bb9af7", "#f7768e", "#9ece6a", "#ff9e64"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', 'JetBrains Mono', 'DejaVu Sans Mono', Consolas, 'Courier New', monospace"
FALLBACK = [BLUE, PURPLE, PINK, GREEN, ORANGE, "#7dcfff"]

QUERY = """
query($login:String!){
  user(login:$login){
    createdAt
    followers{totalCount}
    repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){
      totalCount
      nodes{
        stargazerCount
        languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}
      }
    }
    contributionsCollection{
      totalCommitContributions
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
  }
}"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if "errors" in res:
        raise RuntimeError(res["errors"])
    return res["data"]


def sample_data():
    today = dt.date.today()
    counts = [0] * 341 + [0] * 22 + [1, 0, 2, 0, 1, 3, 0, 1]
    n = len(counts)
    days = [((today - dt.timedelta(days=n - 1 - i)).isoformat(), c) for i, c in enumerate(counts)]
    return dict(repos=5, stars=0, commits=3, total=sum(counts), days=days,
                langs=[("C#", 5500, "#178600"), ("C++", 2500, "#f34b7d"), ("Python", 2000, "#3572A5")])


def load_data():
    if not TOKEN:
        print("GITHUB_TOKEN not set -> using sample data")
        return sample_data()
    u = gql(QUERY, {"login": USER})["user"]
    cc = u["contributionsCollection"]
    days = [(x["date"], x["contributionCount"]) for w in cc["contributionCalendar"]["weeks"] for x in w["contributionDays"]]
    agg = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            a = agg.setdefault(e["node"]["name"], [0, e["node"]["color"]])
            a[0] += e["size"]
    langs = sorted(((k, v[0], v[1]) for k, v in agg.items()), key=lambda t: -t[1])
    return dict(repos=u["repositories"]["totalCount"], stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
                commits=cc["totalCommitContributions"], total=cc["contributionCalendar"]["totalContributions"],
                days=days, langs=langs)


# ---------------------------------------------------------------- terminal card
def reveal(width, start, dur, total):
    a, b = start / total, (start + dur) / total
    return (f'<animate attributeName="width" values="0;0;{width:.1f};{width:.1f}" '
            f'keyTimes="0;{a:.4f};{b:.4f};1" dur="{total:.1f}s" repeatCount="indefinite"/>')


def terminal_svg(d):
    tot = sum(s for _, s, _ in d["langs"]) or 1
    lang_txt = " · ".join(f"{n} {s * 100 / tot:.0f}%" for n, s, _ in d["langs"][:4]) or "no language data yet"
    rows = [
        ("cmd", "whoami"),
        ("out", "Suraim Ahmad · Software Engineering Undergraduate @ NTU"),
        ("cmd", "cat stack.txt"),
        ("out", "C++ · C# · Python · SQL · .NET · RAG pipelines"),
        ("cmd", "git stats --last-year"),
        ("out", f"{d['commits']} commits · {d['total']} contributions · {d['repos']} public repos · {d['stars']} stars"),
        ("cmd", "ls ~/languages"),
        ("out", lang_txt),
        ("cmd", "./now_building.sh"),
        ("out", "C# WinForms apps · SQL databases · AI Agent RAG systems"),
    ]
    CW, X0, Y0, LH, W = 9.0, 30, 92, 24, 900
    H = Y0 + len(rows) * LH + 34
    t, spans = 0.6, []
    for kind, text in rows:
        n = len(text) + 2
        dur = max(0.4, n * (0.05 if kind == "cmd" else 0.022))
        spans.append((t, dur))
        t += dur + (0.45 if kind == "cmd" else 0.35)
    final_start = t
    total = t + 0.4 + 7
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<defs><clipPath id="win"><rect width="{W}" height="{H}" rx="16"/></clipPath>']
    for i, ((kind, text), (st, du)) in enumerate(zip(rows, spans)):
        w = (len(text) + 2) * CW
        s.append(f'<clipPath id="c{i}"><rect x="{X0}" y="{Y0 + i * LH - 17}" width="{w:.1f}" height="24">{reveal(w, st, du, total)}</rect></clipPath>')
    yl = Y0 + len(rows) * LH
    s.append(f'<clipPath id="cf"><rect x="{X0}" y="{yl - 17}" width="{3 * CW:.1f}" height="24">{reveal(3 * CW, final_start, 0.4, total)}</rect></clipPath></defs>')
    s.append('<g clip-path="url(#win)">')
    s.append(f'<rect width="{W}" height="{H}" fill="#16161e"/><rect width="{W}" height="40" fill="#1f2335"/>')
    for cx, col in ((24, PINK), (46, "#e0af68"), (68, GREEN)):
        s.append(f'<circle cx="{cx}" cy="20" r="6" fill="{col}"/>')
    s.append(f'<text x="{W / 2}" y="25" font-size="13" text-anchor="middle" font-family="{MONO}" fill="{MUTED}">suraim@ntu: ~/profile</text>')
    for i, (kind, text) in enumerate(rows):
        y = Y0 + i * LH
        n = len(text) + 2
        if kind == "cmd":
            body = f'<tspan fill="{GREEN}">$ </tspan><tspan fill="{BLUE}">{escape(text)}</tspan>'
        else:
            body = f'<tspan fill="{PURPLE}">→ </tspan><tspan fill="{TEXT}">{escape(text)}</tspan>'
        s.append(f'<text x="{X0}" y="{y}" font-size="15" font-family="{MONO}" textLength="{n * CW:.1f}" lengthAdjust="spacing" clip-path="url(#c{i})">{body}</text>')
    s.append(f'<g clip-path="url(#cf)"><text x="{X0}" y="{yl}" font-size="15" font-family="{MONO}" fill="{GREEN}">$ </text>'
             f'<rect x="{X0 + 2 * CW + 1}" y="{yl - 13}" width="9" height="17" fill="{PURPLE}"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>')
    s.append(f'</g><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="#292e42"/></svg>')
    return "\n".join(s)


# ---------------------------------------------------------------- languages card
def languages_svg(d):
    W, H = 480, 200
    tot = sum(sz for _, sz, _ in d["langs"])
    top = d["langs"][:5]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" rx="15" fill="{BG}"/>',
         f'<text x="210" y="34" font-size="17" font-weight="700" fill="{BLUE}">Most Used Languages</text>']
    if not tot:
        s.append(f'<text x="{W / 2}" y="110" font-size="14" text-anchor="middle" fill="{MUTED}">No language data yet</text></svg>')
        return "\n".join(s)
    cx, cy, r, sw = 100, 104, 62, 22
    C = 2 * math.pi * r
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{CARD}" stroke-width="{sw}"/>')
    start = 0.0
    for i, (name, size, color) in enumerate(top):
        col = color or FALLBACK[i % len(FALLBACK)]
        seg = C * size / tot
        ln = max(seg - 2, 0.5)
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" '
                 f'stroke-dasharray="{ln:.2f} {C - ln:.2f}" stroke-dashoffset="{-start:.2f}" transform="rotate(-90 {cx} {cy})">'
                 f'<animate attributeName="stroke-dasharray" from="0 {C:.2f}" to="{ln:.2f} {C - ln:.2f}" dur="1.2s" fill="freeze"/></circle>')
        start += seg
    s.append(f'<text x="{cx}" y="{cy + 2}" font-size="22" font-weight="700" text-anchor="middle" fill="{TEXT}">{top[0][1] * 100 / tot:.0f}%</text>')
    s.append(f'<text x="{cx}" y="{cy + 20}" font-size="12" text-anchor="middle" fill="{MUTED}">{escape(top[0][0])}</text>')
    for i, (name, size, color) in enumerate(top):
        col = color or FALLBACK[i % len(FALLBACK)]
        y = 66 + i * 28
        pct = size * 100 / tot
        bw = 85 * pct / 100
        s += [f'<circle cx="217" cy="{y - 4}" r="5" fill="{col}"/>',
              f'<text x="230" y="{y}" font-size="13" fill="{TEXT}">{escape(name)}</text>',
              f'<rect x="322" y="{y - 9}" width="85" height="7" rx="3.5" fill="{CARD}"/>',
              f'<rect x="322" y="{y - 9}" width="{bw:.1f}" height="7" rx="3.5" fill="{col}"><animate attributeName="width" from="0" to="{bw:.1f}" dur="1.2s" fill="freeze"/></rect>',
              f'<text x="{W - 18}" y="{y}" font-size="12" text-anchor="end" fill="{MUTED}">{pct:.1f}%</text>']
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- 3D skyline
PAL = [("#262b40", "#343b58", "#1d2133"), ("#3b4f8a", "#4f66ad", "#2e3d6c"), ("#5a7bd6", "#7aa2f7", "#4660ad"),
       ("#9d7cd8", "#bb9af7", "#7d62ae"), ("#f7768e", "#ff9db0", "#c95e72")]


def contrib3d_svg(d):
    days = d["days"][-371:]
    first = dt.date.fromisoformat(days[0][0])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cells = []
    for ds, c in days:
        dd = dt.date.fromisoformat(ds)
        cells.append(((dd - start).days // 7, (dd.weekday() + 1) % 7, c))
    ncol = max(c[0] for c in cells) + 1
    mx = max(c for _, _, c in cells)
    W, H = 900, 270
    cw, bw, rdx, rdy, tx, ty = 14, 10, 6, 8, 5, 4
    L = (W - ((ncol - 1) * cw + 6 * rdx + bw + tx)) / 2
    B0 = H - 44
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
         f'<text x="28" y="40" font-size="22" font-weight="700" fill="{BLUE}">3D Contribution Skyline</text>',
         f'<text x="28" y="60" font-size="13" fill="{MUTED}">Last 12 months</text>',
         f'<text x="{W - 28}" y="40" font-size="14" text-anchor="end" fill="{TEXT}">{d["total"]} contributions · best day {mx}</text>']
    for col, row, c in sorted(cells, key=lambda k: (-k[1], k[0])):
        lvl = 0 if (c == 0 or mx == 0) else min(4, math.ceil(c / mx * 4))
        h = 3 if lvl == 0 else 6 + c / mx * 72
        px, py = L + col * cw + row * rdx, B0 - row * rdy
        f, t, sd = PAL[lvl]
        poly = (f'<polygon points="{px:.1f},{py:.1f} {px + bw:.1f},{py:.1f} {px + bw:.1f},{py - h:.1f} {px:.1f},{py - h:.1f}" fill="{f}"/>'
                f'<polygon points="{px:.1f},{py - h:.1f} {px + bw:.1f},{py - h:.1f} {px + bw + tx:.1f},{py - h - ty:.1f} {px + tx:.1f},{py - h - ty:.1f}" fill="{t}"/>'
                f'<polygon points="{px + bw:.1f},{py:.1f} {px + bw + tx:.1f},{py - ty:.1f} {px + bw + tx:.1f},{py - h - ty:.1f} {px + bw:.1f},{py - h:.1f}" fill="{sd}"/>')
        if lvl == 4:
            poly = f'<g>{poly}<animate attributeName="opacity" values="1;0.55;1" dur="2.4s" repeatCount="indefinite"/></g>'
        s.append(poly)
    lx = W - 190
    s.append(f'<text x="{lx - 8}" y="{H - 14}" font-size="11" text-anchor="end" fill="{MUTED}">Less</text>')
    for i, p in enumerate(PAL):
        s.append(f'<rect x="{lx + i * 20}" y="{H - 24}" width="14" height="14" rx="3" fill="{p[2 if i else 0]}"/>' if False else
                 f'<rect x="{lx + i * 20}" y="{H - 24}" width="14" height="14" rx="3" fill="{p[1]}"/>')
    s.append(f'<text x="{lx + 108}" y="{H - 14}" font-size="11" fill="{MUTED}">More</text></svg>')
    return "\n".join(s)


def main():
    try:
        d = load_data()
    except Exception as e:  # show the error in the Actions log
        print("ERROR:", e)
        sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("terminal.svg", terminal_svg), ("languages.svg", languages_svg), ("contributions-3d.svg", contrib3d_svg)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(fn(d))
    print("done:", {k: v for k, v in d.items() if k not in ("days", "langs")}, [l[0] for l in d["langs"][:5]])


if __name__ == "__main__":
    main()
