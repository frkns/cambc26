import os
import subprocess
import re
import csv
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

OUTPUT_FILE = "top10_games.csv"
FIELDNAMES = ["match_id", "team_a", "team_b", "map", "winner", "date"]

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
            })
        except (ValueError, KeyError):
            continue
    return result

def extract_full_match_ids(text):
    return re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)

def parse_matches(text):
    rows = parse_table(text)
    full_ids = extract_full_match_ids(text)
    matches = []
    for i, r in enumerate(rows):
        team_a   = r.get("Team A", "").strip()
        team_b   = r.get("Team B", "").strip()
        date     = r.get("Date", "").strip()
        match_id = full_ids[i] if i < len(full_ids) else r.get("Match ID", "").strip()
        if not match_id:
            continue
        matches.append({
            "match_id": match_id,
            "team_a":   team_a,
            "team_b":   team_b,
            "date":     date,
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
    seen = set()
    if not os.path.exists(filepath):
        return seen
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "match_id" not in (reader.fieldnames or []):
            return seen
        for row in reader:
            if row.get("match_id"):
                seen.add(row["match_id"])
    print(f"[DEDUP] Loaded {len(seen)} already-seen match IDs from {filepath}")
    return seen

# -------------------------
# MAIN
# -------------------------
env = os.environ.copy()

print("Fetching top-10 ladder...")
ladder_output = run_cmd(["cambc", "ladder", "--limit", "10"], env)
ladder = parse_ladder(ladder_output)
top10_teams = [t["team"] for t in ladder if t["team"]]
print(f"Top 10 teams: {top10_teams}")

if not top10_teams:
    print("ERROR: could not parse any teams from ladder, exiting.")
    exit(1)

seen_match_ids = load_seen_match_ids(OUTPUT_FILE)
file_mode = "a" if os.path.exists(OUTPUT_FILE) and seen_match_ids else "w"

total_games    = 0
skipped_matches = 0

with open(OUTPUT_FILE, file_mode, newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    if file_mode == "w":
        writer.writeheader()

    for team in top10_teams:
        print(f"\n--- Fetching matches for: {team} ---")
        team_games   = 0
        team_skipped = 0
        pagination   = None

        for page in range(20):
            print(f"  Page {page + 1}...")

            command = ["cambc", "match", "list", "--team", team, "--limit", "100"]
            if pagination:
                command += ["--cursor", pagination]

            output = run_cmd(command, env)

            cursor_match = re.search(r"--cursor\s+([^\s']+)", output)
            pagination = cursor_match.group(1) if cursor_match else None

            matches = parse_matches(output)
            page_games        = 0
            new_top10_on_page  = 0
            seen_top10_on_page = 0

            for m in matches:
                a_in = m["team_a"] in top10_teams
                b_in = m["team_b"] in top10_teams
                if not (a_in and b_in):
                    # not a top10 vs top10 match — skip but don't affect dedup logic
                    continue

                if m["match_id"] in seen_match_ids:
                    seen_top10_on_page += 1
                    team_skipped       += 1
                    skipped_matches    += 1
                    continue

                # New top10 match
                new_top10_on_page += 1
                result2 = run_cmd(["cambc", "match", "info", m["match_id"]], env)
                game_results = parse_game_results(result2)

                for o in game_results:
                    row = {
                        "match_id": m["match_id"],
                        "team_a":   m["team_a"],
                        "team_b":   m["team_b"],
                        "map":      o["map"],
                        "winner":   o["winner"],
                        "date":     m["date"],
                    }
                    writer.writerow(row)
                    f.flush()
                    page_games += 1
                    team_games += 1
                    total_games += 1

                seen_match_ids.add(m["match_id"])

            print(f"    {page_games} new games written, "
                  f"{seen_top10_on_page} already seen "
                  f"(team total skipped: {team_skipped})")

            # Stop early only if every top10 match on this page was already recorded
            if new_top10_on_page == 0 and seen_top10_on_page > 0:
                print("  All top10 matches on this page already recorded, stopping early.")
                break

            if not pagination:
                break

        print(f"  Total new games for {team}: {team_games}")

print(f"\nDone. {total_games} new game-rows saved to {OUTPUT_FILE} "
      f"({skipped_matches} matches skipped as duplicates)")
