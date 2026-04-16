import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import pandas as pd
import numpy as np


TEAM = "something else"
TEAM = "Blue Dragon"  # spy on other teams

FILE = f"Games_{TEAM.replace(' ', '_')}.csv"

df = pd.read_csv(FILE)

df["date"] = pd.to_datetime(df["date"]).dt.tz_localize("UTC")

now = pd.Timestamp.now(tz="UTC")
df["hours_ago"] = (now - df["date"]).dt.total_seconds() / 3600

df = df[df["hours_ago"] < 15]
maps = set(df["maps"])
teams = set(df["enemyTeam"])
teams = set(team for team in teams if '(OLD)' not in team)


team_side_winfrac = {}
team_games = {}
team_counts = {}

for team in teams:
    sub = df[(df["enemyTeam"] == team)]
    if not sub.empty:
        win_frac = sub.groupby("maps")["Victory"].mean()
        win_sum  = sub.groupby("maps")["Victory"].sum()
        counts   = sub.groupby("maps")["Victory"].count()
    else:
        win_frac = pd.Series(dtype=float)
        win_sum  = pd.Series(dtype=float)
        counts   = pd.Series(dtype=float)
    win_frac = win_frac.reindex(maps)
    win_sum  = win_sum.reindex(maps)
    counts   = counts.reindex(maps)
    team_side_winfrac[f"{team}"] = win_frac
    team_games[f"{team}"]        = win_sum
    team_counts[f"{team}"]       = counts

summary_df       = pd.DataFrame(team_side_winfrac)
summary_df_games = pd.DataFrame(team_games)
summary_df_count = pd.DataFrame(team_counts)

summary_df.loc["AVG_WIN"]           = summary_df.mean()
summary_df_games.loc["TOTAL_WINS"]  = summary_df_games.sum()
summary_df_count.loc["TOTAL_GAMES"] = summary_df_count.sum()

summary_df["MAP_AVG"]         = summary_df.mean(axis=1)
summary_df_games["MAP_TOTAL"] = summary_df_games.sum(axis=1)
summary_df_count["MAP_GAMES"] = summary_df_count.sum(axis=1)

cols_to_sort = [c for c in summary_df.columns if c != "MAP_AVG"]
sorted_cols  = summary_df[cols_to_sort].sort_values("AVG_WIN", axis=1, ascending=True).columns.tolist()

summary_df       = summary_df[sorted_cols + ["MAP_AVG"]]
summary_df_games = summary_df_games[sorted_cols + ["MAP_TOTAL"]]
summary_df_count = summary_df_count[sorted_cols + ["MAP_GAMES"]]

# Sort rows (maps) by MAP_AVG ascending (worst maps first), keeping summary rows last
data_rows   = [i for i in summary_df.index if i != "AVG_WIN"]
sorted_rows = summary_df.loc[data_rows].sort_values("MAP_AVG", ascending=True).index.tolist()

summary_df       = summary_df.loc[sorted_rows + ["AVG_WIN"]]
summary_df_games = summary_df_games.loc[sorted_rows + ["TOTAL_WINS"]]
summary_df_count = summary_df_count.loc[sorted_rows + ["TOTAL_GAMES"]]


def calc_95ci_wilson(wins, n):
    if n == 0 or pd.isna(wins) or pd.isna(n) or n < 1:
        return np.nan, np.nan
    z  = 1.96
    n  = float(n)
    p  = wins / n
    center = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / (1 + z**2 / n)
    return (center - margin) * 100, (center + margin) * 100


def get_wins_and_games(idx, col, df_rates, df_games):
    last_row_rates = df_rates.index[-1]
    last_col_rates = df_rates.columns[-1]
    last_row_games = df_games.index[-1]
    last_col_games = df_games.columns[-1]

    is_summary_row = (idx == last_row_rates)
    is_summary_col = (col == last_col_rates)

    data_rows = [i for i in df_games.index if i != last_row_games]
    data_cols = [c for c in df_games.columns if c != last_col_games]

    if is_summary_row and is_summary_col:
        total_wins, total_games = 0, 0
        for r in data_rows:
            for c in data_cols:
                w  = df_games.loc[r, c]
                wr = df_rates.loc[r, c]
                if not pd.isna(w) and not pd.isna(wr) and wr > 0:
                    total_wins  += w
                    total_games += w / wr
        return total_wins, total_games

    elif is_summary_row:
        total_wins, total_games = 0, 0
        for r in data_rows:
            w  = df_games.loc[r, col]
            wr = df_rates.loc[r, col]
            if not pd.isna(w) and not pd.isna(wr) and wr > 0:
                total_wins  += w
                total_games += w / wr
        return total_wins, total_games

    elif is_summary_col:
        total_wins, total_games = 0, 0
        for c in data_cols:
            w  = df_games.loc[idx, c]
            wr = df_rates.loc[idx, c]
            if not pd.isna(w) and not pd.isna(wr) and wr > 0:
                total_wins  += w
                total_games += w / wr
        return total_wins, total_games

    return np.nan, np.nan


