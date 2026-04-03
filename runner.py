import subprocess
import time
import os
import random
import re
import uuid
import webbrowser
import argparse
import json
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Thread-safe printing lock
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)

def getMaps():
    return list(filter(lambda x: not x.startswith("~"), map(lambda x: os.path.splitext(os.path.basename(x))[0], os.listdir("maps"))))

def runMatch(a, b, m, verbose=False):
    safe_print(f"Running {a} vs {b} on {m}...")

    replayName = os.path.join("matches", f"{a}-vs-{b}-on-{m}-{time.time_ns()}.replay26")

    command = f"cambc run --replay {replayName} {a} {b} {os.path.join('maps', m + '.map26')}"
    startTime = time.time()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
    try:
        output, _ = proc.communicate()
    except KeyboardInterrupt:
        safe_print("Keyboard interrupt received, terminating active match process...")
        proc.kill()
        proc.wait()
        raise
    finally:
        totalTime = time.time() - startTime

    if proc.returncode != 0:
        safe_print(f"Match process returned code {proc.returncode}. Output:\n{output}")
        raise subprocess.CalledProcessError(proc.returncode, command, output=output)


    # # Open the replay
    # p = subprocess.Popen(f"cambc watch {replayName}")

    # time.sleep(3)

    # p.terminate()
    # p.wait()

    lines = output.splitlines()
    if verbose:
        safe_print(lines)
    for line in lines[::-1]:
        if ("Winner" in line):
            winLine = line
            break
    else:
        raise Exception("Couldn't find win line among: " + lines)

    if verbose:
        safe_print(winLine)

    if a in winLine and b in winLine:
        if len(a) > len(b):
            winner = "a"
        else:
            winner = "b"
    elif a in winLine:
        winner = "a"
    elif b in winLine:
        winner = "b"
    else:
        raise Exception("Invalid win line: " + winLine)

    if verbose:
        safe_print(f"{winner.upper()} wins!")

    winnerName = a if winner == "a" else b

    # Extract titanium mined for each team
    titaniumA = 0
    titaniumB = 0
    for line in lines:
        if "Titanium" in line and "mined" in line:
            mined = re.findall(r'(\d+) mined', line)
            if len(mined) >= 2:
                titaniumA = int(mined[0])
                titaniumB = int(mined[1])
            break

    safe_print(f"Match complete in {totalTime:.1f}s ({winnerName} ({winner}) wins) [Titanium mined: {a}={titaniumA:,}, {b}={titaniumB:,}, margin={abs(titaniumA-titaniumB):,}]")

    return winner, totalTime, titaniumA, titaniumB

def runTourney(a, b, maps, verbose=False):
    aWins = 0
    bWins = 0
    mapValues = []
    matchNum = 1
    totalMatches = len(maps)*2
    for m in maps:
        # [map, aWins, bWins, avgTime, avgTitaniumA, avgTitaniumB]
        mapValues.append([m, 0, 0, 0, 0, 0])

        print(f"Match {matchNum}/{totalMatches}")
        matchNum += 1

        winner, t, titA, titB = runMatch(a, b, m, verbose)
        if winner == "a":
            aWins += 1
            mapValues[-1][1] += 1
        else:
            bWins += 1
            mapValues[-1][2] += 1

        mapValues[-1][3] += t/2
        mapValues[-1][4] += titA / 2
        mapValues[-1][5] += titB / 2

        print(f"Match {matchNum}/{totalMatches}")
        matchNum += 1

        winner, t, titA, titB = runMatch(b, a, m, verbose)
        if winner == "b":
            aWins += 1
            mapValues[-1][1] += 1
        else:
            bWins += 1
            mapValues[-1][2] += 1

        mapValues[-1][3] += t/2
        # When b,a order: titA is b's titanium, titB is a's titanium
        mapValues[-1][4] += titB / 2
        mapValues[-1][5] += titA / 2

    return aWins, bWins, mapValues

