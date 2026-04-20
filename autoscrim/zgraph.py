import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# -------------------------
# CONFIG
# -------------------------
INPUT_FILE   = "top10_games.csv"
HOURS_LIMIT  = 24 * 30      # set None for all time
MIN_GAMES    = 1            # minimum map-games between a pair to include it
OUT_PATH     = "tournament_graph.png"

# -------------------------
# LOAD
# -------------------------
df = pd.read_csv(INPUT_FILE)
df["date"] = pd.to_datetime(df.get("date", None), utc=True, errors="coerce")

if HOURS_LIMIT is not None:
    now = pd.Timestamp.now(tz="UTC")
    df = df[(df["date"].isna()) | (df["date"] >= now - pd.Timedelta(hours=HOURS_LIMIT))].copy()

required = {"team_a", "team_b", "winner"}
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"CSV missing columns: {missing}. Found: {list(df.columns)}")

df["team_a"] = df["team_a"].astype(str)
df["team_b"] = df["team_b"].astype(str)
df["winner"] = df["winner"].astype(str)
df = df[df["winner"].str.strip().ne("")].copy()

teams_in_data = sorted(set(df["team_a"]).union(set(df["team_b"])))
print(f"Rows after filtering: {len(df)}")
print(f"Teams in data ({len(teams_in_data)}): {teams_in_data}")

