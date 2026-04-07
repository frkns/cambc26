# type: ignore
import os
import sys
import re
from datetime import datetime
from pathlib import Path
import subprocess
from collections import defaultdict, deque

HEADER_IMPORTS = [
    "from __future__ import annotations",
    *[line.rstrip("\n") for line in open("imports.ppy")]
]

SOURCE_DIRS = [Path("../Awubot"), Path("../Generated")]
OUTPUT_FILE = Path("../main.py")


def git_commit(message="pre-concat checkpoint"):
    pass
    # print("checkpointing...")
    # try:
    #     subprocess.run(["git", "add", "-A"], check=True)
    #     subprocess.run(["git", "commit", "-m", message], check=True)
    #     print("Git commit created successfully.")
    # except subprocess.CalledProcessError as e:
    #     print(f"Git commit failed: {e}", file=sys.stderr)


def get_bot_name() -> str:
    return OUTPUT_FILE.resolve().parent.name


def get_secondary_output() -> Path:
    """Derive /bots/<bot_name>/main.py from the resolved OUTPUT_FILE location."""
    resolved = OUTPUT_FILE.resolve()
    bot_name = resolved.parent.name
    project_root = resolved.parent.parent.parent
    secondary = project_root / "bots" / bot_name / "main.py"
    return secondary


def is_import_line(s: str) -> bool:
    stripped = s.strip()
    cond1 = stripped.startswith("import ") or stripped.startswith("from ")
    # cond2 = stripped.startswith("# ---=== IMPORT") or stripped.startswith("# ===--- IMPORT")
    cond2 = False
    return cond1 or cond2


def strip_leading_imports(lines: list[str]) -> list[str]:
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1

    in_imports = False

    while i < len(lines):
        stripped = lines[i].strip()

        if is_import_line(stripped):
            in_imports = True
            i += 1
        elif stripped == "" and in_imports:
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and is_import_line(lines[j].strip()):
                i = j
            else:
                i = j
                break
        else:
            break

    while i < len(lines) and lines[i].strip() == "":
        i += 1

    return lines[i:]


CLASS_RE = re.compile(r"^class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:")


def is_class_body_line(line: str) -> bool:
    return line.strip() == "" or line[0] in (" ", "\t", "#", "{")


def parse_classes(lines: list[str], filename: str):
    classes = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.strip() == "" or line.strip().startswith("#"):
            i += 1
            continue

        match = CLASS_RE.match(line)
        if not match:
            print(
                f"  WARNING [{filename}]: stray top-level line {i + 1}: {line.rstrip()}",
                file=sys.stderr,
            )
            i += 1
            continue

        name = match.group(1)
        bases_str = match.group(2)
        bases = (
            [b.strip() for b in bases_str.split(",") if b.strip()]
            if bases_str
            else []
        )

        class_lines = [line]
        i += 1
        while i < len(lines):
            if is_class_body_line(lines[i]):
                class_lines.append(lines[i])
                i += 1
            else:
                break

        while class_lines and class_lines[-1].strip() == "":
            class_lines.pop()

        classes.append((name, bases, class_lines))

    return classes


def toposort_classes(all_classes):
    name_set = {name for name, _, _ in all_classes}
    class_map = {name: (bases, lines) for name, bases, lines in all_classes}

    in_degree = {name: 0 for name in name_set}
    dependents = defaultdict(list)

    for name, bases, _ in all_classes:
        for base in bases:
            if base in name_set:
                in_degree[name] += 1
                dependents[base].append(name)

    queue = deque(sorted(n for n in name_set if in_degree[n] == 0))
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for dep in sorted(dependents[node]):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    if len(result) != len(name_set):
        remaining = name_set - set(result)
        print(f"WARNING: circular inheritance among: {remaining}", file=sys.stderr)
        for name, _, _ in all_classes:
            if name in remaining:
                result.append(name)

    return [(name, class_map[name][0], class_map[name][1]) for name in result]


def write_output(path: Path, content: str, label: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {label}: {path} ({len(content)} bytes)")


def build():
    py_files = []
    for source_dir in SOURCE_DIRS:
        if not source_dir.exists():
            print(f"  Skipping {source_dir} (not found)")
            continue
        found = sorted(source_dir.rglob("*.py"))
        print(f"  {source_dir}: {len(found)} files")
        py_files.extend((source_dir, path) for path in found)

    if not py_files:
        print(f"No .py files found in {SOURCE_DIRS}", file=sys.stderr)
        return

    all_classes = []
    for source_dir, path in py_files:
        rel = path.relative_to(source_dir)
        label = f"{source_dir.name}/{rel}"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            text = text.replace(f'# ---{""}=== IMPORT', '')
            text = text.replace(f'# ==={""}--- IMPORT', '')
            text = text.replace(f'# ---{""}===', '')
            text = text.replace(f'# ==={""}---', '')
            lines = text.splitlines(keepends=True)
        body = strip_leading_imports(lines)
        classes = parse_classes(body, label)
        names = [n for n, _, _ in classes]
        print(f"  {label}: {len(classes)} classes — {', '.join(names) or '(none)'}")
        if not classes and body:
            print(
                f"  WARNING [{label}]: has content but no classes",
                file=sys.stderr,
            )
        all_classes.extend(classes)

    print(f"\nTotal: {len(all_classes)} classes across {len(py_files)} files")

    seen = set()
    for name, _, _ in all_classes:
        if name in seen:
            print(f"  WARNING: duplicate class name: {name}", file=sys.stderr)
        seen.add(name)

    name_set = {n for n, _, _ in all_classes}
    any_inheritance = False
    for name, bases, _ in all_classes:
        internal = [b for b in bases if b in name_set]
        if internal:
            any_inheritance = True
            print(f"  {name} extends {', '.join(internal)}")
    if not any_inheritance:
        print("No inter-class inheritance — order doesn't matter")

    sorted_classes = toposort_classes(all_classes)

    bot_name = get_bot_name()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = [f"# {bot_name},  @ {timestamp} (local)\n\n"]
    for imp in HEADER_IMPORTS:
        parts.append(imp + "\n")
    parts.append("\n")

    for name, bases, lines in sorted_classes:
        parts.append(f"# {'=' * 60}\n")
        parts.append(f"# {name}\n")
        parts.append(f"# {'=' * 60}\n\n")
        parts.extend(lines)
        if lines and not lines[-1].endswith("\n"):
            parts.append("\n")
        parts.append("\n\n")

    content = "".join(parts)

    print()
    write_output(OUTPUT_FILE, content, "primary")

    secondary = get_secondary_output()
    write_output(secondary, content, "secondary")


if __name__ == "__main__":
    git_commit()
    build()