def runTourneyParallel(a, b, maps, parallel_count=4, verbose=False):
    """Run tournament with parallel match execution"""
    aWins = 0
    bWins = 0
    mapValues = []
    totalMatches = len(maps) * 2
    completed = 0
    completed_lock = threading.Lock()
    
    # Initialize map values
    for m in maps:
        mapValues.append([m, 0, 0, 0, 0, 0])
    
    # Create a mapping from map index to results
    results_map = [{} for _ in range(len(maps))]
    results_lock = threading.Lock()
    
    def run_and_track_match(match_info):
        """Run a single match and track results"""
        nonlocal completed, aWins, bWins
        
        map_idx, m, teamA, teamB, is_reversed = match_info
        
        try:
            winner, elapsed, titA, titB = runMatch(teamA, teamB, m, verbose)
            
            with results_lock:
                if is_reversed:
                    # When reversed (b, a): titA is b's, titB is a's
                    results_map[map_idx][f"match_{len(results_map[map_idx])}"] = {
                        "winner": winner,
                        "time": elapsed,
                        "titaniumA": titB,  # a's titanium
                        "titaniumB": titA,  # b's titanium
                        "reversed": True
                    }
                else:
                    results_map[map_idx][f"match_{len(results_map[map_idx])}"] = {
                        "winner": winner,
                        "time": elapsed,
                        "titaniumA": titA,
                        "titaniumB": titB,
                        "reversed": False
                    }
            
            with completed_lock:
                completed += 1
                safe_print(f"[{completed}/{totalMatches}] Completed {teamA} vs {teamB} on {m}")
        except Exception as e:
            safe_print(f"ERROR in match {teamA} vs {teamB} on {m}: {str(e)}")
            raise
    
    # Create list of all matches to run
    matches_to_run = []
    for map_idx, m in enumerate(maps):
        matches_to_run.append((map_idx, m, a, b, False))
        matches_to_run.append((map_idx, m, b, a, True))
    
    # Run matches in parallel
    safe_print(f"Starting parallel tournament with {parallel_count} workers ({totalMatches} total matches)...")
    executor = ThreadPoolExecutor(max_workers=parallel_count)
    futures = [executor.submit(run_and_track_match, match) for match in matches_to_run]
    try:
        for future in as_completed(futures):
            future.result()  # This will raise if there was an exception
    except KeyboardInterrupt:
        safe_print("KeyboardInterrupt detected; shutting down parallel tournament...")
        for f in futures:
            f.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        executor.shutdown(wait=True)

    
    # Aggregate results from results_map
    for map_idx, m in enumerate(maps):
        map_results = results_map[map_idx]
        for match_key in sorted(map_results.keys()):
            result = map_results[match_key]
            winner = result["winner"]
            elapsed = result["time"]
            titA = result["titaniumA"]
            titB = result["titaniumB"]
            
            if winner == "a":
                aWins += 1
                mapValues[map_idx][1] += 1
            else:
                bWins += 1
                mapValues[map_idx][2] += 1
            
            mapValues[map_idx][3] += elapsed / 2
            mapValues[map_idx][4] += titA / 2
            mapValues[map_idx][5] += titB / 2
    
    safe_print(f"\nTournament complete! Final results: {a} {aWins}-{bWins} {b}")
    return aWins, bWins, mapValues

