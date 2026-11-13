#!/usr/bin/env python3
"""Inventory and rank Claude skills against a task.

Reads the frontmatter of every SKILL.md it can find and scores each skill
against the keywords given. Standard library only.

Sources scanned (installed):
  user      <config>/skills/*/SKILL.md
  project   .claude/skills/*/SKILL.md, walking up from the working directory
  plugin    install paths listed in <config>/plugins/installed_plugins.json
  account   <config>/plugins/synced/*/* (plugins synced from the claude.ai account)
  extra     any folder passed with --root

Sources scanned with --available (not installed):
  marketplace   plugins in <config>/plugins/marketplaces/* that are not installed
  directory     listings in <config>/plugins/plugin-directory-cache-v2.json

Usage:
  skill_inventory.py pdf form fill            rank installed skills
  skill_inventory.py pdf form --deep          also match inside the skill body
  skill_inventory.py pdf form --available     rank things that could be installed
  skill_inventory.py                          counts per source
  skill_inventory.py --all                    every installed skill, one line each
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {".trash", "node_modules", ".git", "configs", "inactive-skills", ".cursor"}
STOPWORDS = set(
    "a an and are as at be by can do for from has have help how i in into is it "
    "me my need of on or skill skills task that the this to use want with you your".split()
)
W_NAME, W_DESC, W_BODY = 5, 3, 1


def config_dir() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env) if env else Path.home() / ".claude"


def tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", text.lower().replace("_", " ")) if t]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_skill(path: Path) -> tuple[dict, str]:
    """Return (frontmatter fields, body). Handles plain, quoted and block scalars."""
    text = read_text(path).lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n")
    end = next((i for i in range(1, len(parts)) if parts[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fields: dict[str, str] = {}
    key = None
    for line in parts[1:end]:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value[:1] in ("|", ">"):
                value = ""
            fields[key] = value
        elif key and line[:1] in (" ", "\t") and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    for k, v in fields.items():
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            fields[k] = v[1:-1]
    return fields, "\n".join(parts[end + 1:])


def find_skill_files(root: Path, max_depth: int = 4) -> list[Path]:
    found: list[Path] = []
    if not root.is_dir():
        return found
    base = len(root.parts)
    for current, dirs, files in os.walk(root):
        depth = len(Path(current).parts) - base
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and depth < max_depth]
        if "SKILL.md" in files:
            found.append(Path(current) / "SKILL.md")
            dirs[:] = []
    return found


def plugin_name(plugin_root: Path, fallback: str) -> str:
    try:
        data = json.loads(read_text(plugin_root / ".claude-plugin" / "plugin.json"))
        return data.get("name") or fallback
    except (ValueError, AttributeError):
        return fallback


def make_entry(path: Path, source: str, prefix: str = "", installed: bool = True) -> dict:
    fields, body = parse_skill(path)
    folder = path.parent.name
    return {
        "invoke": f"{prefix}:{folder}" if prefix else folder,
        "name": fields.get("name") or folder,
        "description": " ".join(
            x for x in (fields.get("description"), fields.get("when_to_use")) if x
        ),
        "sources": [source],
        "installed": installed,
        "path": str(path),
        "_body": body,
    }


def collect_installed(cfg: Path, cwd: Path, extra_roots: list[str]) -> list[dict]:
    entries: list[dict] = []
    for f in find_skill_files(cfg / "skills", max_depth=2):
        entries.append(make_entry(f, "user"))

    seen_project: set[Path] = set()
    for folder in [cwd, *cwd.parents]:
        root = folder / ".claude" / "skills"
        if root.resolve() == (cfg / "skills").resolve() or root in seen_project:
            continue
        seen_project.add(root)
        for f in find_skill_files(root, max_depth=2):
            entries.append(make_entry(f, "project"))

    try:
        installed = json.loads(read_text(cfg / "plugins" / "installed_plugins.json"))
        plugins = installed.get("plugins", {})
    except (ValueError, AttributeError):
        plugins = {}
    for plugin_id, installs in plugins.items():
        short = plugin_id.split("@")[0]
        for inst in installs if isinstance(installs, list) else []:
            root = Path(inst.get("installPath", ""))
            for f in find_skill_files(root / "skills"):
                entries.append(make_entry(f, f"plugin:{plugin_id}", short))

    synced = cfg / "plugins" / "synced"
    if synced.is_dir():
        for bucket in synced.iterdir():
            if not bucket.is_dir() or bucket.name.startswith("."):
                continue
            for plugin_root in bucket.iterdir():
                if not plugin_root.is_dir():
                    continue
                name = plugin_name(plugin_root, plugin_root.name)
                for f in find_skill_files(plugin_root / "skills"):
                    entries.append(make_entry(f, f"account:{name}", name))

    for raw in extra_roots:
        for f in find_skill_files(Path(raw).expanduser()):
            entries.append(make_entry(f, f"extra:{raw}"))
    return entries


def collect_available(cfg: Path, installed: list[dict]) -> list[dict]:
    have = {e["invoke"].split(":")[0].lower() for e in installed if ":" in e["invoke"]}
    entries: list[dict] = []
    markets = cfg / "plugins" / "marketplaces"
    if markets.is_dir():
        for market in markets.iterdir():
            if not market.is_dir():
                continue
            for f in find_skill_files(market, max_depth=6):
                rel = f.relative_to(market).parts
                if "skills" not in rel:
                    continue
                idx = rel.index("skills")
                plugin = rel[idx - 1] if idx > 0 else market.name
                if plugin.lower() in have:
                    continue
                e = make_entry(f, f"marketplace:{market.name}", plugin, installed=False)
                e["install"] = f"claude plugin install {plugin}@{market.name}"
                entries.append(e)
    try:
        cache = json.loads(read_text(cfg / "plugins" / "plugin-directory-cache-v2.json"))
        listings = cache.get("listings", [])
    except (ValueError, AttributeError):
        listings = []
    for item in listings:
        name = item.get("name") or ""
        if not name or name.lower() in have:
            continue
        repo = ((item.get("source") or {}).get("repository") or {}).get("url", "")
        review = ((item.get("checks") or {}).get("review") or {})
        reviewer = (review.get("by") or {}).get("type", "")
        entries.append({
            "invoke": name,
            "name": name,
            "description": item.get("summary") or "",
            "sources": ["directory"],
            "installed": False,
            "path": repo,
            "review": f"{review.get('state', 'unknown')}" + (f" by {reviewer}" if reviewer else ""),
            "_body": "",
        })
    return entries


def merge_duplicates(entries: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for e in entries:
        key = (e["name"].lower(), re.sub(r"\W+", "", e["description"].lower())[:200])
        if key in merged:
            first = merged[key]
            first["sources"] = sorted(set(first["sources"] + e["sources"]))
            first.setdefault("also", []).append(e["invoke"])
        else:
            merged[key] = e
    return list(merged.values())


def word_hit(query: str, words: set[str]) -> bool:
    if query in words:
        return True
    if len(query) < 4:
        return False
    return any(len(w) >= 4 and (w.startswith(query) or query.startswith(w)) for w in words)


def score(entry: dict, query: list[str], deep: bool) -> None:
    name_words = set(tokens(entry["name"] + " " + entry["invoke"]))
    desc_words = set(tokens(entry["description"]))
    body_words = set(tokens(entry["_body"])) if deep else set()
    total, matched = 0, []
    for q in query:
        best = 0
        if word_hit(q, name_words):
            best = W_NAME
        elif word_hit(q, desc_words):
            best = W_DESC
        elif deep and word_hit(q, body_words):
            best = W_BODY
        if best:
            matched.append(q)
            total += best
    entry["score"], entry["matched"] = total, matched


def shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory and rank Claude skills against a task.")
    ap.add_argument("keywords", nargs="*", help="task keywords, synonyms included")
    ap.add_argument("--deep", action="store_true", help="also match inside the skill body")
    ap.add_argument("--available", action="store_true",
                    help="rank skills and plugins that are NOT installed")
    ap.add_argument("--root", action="append", default=[], help="extra folder to scan")
    ap.add_argument("--cwd", default=os.getcwd(), help="project folder (default: current)")
    ap.add_argument("--limit", type=int, default=12, help="results to show (default 12)")
    ap.add_argument("--all", action="store_true", help="list every skill, one line each")
    ap.add_argument("--json", action="store_true", help="JSON output with full descriptions")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    cfg = config_dir()
    installed = collect_installed(cfg, Path(args.cwd).resolve(), args.root)
    pool = collect_available(cfg, installed) if args.available else installed
    pool = merge_duplicates(pool)

    counts: dict[str, int] = {}
    for e in pool:
        for s in e["sources"]:
            kind = s.split(":")[0]
            counts[kind] = counts.get(kind, 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "nothing found"
    scope = "not-installed candidates" if args.available else "installed skills"

    query = [t for t in tokens(" ".join(args.keywords)) if t not in STOPWORDS]
    if query:
        for e in pool:
            score(e, query, args.deep)
        results = sorted(
            (e for e in pool if e["score"] > 0),
            key=lambda e: (-e["score"], -len(e["matched"]), e["invoke"].lower()),
        )[: args.limit]
    elif args.all:
        results = sorted(pool, key=lambda e: e["invoke"].lower())
    else:
        results = []

    if args.json:
        clean = [{k: v for k, v in e.items() if not k.startswith("_")} for e in results]
        json.dump({"scope": scope, "counts": counts, "query": query, "results": clean},
                  sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0

    print(f"Scanned {len(pool)} {scope} ({summary}).")
    if not query and not args.all:
        print("Give keywords to rank them, or --all to list every one.")
        return 0
    if query:
        print(f"Query: {' '.join(query)}" + ("  [deep]" if args.deep else ""))
    if not results:
        print("No matches. Try synonyms, another language, --deep, or --available.")
        print("Account-only skills are not on disk: check them with the ListSkills tool.")
        return 0
    for i, e in enumerate(results, 1):
        if args.all and not query:
            print(f"{e['invoke']}  [{', '.join(e['sources'])}]  {shorten(e['description'], 110)}")
            continue
        hit = f"{len(e['matched'])}/{len(query)}: {', '.join(e['matched'])}"
        print(f"\n{i}. {e['invoke']}  [score {e['score']}, matched {hit}]")
        print(f"   source: {', '.join(e['sources'])}"
              + (f"  | also as: {', '.join(e['also'])}" if e.get("also") else ""))
        print(f"   {shorten(e['description'], 320) or '(no description)'}")
        if e.get("install"):
            print(f"   install: {e['install']}")
        if e.get("review"):
            print(f"   review: {e['review']}")
        print(f"   {e['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
