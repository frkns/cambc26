import subprocess
import time
import os
import random
import re
import uuid
import webbrowser
import argparse

def getMaps():
    return list(filter(lambda x: not x.startswith("~"), map(lambda x: os.path.splitext(os.path.basename(x))[0], os.listdir("maps"))))

def runMatch(a, b, m, verbose=False):
    print(f"Running {a} vs {b} on {m}...")

    replayName = os.path.join("matches", f"{a}-vs-{b}-on-{m}-{time.time_ns()}.replay26")

    startTime = time.time()
    output = subprocess.run(f"cambc run --replay {replayName} {a} {b} {os.path.join("maps", m+".map26")}", capture_output=True, text=True, check=True, shell=True)
    totalTime = time.time() - startTime

    # # Open the replay
    # p = subprocess.Popen(f"cambc watch {replayName}")

    # time.sleep(3)

    # p.terminate()
    # p.wait()

    lines = output.stdout.splitlines()
    if verbose:
        print(lines)
    for line in lines[::-1]:
        if ("Winner" in line):
            winLine = line
            break
    else:
        raise Exception("Couldn't find win line among: " + lines)

    if verbose:
        print(winLine)

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
        print(f"{winner.upper()} wins!")

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

    print(f"Match complete in {totalTime:.1f}s ({winnerName} ({winner}) wins) [Titanium mined: {a}={titaniumA:,}, {b}={titaniumB:,}, margin={abs(titaniumA-titaniumB):,}]")

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

def generateOutput(aWins, bWins, mapValues, aName="?", bName="?"):
    ap = aWins / (aWins + bWins)
    bp = bWins / (aWins + bWins)

    u = str(uuid.uuid4())
    if not os.path.exists("tests"):
        os.mkdir("tests")
    with open(os.path.join("tests", u + ".html"), "w") as file:
        file.write(
f"""
<!DOCTYPE html>
<html>
    <head>
        <title> Battlecode Test {u} </title>
    </head>
    <body>
        <h3>{u}</h3>
        <div style="display: flex; flex-direction: row">
            <div style="margin: 50px">
                <h1> A {aName} wins </h1>
                <h3> {aWins} ({(ap*100):.0f}%) </h3>
            </div>

            <div style="margin: 50px">
                <h1> B {bName} wins </h1>
                <h3> {bWins} ({(bp*100):.0f}%) </h3>
            </div>
        </div>

        <table>
            <tr>
                <th> Map </th>
                <th> A wins </th>
                <th> B wins </th>
                <th> Average time </th>
                <th> Avg Titanium A </th>
                <th> Avg Titanium B </th>
            </tr>
            {"\n".join(
                list(map(lambda mv:
                f"""
            <tr>
                <td>{mv[0]}</td>
                <td>{mv[1]}</td>
                <td>{mv[2]}</td>
                <td>{mv[3]:.1f}s</td>
                <td>{mv[4]:,.0f}</td>
                <td>{mv[5]:,.0f}</td>
            </tr>
                """, mapValues))
            )}
        </table>
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

    args = parser.parse_args()

    if args.maps and len(args.maps) == 1 and args.maps[0].isnumeric():
        maps = random.sample(getMaps(), int(args.maps[0]))
    elif args.maps:
        maps = args.maps
    else:
        maps = getMaps()
    teamA = args.teamA
    teamB = args.teamB
    aWins, bWins, mapValues = runTourney(teamA, teamB, maps, verbose=args.verbose)
    generateOutput(aWins, bWins, mapValues, aName=teamA, bName=teamB)
