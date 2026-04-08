import pandas as pd
import time

df = pd.read_csv("ModifiedGames.csv")

df["date"] = pd.to_datetime(df["date"]).dt.tz_localize("UTC")

now = pd.Timestamp.now(tz="UTC")
df["hours_ago"] = (now - df["date"]).dt.total_seconds() / 3600

df = df[df["hours_ago"] < 15]
print(len(df["hours_ago"]))
maps = set(df["maps"])
teams = set(df["enemyTeam"])
sides = ["A", "B"]
print(len(teams))

# Dictionary to hold the per-team-side series
team_side_winfrac = {}
team_games = {}

for team in teams:
    sub = df[(df["enemyTeam"] == team)]
    if not sub.empty:
        win_frac = sub.groupby("maps")["Victory"].mean()
    else:
        win_frac = pd.Series(dtype=float)
    win_frac = win_frac.reindex(maps)
    team_side_winfrac[f"{team}"] = win_frac

summary_df = pd.DataFrame(team_side_winfrac)

for team in teams:
    sub = df[(df["enemyTeam"] == team)]
    if not sub.empty:
        win_frac = sub.groupby("maps")["Victory"].sum()
    else:
        win_frac = pd.Series(dtype=float)
    win_frac = win_frac.reindex(maps)
    team_games[f"{team}"] = win_frac

summary_df_games = pd.DataFrame(team_games)

# Add average win % row at the bottom
summary_df.loc["AVG_WIN%"] = summary_df.mean()
summary_df_games.loc["TOTAL_WINS"] = summary_df_games.sum()

# --- Add overall map win rate column (mean across all teams, ignoring NaN) ---
summary_df["MAP_AVG"] = summary_df.mean(axis=1)
summary_df_games["MAP_TOTAL"] = summary_df_games.sum(axis=1)

# Sort columns by average win rate (worst enemies first), excluding MAP_AVG
cols_to_sort = [c for c in summary_df.columns if c != "MAP_AVG"]
sorted_cols = summary_df[cols_to_sort].sort_values("AVG_WIN%", axis=1, ascending=True).columns.tolist()

# Put MAP_AVG at the end
summary_df = summary_df[sorted_cols + ["MAP_AVG"]]
summary_df_games = summary_df_games[sorted_cols + ["MAP_TOTAL"]]

print(summary_df)
summary_df.to_csv("Win.csv")
summary_df_games.to_csv("ProcGames.csv")



def print_colored_winrate(df):
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    GRAY   = "\033[90m"
    BOLD   = "\033[1m"
    WHITE  = "\033[97m"
    RESET  = "\033[0m"

    BG_RED    = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_GREEN  = "\033[42m"
    BG_GRAY   = "\033[100m"

    col_width = 9
    row_label_width = 25

    def get_color(val, background=False):
        if pd.isna(val):
            return BG_GRAY if background else GRAY
        if val >= 0.6:
            return BG_GREEN if background else GREEN
        elif val >= 0.4:
            return BG_YELLOW if background else YELLOW
        else:
            return BG_RED if background else RED

    def format_val(val):
        if pd.isna(val):
            return '-'
        s = f'{val*100:.1f}%'
        if s.endswith('.0%'):
            s = s[:-3] + '%'
        return s

    # Identify special rows/cols
    last_row = df.index[-1]
    last_col = df.columns[-1]

    header = f"{'Map':<{row_label_width}}"
    for col in df.columns:
        truncated = str(col)[:col_width-1]
        # Bold the last summary column header
        if col == last_col:
            header += f"{BOLD}{truncated:>{col_width}}{RESET}"
        else:
            header += f"{truncated:>{col_width}}"
    print(f"\n{BOLD}{header}{RESET}")
    print("-" * (row_label_width + col_width * len(df.columns)))

    for idx, row in df.iterrows():
        is_summary_row = (idx == last_row)

        label = str(idx)[:row_label_width-1]
        line = f"{label:<{row_label_width}}"

        for col, val in row.items():
            is_summary_col = (col == last_col)
            # Use background if it's the summary row OR summary column
            use_background = is_summary_row or is_summary_col
            color = get_color(val, background=use_background)
            text = format_val(val)
            padded = f"{text:>{col_width}}"

            if use_background:
                line += f"{BOLD}{color}\033[30m{padded}{RESET}"
            else:
                line += f"{color}{padded}{RESET}"

        print(line)

    print()

print_colored_winrate(summary_df)