# -------------------------
# Resolve winner string -> actual team name (fixes 0-edge graphs)
# -------------------------
def norm(s: str) -> str:
    s = str(s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def resolve_winner(team_a: str, team_b: str, winner_raw: str):
    a = norm(team_a)
    b = norm(team_b)
    w = norm(winner_raw)

    # common "side" outputs
    if w in {"a", "team a", "side a", "player a"}:
        return team_a
    if w in {"b", "team b", "side b", "player b"}:
        return team_b

    # exact match
    if w == a:
        return team_a
    if w == b:
        return team_b

    # substring match (handles "Winner: X", etc.)
    if a and a in w:
        return team_a
    if b and b in w:
        return team_b

    return None

df["winner_team"] = [
    resolve_winner(ta, tb, w)
    for ta, tb, w in zip(df["team_a"], df["team_b"], df["winner"])
]

print(f"Resolved winners: {df['winner_team'].notna().sum()}")
print(f"Unresolved winners: {df['winner_team'].isna().sum()}")
if df["winner_team"].isna().any():
    print("\nUnresolved winner examples (first 10):")
    bad = df[df["winner_team"].isna()][["winner", "team_a", "team_b"]].head(10)
    for _, r in bad.iterrows():
        print(f"  winner_raw={r['winner']!r}  team_a={r['team_a']!r} team_b={r['team_b']!r}")

df = df[df["winner_team"].notna()].copy()

# -------------------------
# Aggregate unordered pair stats
# -------------------------
def canonical(a, b):
    return (a, b) if a < b else (b, a)

pair = {}  # (t1, t2) -> wins for t1/t2

for _, r in df.iterrows():
    ta, tb = r["team_a"], r["team_b"]
    wteam = r["winner_team"]
    t1, t2 = canonical(ta, tb)
    if (t1, t2) not in pair:
        pair[(t1, t2)] = {"t1": t1, "t2": t2, "w1": 0, "w2": 0}
    if wteam == t1:
        pair[(t1, t2)]["w1"] += 1
    elif wteam == t2:
        pair[(t1, t2)]["w2"] += 1

# -------------------------
# Build directed graph: WINNER -> LOSER  (your requested direction)
# -------------------------
G = nx.DiGraph()
for t in teams_in_data:
    G.add_node(t)

edge_rows = []  # (winner, loser, winrate_of_winner, wins, total)

for (t1, t2), s in pair.items():
    w1, w2 = s["w1"], s["w2"]
    total = w1 + w2
    if total < MIN_GAMES or total == 0:
        continue

    wr_t1_over_t2 = w1 / total
    if wr_t1_over_t2 >= 0.5:
        winner, loser = t1, t2
        winrate = wr_t1_over_t2
        wins = w1
    else:
        winner, loser = t2, t1
        winrate = 1.0 - wr_t1_over_t2
        wins = w2

    G.add_edge(winner, loser, winrate=winrate, total=total, wins=wins)
    edge_rows.append((winner, loser, winrate, wins, total))

print(f"Edges to draw: {len(edge_rows)}")
if len(edge_rows) == 0:
    raise SystemExit(
        "No edges to draw. This usually means winner strings still aren't resolvable.\n"
        "Check the unresolved examples printed above."
    )

# -------------------------
# Node metric: average winrate vs opponents, UNWEIGHTED by games
# (each opponent counts equally)
# -------------------------
opp_wr = {t: [] for t in teams_in_data}

for (t1, t2), s in pair.items():
    w1, w2 = s["w1"], s["w2"]
    total = w1 + w2
    if total < MIN_GAMES or total == 0:
        continue
    opp_wr[t1].append(w1 / total)  # t1's winrate vs t2
    opp_wr[t2].append(w2 / total)  # t2's winrate vs t1

avg_wr = {
    t: (float(np.mean(v)) if len(v) else np.nan)
    for t, v in opp_wr.items()
}

print("\nUnweighted avg winrate by opponent:")
for t in teams_in_data:
    v = avg_wr[t]
    print(f"  {t}: {'-' if np.isnan(v) else f'{v*100:.1f}%'}  (opponents={len(opp_wr[t])})")

# -------------------------
# Colors (yellow near 50%, green near 100%)
# -------------------------
YELLOW = np.array([0.98, 0.80, 0.10])
GREEN  = np.array([0.15, 0.70, 0.25])

def edge_color(winrate):
    t = np.clip((winrate - 0.5) / 0.5, 0.0, 1.0)
    rgb = YELLOW + (GREEN - YELLOW) * t
    return tuple(rgb.tolist())

# Node color from avg_wr (50%->yellow-ish, 100%->green-ish, <50%->orange/red)
def node_color_from_avg(v):
    if np.isnan(v):
        return (0.85, 0.85, 0.85)
    # map 0..1 into a red->yellow->green colormap
    cmap = plt.get_cmap("RdYlGn")
    return cmap(v)

# -------------------------
# Layout (compact, fits one screen)
# -------------------------
pos = nx.circular_layout(G)
for k in pos:
    pos[k] = pos[k] * 1.12

# -------------------------
# Draw
# -------------------------
fig, ax = plt.subplots(figsize=(11, 11))
ax.set_facecolor("white")
fig.patch.set_facecolor("white")

ax.set_title(
    "Top-10 directed matchup graph\n"
    "Arrow points WINNER → LOSER | Edge color: yellow≈50%, green≈100% | Node label shows unweighted avg winrate",
    fontsize=11
)

nodes = list(G.nodes())

# Node sizes: based on number of distinct opponents (not games)
node_sizes = []
node_colors = []
for n in nodes:
    node_sizes.append(1400 + 180 * len(opp_wr[n]))
    node_colors.append(node_color_from_avg(avg_wr[n]))

nx.draw_networkx_nodes(
    G, pos,
    nodelist=nodes,
    node_size=node_sizes,
    node_color=node_colors,
    edgecolors="#333333",
    linewidths=1.4,
    ax=ax
)

# Edges: thick, very visible arrows
for winner, loser, winrate, wins, total in edge_rows:
    col = edge_color(winrate)
    lw = 2.6 + 0.35 * min(total, 20)

    ax.annotate(
        "",
        xy=pos[loser],
        xytext=pos[winner],
        arrowprops=dict(
            arrowstyle="-|>",
            color=col,
            lw=lw,
            mutation_scale=26,
            shrinkA=26,
            shrinkB=26,
            connectionstyle="arc3,rad=0.18",
            alpha=0.95,
        ),
        zorder=3
    )

    # edge label
    x0, y0 = pos[winner]
    x1, y1 = pos[loser]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    ax.text(
        mx, my,
        f"{wins}/{total}  {winrate*100:.0f}%",
        ha="center", va="center",
        fontsize=7,
        color="#111",
        bbox=dict(boxstyle="round,pad=0.18", fc=col, ec="#333", lw=0.8, alpha=0.92),
        zorder=6
    )

# Node labels: team name + unweighted avg winrate
for n, (x, y) in pos.items():
    v = avg_wr[n]
    avg_txt = "-" if np.isnan(v) else f"{v*100:.1f}%"
    ax.text(
        x, y,
        f"{n}\navg {avg_txt}",
        ha="center", va="center",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#333", lw=1.0, alpha=0.95),
        zorder=10
    )

# Legend
legend_patches = [
    mpatches.Patch(facecolor=edge_color(0.50), edgecolor="#333", label="edge ~50%"),
    mpatches.Patch(facecolor=edge_color(0.70), edgecolor="#333", label="edge ~70%"),
    mpatches.Patch(facecolor=edge_color(1.00), edgecolor="#333", label="edge 100%"),
    mpatches.Patch(facecolor=node_color_from_avg(0.50), edgecolor="#333", label="node avg ~50%"),
    mpatches.Patch(facecolor=node_color_from_avg(0.80), edgecolor="#333", label="node avg ~80%"),
]
ax.legend(handles=legend_patches, loc="upper right", frameon=True)

ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUT_PATH, dpi=170, bbox_inches="tight")
print(f"\nSaved -> {OUT_PATH}")
plt.show()
