import os
import subprocess
import re
from time import sleep
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

TEAM = "something else"

def run_cmd(command, env):
    wide_env = env.copy()
    wide_env["COLUMNS"] = "300"
    wide_env["LINES"] = "10000"
    wide_env["TERM"] = "dumb"
    wide_env["NO_COLOR"] = "1"
    wide_env["RICH_NO_COLOR"] = "1"
    wide_env["FORCE_COLOR"] = "0"

    cmd_str = " ".join(f"'{a}'" if " " in a else a for a in command)
    full_cmd = f"stty cols 300 2>/dev/null; {cmd_str}"
    wrapped = ["script", "-q", "-c", full_cmd, "/dev/null"]

    result = subprocess.run(
        wrapped,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env=wide_env
    )
    return result.stdout

def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)

def strip_box(text):
    replacements = str.maketrans({
        "┃": "│", "┡": "├", "┩": "┤", "╇": "┼",
        "━": "─", "┏": "┌", "┗": "└", "┓": "┐", "┛": "┘",
        "\r": "",
    })
    return text.translate(replacements)

def parse_table(text):
    """Generic box-drawing table parser, returns list of dicts keyed by header."""
    text = strip_ansi(strip_box(text))
    lines = text.splitlines()
    separator_only = re.compile(r'^[│├┼┤\-\+\s─]+$')
    rows = []

    for line in lines:
        line = line.rstrip()
        if not line.startswith("│"):
            continue
        if separator_only.match(line):
            continue
        cells = [c.strip() for c in line.strip("│").split("│")]
        rows.append(cells)

    if len(rows) < 2:
        return []

    header = rows[0]
    num_cols = len(header)
    records = []

    for cells in rows[1:]:
        while len(cells) < num_cols:
            cells.append("")
        if cells[0] == "" and records:
            for i, val in enumerate(cells):
                if val and i < num_cols:
                    prev = records[-1][header[i]]
                    records[-1][header[i]] = (prev + " " + val).strip() if prev else val
        else:
            records.append({header[i]: cells[i] if i < len(cells) else "" for i in range(num_cols)})

    return records

def parse_ladder(text):
    rows = parse_table(text)
    result = []
    for r in rows:
        try:
            result.append({
                "rank": int(r.get("#", r.get("Rank", 0))),
                "team": r.get("Team", "").strip(),
                "rating": int(r.get("Rating", 0)),
                "matches": int(r.get("Matches", 0)),
                "category": r.get("Category", "").strip(),
                "region": r.get("Region", "").strip(),
            })
        except (ValueError, KeyError):
            continue
    return result

def parse_team_search(text):
    """Returns list of teams with team_id from search results."""
    rows = parse_table(text)
    result = []
    for r in rows:
        team_id = (r.get("Team ID") or r.get("ID") or r.get("team_id") or "").strip()
        name = (r.get("Name") or r.get("Team") or r.get("name") or "").strip()
        if team_id:
            result.append({
                "team_id": team_id,
                "name": name,
                "category": r.get("Category", r.get("category", "")).strip(),
                "rating": r.get("Rating", r.get("rating", "")).strip(),
                "matches": r.get("Matches", r.get("matches", "")).strip(),
                "region": r.get("Region", r.get("region", "")).strip(),
            })
    return result

# -------------------------
# ENV
# -------------------------
env = os.environ.copy()

# -------------------------
# FETCH LADDER + TEAM IDs
# -------------------------
print("Fetching ladder...")
output = run_cmd(["cambc", "ladder", "--limit", "4"], env)
ladder = parse_ladder(output)

teams = []
ranks = []
team_ids = []

for t in ladder:
    print(f"  Looking up team ID for: {t['team']}")
    output2 = run_cmd(["cambc", "team", "search", t["team"]], env)
    search_results = parse_team_search(output2)
    if not search_results:
        print(f"  WARNING: could not find team ID for '{t['team']}', skipping")
        continue
    if t["team"] == TEAM:
        continue
    teams.append(t["team"])
    ranks.append(t["rank"])
    team_ids.append(search_results[0]["team_id"])
    print(f"    rank={t['rank']} id={search_results[0]['team_id']}")

print(f"\nReady. Running matches against {len(teams)} teams every X minutes.\n")

# -------------------------
# MAIN LOOP
# -------------------------
for i in range(1000):
    print(f"\n--- Iteration {i} ---")
    for rank, team, tid in zip(ranks, teams, team_ids):
        print(f"  Running unrated vs {team} (rank {rank}, id {tid})")
        output = run_cmd(["cambc", "match", "unrated", tid], env)
        print(output)
        sleep(60 * 21)