def get_match_count(idx, col, df_rates, df_count):
    last_row   = df_rates.index[-1]
    last_col   = df_rates.columns[-1]
    last_row_c = df_count.index[-1]
    last_col_c = df_count.columns[-1]

    is_summary_row = (idx == last_row)
    is_summary_col = (col == last_col)

    if is_summary_row and is_summary_col:
        v = df_count.loc[last_row_c, last_col_c]
    elif is_summary_row:
        v = df_count.loc[last_row_c, col]
    elif is_summary_col:
        v = df_count.loc[idx, last_col_c]
    else:
        return np.nan

    return int(v) if not pd.isna(v) else 0


def print_colored_winrate(df, df_games, df_count):
# ---===
    RED        = "\033[91m"
    YELLOW     = "\033[93m"
    GREEN      = "\033[92m"
    GRAY       = "\033[90m"
    CYAN       = "\033[96m"
    BLUE       = "\033[94m"
    MAGENTA    = "\033[95m"
    WHITE      = "\033[97m"
    ORANGE     = "\033[38;5;214m"
    PINK       = "\033[38;5;213m"
    LIME       = "\033[38;5;154m"
    TEAL       = "\033[38;5;43m"
    GOLD       = "\033[38;5;220m"
    CORAL      = "\033[38;5;209m"
    SKY        = "\033[38;5;117m"
    PURPLE     = "\033[38;5;141m"
    DARK_RED   = "\033[38;5;124m"
    DARK_GREEN = "\033[38;5;22m"
    DARK_GRAY  = "\033[38;5;240m"
    LIGHT_GRAY = "\033[38;5;250m"

    # Background colors
    BG_RED        = "\033[41m"
    BG_YELLOW     = "\033[43m"
    BG_GREEN      = "\033[42m"
    BG_GRAY       = "\033[100m"
    BG_CYAN       = "\033[46m"
    BG_BLUE       = "\033[44m"
    BG_MAGENTA    = "\033[45m"
    BG_WHITE      = "\033[47m"
    BG_ORANGE     = "\033[48;5;214m"
    BG_PINK       = "\033[48;5;213m"
    BG_LIME       = "\033[48;5;154m"
    BG_TEAL       = "\033[48;5;43m"
    BG_GOLD       = "\033[48;5;220m"
    BG_CORAL      = "\033[48;5;209m"
    BG_SKY        = "\033[48;5;117m"
    BG_PURPLE     = "\033[48;5;141m"
    BG_DARK_RED   = "\033[48;5;124m"
    BG_DARK_GREEN = "\033[48;5;22m"
    BG_DARK_GRAY  = "\033[48;5;240m"
    BG_BLACK      = "\033[40m"

    # Styles
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    ITALIC    = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK     = "\033[5m"
    REVERSE   = "\033[7m"
    STRIKE    = "\033[9m"
    RESET     = "\033[0m"