def generateOutput(aWins, bWins, mapValues, aName="?", bName="?"):
    ap = aWins / (aWins + bWins)
    bp = bWins / (aWins + bWins)

    # Calculate additional stats
    totalMatches = aWins + bWins
    totalTitaniumA = sum(mv[4] for mv in mapValues)
    totalTitaniumB = sum(mv[5] for mv in mapValues)
    avgTitaniumDiff = abs(totalTitaniumA - totalTitaniumB) / len(mapValues) if mapValues else 0
    avgMatchTime = sum(mv[3] for mv in mapValues) / len(mapValues) if mapValues else 0

    winner = aName if aWins > bWins else bName
    winnerColor = "#2ecc71" if aWins > bWins else "#e74c3c"
    loserColor = "#e74c3c" if aWins > bWins else "#2ecc71"

    u = str(uuid.uuid4())
    if not os.path.exists("tests"):
        os.mkdir("tests")
    with open(os.path.join("tests", u + ".html"), "w", encoding="utf-8") as file:
        file.write(
f"""
<!DOCTYPE html>
<html>
    <head>
        <title>Battlecode Test {u}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .header p {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .scoreboard {{
                display: flex;
                justify-content: space-around;
                padding: 40px 20px;
                background: #f8f9fa;
                border-bottom: 2px solid #ecf0f1;
            }}
            .score-card {{
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                flex: 1;
                margin: 0 15px;
                background: white;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }}
            .score-card.winner {{
                background: {winnerColor};
                color: white;
                transform: scale(1.05);
            }}
            .score-card.loser {{
                background: {loserColor};
                color: white;
                opacity: 0.8;
            }}
            .score-card h2 {{
                font-size: 24px;
                margin-bottom: 10px;
            }}
            .score-card .team-name {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            .score-card .wins {{
                font-size: 36px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .score-card .percentage {{
                font-size: 16px;
                opacity: 0.9;
            }}
            .stats-section {{
                padding: 30px;
                background: #f8f9fa;
                border-bottom: 2px solid #ecf0f1;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .stat-box {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}
            .stat-box label {{
                display: block;
                font-size: 12px;
                color: #7f8c8d;
                text-transform: uppercase;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .stat-box .value {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .table-section {{
                padding: 30px;
            }}
            .table-section h2 {{
                margin-bottom: 20px;
                color: #2c3e50;
                font-size: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}
            thead {{
                background: #34495e;
                color: white;
            }}
            th {{
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            td {{
                padding: 15px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            tr:last-child td {{
                border-bottom: none;
            }}
            .map-name {{
                font-weight: 600;
                color: #2c3e50;
            }}
            .win-cell {{
                font-weight: bold;
            }}
            .win-a {{
                color: #2ecc71;
            }}
            .win-b {{
                color: #e74c3c;
            }}
            .neutral {{
                color: #95a5a6;
            }}
            .titanium {{
                font-family: 'Courier New', monospace;
                color: #3498db;
            }}
            .time {{
                color: #9b59b6;
                font-family: 'Courier New', monospace;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #7f8c8d;
                font-size: 12px;
                border-top: 1px solid #ecf0f1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚔️ Battlecode Tournament Results</h1>
                <p>Session ID: {u}</p>
            </div>

            <div class="scoreboard">
                <div class="score-card winner">
                    <div class="team-name">{aName}</div>
                    <div class="wins">{aWins}</div>
                    <div class="percentage">{(ap*100):.1f}%</div>
                </div>
                <div class="score-card loser">
                    <div class="team-name">{bName}</div>
                    <div class="wins">{bWins}</div>
                    <div class="percentage">{(bp*100):.1f}%</div>
                </div>
            </div>

            <div class="stats-section">
                <h2>Tournament Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <label>Total Matches</label>
                        <div class="value">{totalMatches}</div>
                    </div>
                    <div class="stat-box">
                        <label>Avg Match Time</label>
                        <div class="value">{avgMatchTime:.1f}s</div>
                    </div>
                    <div class="stat-box">
                        <label>Total Titanium {aName}</label>
                        <div class="value">{totalTitaniumA:,.0f}</div>
                    </div>
                    <div class="stat-box">
                        <label>Total Titanium {bName}</label>
                        <div class="value">{totalTitaniumB:,.0f}</div>
                    </div>
                    <div class="stat-box">
                        <label>Avg Titanium Diff</label>
                        <div class="value">{avgTitaniumDiff:,.0f}</div>
                    </div>
                    <div class="stat-box">
                        <label>Map Count</label>
                        <div class="value">{len(mapValues)}</div>
                    </div>
                </div>
            </div>

            <div class="table-section">
                <h2>Results by Map</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Map</th>
                            <th>{aName} Wins</th>
                            <th>{bName} Wins</th>
                            <th>Win Rate</th>
                            <th>Avg Time</th>
                            <th>Avg Titanium {aName}</th>
                            <th>Avg Titanium {bName}</th>
                            <th>Titanium Diff</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"\n".join(
                            list(map(lambda mv:
                            f"""
                        <tr>
                            <td class="map-name">{mv[0]}</td>
                            <td class="win-cell win-a">{mv[1]}</td>
                            <td class="win-cell win-b">{mv[2]}</td>
                            <td class="neutral">{(mv[1]/(mv[1]+mv[2])*100) if mv[1]+mv[2] > 0 else 0:.1f}%</td>
                            <td class="time">{mv[3]:.1f}s</td>
                            <td class="titanium">{mv[4]:,.0f}</td>
                            <td class="titanium">{mv[5]:,.0f}</td>
                            <td class="titanium">±{abs(mv[4] - mv[5]):,.0f}</td>
                        </tr>
                            """, mapValues))
                        )}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
</html>
""")
    webbrowser.open(f"file:///{os.path.abspath(os.path.join("tests", u + ".html"))}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("runner.py", description="Run batch matches between two Battlecode bots", epilog="Example: python %(prog)s rush turtle 3")

    parser.add_argument("teamA", help="Name of team A bot")
    parser.add_argument("teamB", help="Name of team B bot")
    parser.add_argument("maps", nargs="*", help="Map names to play on, or a single number to randomly sample that many maps (default: all maps)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
    parser.add_argument("-p", "--parallel", type=int, default=1, metavar="N", help="Number of matches to run in parallel (default: 1, sequential)")

    args = parser.parse_args()

    if args.maps and len(args.maps) == 1 and args.maps[0].isnumeric():
        maps = random.sample(getMaps(), int(args.maps[0]))
    elif args.maps:
        maps = args.maps
    else:
        maps = getMaps()
    teamA = args.teamA
    teamB = args.teamB

    try:
        if args.parallel > 1:
            aWins, bWins, mapValues = runTourneyParallel(teamA, teamB, maps, parallel_count=args.parallel, verbose=args.verbose)
        else:
            aWins, bWins, mapValues = runTourney(teamA, teamB, maps, verbose=args.verbose)

        generateOutput(aWins, bWins, mapValues, aName=teamA, bName=teamB)
    except KeyboardInterrupt:
        safe_print("\nExecution interrupted by user (Ctrl+C). Exiting cleanly.")
        sys.exit(1)

