"""Build assets/analytics.svg from the GitHub GraphQL API.

Runs in GitHub Actions (see .github/workflows/stats.yml) with GITHUB_TOKEN,
so the profile no longer depends on third-party stats services.
Usage: GITHUB_TOKEN=... python3 scripts/gen_stats.py [--mock]
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import gen_assets as g  # noqa: E402

LOGIN = "demianscult"
HIDE_LANGS = {"Java"}            # languages to leave out of the chart
SKIP_REPOS = {"demianscult"}     # the profile repo itself
TOP_N = 5

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def mock():
    return {
        "followers": {"totalCount": 1},
        "repositories": {"totalCount": 14, "nodes": [
            {"name": "a", "stargazerCount": 2, "languages": {"edges": [
                {"size": 52000, "node": {"name": "Python"}}, {"size": 9000, "node": {"name": "HTML"}}]}},
            {"name": "b", "stargazerCount": 0, "languages": {"edges": [
                {"size": 21000, "node": {"name": "TypeScript"}}, {"size": 14000, "node": {"name": "CSS"}},
                {"size": 8000, "node": {"name": "JavaScript"}}, {"size": 30000, "node": {"name": "Java"}}]}},
        ]},
        "contributionsCollection": {"totalCommitContributions": 18, "totalPullRequestContributions": 0,
                                    "totalIssueContributions": 0,
                                    "contributionCalendar": {"totalContributions": 21}},
    }


def build(u):
    e = g.e
    repos = [n for n in u["repositories"]["nodes"] if n["name"] not in SKIP_REPOS]
    stars = sum(n["stargazerCount"] for n in repos)
    langs = {}
    for n in repos:
        for ed in n["languages"]["edges"]:
            name = ed["node"]["name"]
            if name not in HIDE_LANGS:
                langs[name] = langs.get(name, 0) + ed["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:TOP_N]
    cc = u["contributionsCollection"]

    stats = [
        ("contributions · last 12 months", cc["contributionCalendar"]["totalContributions"]),
        ("commits", cc["totalCommitContributions"]),
        ("public repositories", len(repos)),
        ("stars earned", stars),
        ("pull requests", cc["totalPullRequestContributions"]),
        ("followers", u["followers"]["totalCount"]),
    ]

    W, H, pad = 1200, 330, 28
    lw = 560
    left = []
    for i, (label, val) in enumerate(stats):
        col, row = i % 2, i // 2
        x = pad + col * (lw / 2)
        y = pad + 86 + row * 72
        left.append(f'<text x="{x:.0f}" y="{y}" font-size="38" class="serif" fill="{g.SILVER if i else g.RED}">{val}</text>'
                    f'<text x="{x:.0f}" y="{y + 24}" font-size="11.5" fill="{g.MUTED}" letter-spacing="1">{e(label.upper())}</text>')

    rx = pad + lw + 40
    bw = W - rx - pad - 70
    right = []
    for i, (name, size) in enumerate(top):
        pct = size / total
        y = pad + 64 + i * 40
        right.append(f'<text x="{rx}" y="{y}" font-size="13" fill="{g.SILVER}">{e(name)}</text>'
                     f'<text x="{rx + bw + 70}" y="{y}" text-anchor="end" font-size="12" fill="{g.MUTED}">{pct * 100:.1f}%</text>'
                     f'<rect x="{rx}" y="{y + 9}" width="{bw}" height="4" rx="2" fill="{g.LINE}"/>'
                     f'<rect x="{rx}" y="{y + 9}" width="{max(bw * pct, 3):.1f}" height="4" rx="2" fill="{g.RED if i == 0 else g.RED_SOFT}" opacity="{1 - i * 0.12:.2f}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats for {LOGIN}: {e('; '.join(f'{l} {v}' for l, v in stats))}. Top languages: {e(', '.join(f'{n} {s / total * 100:.0f}%' for n, s in top))}">
{g.STYLE}
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{g.BG}" stroke="{g.LINE}"/>
<text x="{pad}" y="{pad + 22}" font-size="14" fill="{g.MUTED}"><tspan fill="{g.RED}">evel@lab</tspan>:~$ <tspan fill="{g.SILVER}">gh stats --public</tspan></text>
<text x="{rx}" y="{pad + 22}" font-size="11" fill="{g.RED}" letter-spacing="3">TOP LANGUAGES · BY CODE SIZE</text>
<path d="M{pad + lw + 10} {pad + 44}V{H - pad - 10}" stroke="{g.LINE}"/>
{"".join(left)}
{"".join(right)}
<text x="{W - pad}" y="{H - 14}" text-anchor="end" font-size="10" fill="{g.DIM}" letter-spacing="2">VIA GITHUB API · REFRESHED DAILY</text>
</svg>
'''
    g.write("analytics.svg", svg)


if __name__ == "__main__":
    build(mock() if "--mock" in sys.argv else fetch())
