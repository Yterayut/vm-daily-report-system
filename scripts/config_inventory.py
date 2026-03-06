#!/usr/bin/env python3
"""
Build config inventory and suggest safe decommission actions.
Default scope excludes archive/checkpoints/github_clean.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {".git", "archive", "checkpoints", "github_clean", "__pycache__", "output", "logs"}
CONFIG_SUFFIXES = {
    ".env", ".ini", ".conf", ".cfg", ".yaml", ".yml", ".json", ".service", ".timer"
}
CONFIG_EXACT = {
    ".env", ".env.example", ".env.prod.template", "new_crontab.txt", "run_daily_report.sh"
}

CORE_KEEP = {
    ".env",
    ".env.example",
    ".env.prod.template",
    "run_daily_report.sh",
    "scripts/prod_run_daily_report.sh",
    "scripts/phase5_test_gate.sh",
    ".github/workflows/phase5-test-gate.yml",
}

ARCHIVE_HINT_PATTERNS = (
    ".bak", ".bak2", ".backup", "_backup", "_old", "_broken", "emergency", "debug_", "test_"
)


@dataclass
class Item:
    path: str
    used_by: List[str]
    classification: str
    recommendation: str
    reason: str


def tracked_text_files() -> List[str]:
    cmd = ["git", "ls-files"]
    out = subprocess.check_output(cmd, cwd=ROOT, text=True)
    files = []
    for line in out.splitlines():
        p = ROOT / line
        if not p.exists() or not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".gz", ".woff", ".woff2", ".ttf"}:
            continue
        files.append(line)
    return files


def discover_configs() -> List[str]:
    items: List[str] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue

        name = p.name
        low = name.lower()
        if rel in CORE_KEEP:
            items.append(rel)
            continue
        if name in CONFIG_EXACT or name.startswith(".env"):
            items.append(rel)
            continue
        if p.suffix.lower() in CONFIG_SUFFIXES:
            items.append(rel)
            continue
        if "crontab" in low or "config" in low or "deploy" in low:
            if p.suffix in {".sh", ".txt", ""}:
                items.append(rel)
    return sorted(set(items))


def find_usage(target: str, haystack: List[str]) -> List[str]:
    target_name = Path(target).name
    used = []
    for file_rel in haystack:
        # skip self
        if file_rel == target:
            continue
        p = ROOT / file_rel
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if target in text or target_name in text:
            used.append(file_rel)
    return used[:15]


def classify(path: str, used_by: List[str]) -> Item:
    name = Path(path).name.lower()

    if path in CORE_KEEP:
        return Item(path, used_by, "active", "keep", "core runtime/gate file")

    if path.endswith(".service") or path.endswith(".timer"):
        return Item(path, used_by, "system", "keep", "systemd unit should be reviewed manually")

    if used_by:
        return Item(path, used_by, "referenced", "keep", "found references in code/scripts")

    if any(token in name for token in ARCHIVE_HINT_PATTERNS):
        return Item(path, used_by, "legacy_candidate", "archive", "backup/debug/emergency naming pattern")

    if name.startswith(".env"):
        return Item(path, used_by, "sensitive", "manual_review", "env-like file requires manual handling")

    return Item(path, used_by, "unknown", "manual_review", "no direct reference found")


def main() -> int:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    tracked = tracked_text_files()
    configs = discover_configs()

    result: List[Item] = []
    for cfg in configs:
        usage = find_usage(cfg, tracked)
        result.append(classify(cfg, usage))

    result = sorted(result, key=lambda x: (x.recommendation, x.path))

    json_path = OUT_DIR / f"config_inventory_{now}.json"
    md_path = OUT_DIR / f"config_inventory_{now}.md"

    payload: Dict[str, object] = {
        "generated_at": datetime.now().isoformat(),
        "total": len(result),
        "counts": {
            "keep": sum(1 for r in result if r.recommendation == "keep"),
            "archive": sum(1 for r in result if r.recommendation == "archive"),
            "manual_review": sum(1 for r in result if r.recommendation == "manual_review"),
        },
        "items": [asdict(r) for r in result],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Config Inventory",
        "",
        f"Generated: {payload['generated_at']}",
        f"Total: {payload['total']}",
        "",
        "## Summary",
        f"- keep: {payload['counts']['keep']}",
        f"- archive: {payload['counts']['archive']}",
        f"- manual_review: {payload['counts']['manual_review']}",
        "",
        "## Archive Candidates",
    ]
    for r in result:
        if r.recommendation == "archive":
            lines.append(f"- `{r.path}`: {r.reason}")

    lines.extend(["", "## Manual Review", ""])
    for r in result:
        if r.recommendation == "manual_review":
            lines.append(f"- `{r.path}`: {r.reason}")

    lines.extend(["", "## Keep", ""])
    for r in result:
        if r.recommendation == "keep":
            lines.append(f"- `{r.path}`: {r.reason}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(json_path))
    print(str(md_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
