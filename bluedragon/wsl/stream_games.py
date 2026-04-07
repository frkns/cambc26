# working on wsl

import os
import subprocess
import re
import csv
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

TEAM = "something else"
OUTPUT_FILE = "ModifiedGames.csv"

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

def extract_full_match_ids(text):
    return re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)

def parse_table(text):
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

def parse_matches(text):
    rows = parse_table(text)
    full_ids = extract_full_match_ids(text)
    matches = []
    for i, r in enumerate(rows):
        team_a    = r.get("Team A", "").strip()
        team_b    = r.get("Team B", "").strip()
        score_raw = r.get("Score", "").strip()
        date      = r.get("Date", "").strip()
        match_id  = full_ids[i] if i < len(full_ids) else r.get("Match ID", "").strip()
        if not match_id:
            continue
        score_a, score_b = -1, -1
        if "-" in score_raw:
            try:
                score_a, score_b = map(int, score_raw.split("-"))
            except:
                pass
        matches.append({
            "match_id": match_id,
            "team_a": team_a,
            "team_b": team_b,
            "score_a": score_a,
            "score_b": score_b,
            "date": date,
        })
    return matches

def parse_game_results(text):
    rows = parse_table(text)
    results = []
    for r in rows:
        map_name = (r.get("Map") or r.get("map") or r.get("Map Name") or "").strip()
        winner   = (r.get("Winner") or r.get("winner") or r.get("Winning Team") or "").strip()
        if map_name:
            results.append({"map": map_name, "winner": winner})
    return results

def load_seen_match_ids(filepath):
    """Read match_ids already recorded in the CSV, returns a set."""
    seen = set()
    if not os.path.exists(filepath):
        return seen
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "match_id" not in (reader.fieldnames or []):
            return seen  # old CSV without match_id column, can't dedup
        for row in reader:
            if row.get("match_id"):
                seen.add(row["match_id"])
    print(f"[DEDUP] Loaded {len(seen)} already-seen match IDs from {filepath}")
    return seen

# -------------------------
# ENV
# -------------------------
env = os.environ.copy()

FIELDNAMES = ["match_id", "maps", "OurTeamsSide", "Victory", "enemyTeam", "date"]

# -------------------------
# MAIN LOOP
# -------------------------
total_games = 0
skipped_matches = 0
Pagination = None

seen_match_ids = load_seen_match_ids(OUTPUT_FILE)

# Append if file exists, write fresh if not
file_mode = "a" if os.path.exists(OUTPUT_FILE) and seen_match_ids else "w"

with open(OUTPUT_FILE, file_mode, newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    if file_mode == "w":
        writer.writeheader()

    for page in range(20):
        print(f"Page {page + 1}...")

        command = ["cambc", "match", "list", "--team", TEAM, "--limit", "100"]
        if Pagination:
            command += ["--cursor", Pagination]

        output = run_cmd(command, env)

        cursor_match = re.search(r"--cursor\s+([^\s']+)", output)
        Pagination = cursor_match.group(1) if cursor_match else None

        matches = parse_matches(output)
        page_games = 0
        all_seen = True  # tracks if entire page is already recorded

        for m in matches:
            if TEAM not in (m["team_a"], m["team_b"]):
                continue

            if m["match_id"] in seen_match_ids:
                skipped_matches += 1
                all_seen = True
                continue

            all_seen = False
            result2 = run_cmd(["cambc", "match", "info", m["match_id"]], env)
            game_results = parse_game_results(result2)

            for o in game_results:
                weWon = TEAM in o["winner"]
                otherTeam = m["team_b"] if m["team_a"] == TEAM else m["team_a"]
                row = {
                    "match_id": m["match_id"],
                    "maps": o["map"],
                    "OurTeamsSide": "A" if m["team_a"] == TEAM else "B",
                    "Victory": 1 if weWon else 0,
                    "enemyTeam": otherTeam,
                    "date": m["date"],
                }
                writer.writerow(row)
                f.flush()
                page_games += 1
                total_games += 1

            seen_match_ids.add(m["match_id"])

        print(f"  {page_games} new games written (total: {total_games}, skipped: {skipped_matches})")

        # Stop early if entire page was already recorded — no point paginating further
        if all_seen and skipped_matches > 0:
            print("  All matches on this page already recorded, stopping early.")
            break

        if not Pagination:
            break

print(f"\nDone. {total_games} new games saved to {OUTPUT_FILE}")