# ===---

    col_width       = 7   # narrowed
    ci_col_width    = 11  # narrowed
    cnt_col_width   = 6   # end-column for n
    row_label_width = 22  # narrowed

    last_row = df.index[-1]
    last_col = df.columns[-1]

    def get_bg_color(val):
        if pd.isna(val):  return BG_GRAY
        if val >= 0.6:    return BG_GREEN
        elif val >= 0.4:  return BG_YELLOW
        else:             return BG_RED

    def get_fg_color(val_pct):
        if pd.isna(val_pct): return GRAY
        if val_pct >= 60:    return GREEN
        elif val_pct >= 40:  return YELLOW
        else:                return RED

    def fmt_pct(val):
        if pd.isna(val): return '-'
        pct = val * 100
        return f'{int(pct)}' if pct == int(pct) else f'{pct:.1f}'

    def fmt_ci_inline(lo, hi, width):
        """CI string padded to `width` — used for both col_width and ci_col_width slots."""
        if pd.isna(lo) or pd.isna(hi):
            return f"{GRAY}{'-':>{width}}{RESET}"
        lo_r, hi_r = round(lo), round(hi)
        visible = f"{lo_r}-{hi_r}"
        pad     = max(0, width - len(visible))
        return (
            " " * pad
            + f"{get_fg_color(lo_r)}{lo_r}{RESET}"
            + "-"
            + f"{get_fg_color(hi_r)}{hi_r}{RESET}"
        )

    def fmt_count(n, width, bold=False):
        """Count string padded to `width`."""
        if pd.isna(n) or n == 0:
            return f"{GRAY}{'-':>{width}}{RESET}"
        s      = str(int(n))
        padded = f"{s:>{width}}"
        return f"{BOLD}{padded}{RESET}" if bold else f"{GRAY}{padded}{RESET}"

    # Pre-compute CI map
    ci_map = {}
    for idx in df.index:
        for col in df.columns:
            if (idx == last_row) or (col == last_col):
                wins, n = get_wins_and_games(idx, col, df, df_games)
                if not (pd.isna(wins) or pd.isna(n)) and n > 0:
                    lo, hi = calc_95ci_wilson(wins, n)
                else:
                    lo, hi = np.nan, np.nan
                ci_map[(idx, col)] = (lo, hi)

    # ------------------------------------------------------------------ header
    header = f"{'Map':<{row_label_width}}"
    for col in df.columns:
        truncated = str(col)[:col_width - 1]
        pad = " " * (col_width - len(truncated))
        if col == last_col:
            header += f"{pad}{BOLD}{UNDERLINE}{truncated}{RESET}"
        else:
            header += f"{pad}{UNDERLINE}{truncated}{RESET}"

    header += f"{BOLD}{'95CI':>{ci_col_width}}{RESET}"
    header += f"{BOLD}{'n':>{cnt_col_width}}{RESET}"
    print(f"{GRAY}Showing results for team {RESET}{CYAN}{UNDERLINE}{TEAM}{RESET}")
    print(f"{BOLD}{header}{RESET}")
    print("-" * (row_label_width + col_width * len(df.columns) + ci_col_width + cnt_col_width))

    for idx, row in df.iterrows():
        is_summary_row = (idx == last_row)
        label = str(idx)[:row_label_width - 1]

        # ---- main value line ------------------------------------------------
        line = f"{label:<{row_label_width}}"
        for col, val in row.items():
            is_summary_col = (col == last_col)
            use_bg = is_summary_row or is_summary_col
            text   = fmt_pct(val)
            padded = f"{text:>{col_width}}"
            if use_bg:
                line += f"{BOLD}{get_bg_color(val)}\033[30m{padded}{RESET}"
            else:
                line += f"{get_fg_color(val * 100 if not pd.isna(val) else np.nan)}{padded}{RESET}"

        # CI and n for the MAP_AVG column (right-hand summary col)
        lo, hi = ci_map.get((idx, last_col), (np.nan, np.nan))
        line += fmt_ci_inline(lo, hi, ci_col_width)
        n = get_match_count(idx, last_col, df, df_count)
        line += fmt_count(n, cnt_col_width, bold=is_summary_row)
        print(line)

        # ---- sub-rows for the AVG_WIN summary row ---------------------------
        if is_summary_row:
            ci_line  = f"{'  95CI':<{row_label_width}}"
            cnt_line = f"{'  n':<{row_label_width}}"

            for col in df.columns:
                lo, hi = ci_map.get((idx, col), (np.nan, np.nan))
                n      = get_match_count(idx, col, df, df_count)
                if col == last_col:
                    # leave blank — already in the dedicated end columns
                    ci_line  += " " * col_width
                    cnt_line += " " * col_width
                else:
                    # both sub-rows use col_width so they sit under each team column
                    ci_line  += fmt_ci_inline(lo, hi, col_width)
                    cnt_line += fmt_count(n, col_width, bold=False)

            # fill the ci_col_width + cnt_col_width end slots
            lo, hi   = ci_map.get((idx, last_col), (np.nan, np.nan))
            n_corner = get_match_count(idx, last_col, df, df_count)
            ci_line  += fmt_ci_inline(lo, hi, ci_col_width)
            ci_line  += " " * cnt_col_width          # blank under n header
            cnt_line += " " * ci_col_width            # blank under 95CI header
            cnt_line += fmt_count(n_corner, cnt_col_width, bold=True)
            print(ci_line)
            print(cnt_line)

    print()


print_colored_winrate(summary_df, summary_df_games, summary_df_count)
