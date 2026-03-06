#!/usr/bin/env python3
"""
Advanced config inventory with confidence-based decommission recommendations.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {
    ".git", "archive", "checkpoints", "github_clean", "__pycache__", "output", "logs", ".venv", "venv"
}
TEXT_SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".gz", ".woff", ".woff2", ".ttf", ".zip"
}

CORE_RUNTIME_KEEP = {
    ".env",
    ".env.example",
    ".env.prod.template",
    "run_daily_report.sh",
    "scripts/prod_run_daily_report.sh",
    "scripts/phase5_test_gate.sh",
    "scripts/config_inventory.py",
    "scripts/config_decommission.sh",
    ".github/workflows/phase5-test-gate.yml",
}

ENTRYPOINTS = {
    "daily_report.py",
    "mobile_api.py",
    "run_daily_report.sh",
    "scripts/prod_run_daily_report.sh",
    "scripts/phase5_test_gate.sh",
}

CONFIG_HINT_SUFFIXES = {
    ".env", ".ini", ".conf", ".cfg", ".yaml", ".yml", ".json", ".service", ".timer", ".txt"
}

LEGACY_TOKENS = (
    ".bak", ".bak2", ".backup", "_backup", "_old", "_broken", "emergency", "debug_", "test_", "_fix"
)

SAFE_ARCHIVE_SUFFIXES = (".bak", ".bak2", ".backup", ".old", ".orig")
SAFE_ARCHIVE_NAME_TOKENS = ("_backup", "_old", "_broken", "debug_", "emergency_")


@dataclass
class Item:
    path: str
    tracked: bool
    used_by: List[str]
    classification: str
    recommendation: str
    confidence: int
    reason: str


def _run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, text=True)


def tracked_files() -> Set[str]:
    out = _run(["git", "ls-files"])
    return {line.strip() for line in out.splitlines() if line.strip()}


def candidate_files() -> List[str]:
    files: List[str] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue

        name = p.name.lower()
        suffix = p.suffix.lower()

        # Keep broad because we want to classify then decide.
        if rel in CORE_RUNTIME_KEEP:
            files.append(rel)
            continue
        if name.startswith(".env"):
            files.append(rel)
            continue
        if suffix in CONFIG_HINT_SUFFIXES:
            files.append(rel)
            continue
        if any(tok in name for tok in ("config", "deploy", "crontab", "service", "monitor")) and suffix in {".sh", ".py", ".txt", ""}:
            files.append(rel)
            continue
        if any(tok in name for tok in LEGACY_TOKENS):
            files.append(rel)

    return sorted(set(files))


def searchable_text_files() -> List[str]:
    files = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_SKIP_SUFFIXES:
            continue
        files.append(p.relative_to(ROOT).as_posix())
    return files


def find_usage(target: str, corpus: List[str]) -> List[str]:
    t_name = Path(target).name
    used: List[str] = []
    for rel in corpus:
        if rel == target:
            continue
        p = ROOT / rel
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if target in text or t_name in text:
            used.append(rel)
    return sorted(set(used))[:20]


def classify(path: str, tracked: bool, used_by: List[str]) -> Item:
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()

    if path in CORE_RUNTIME_KEEP:
        return Item(path, tracked, used_by, "active", "keep", 100, "core runtime/gate file")

    if suffix in {".service", ".timer"}:
        return Item(path, tracked, used_by, "system", "manual_review", 90, "systemd unit should be reviewed manually")

    if used_by:
        if any(ep in used_by for ep in ENTRYPOINTS):
            return Item(path, tracked, used_by, "active", "keep", 95, "referenced by runtime entrypoint")
        return Item(path, tracked, used_by, "referenced", "keep", 80, "referenced by code/scripts")

    if name.startswith(".env"):
        return Item(path, tracked, used_by, "sensitive", "manual_review", 95, "env-like file requires manual review")

    if name.endswith(SAFE_ARCHIVE_SUFFIXES) or any(tok in name for tok in SAFE_ARCHIVE_NAME_TOKENS):
        return Item(path, tracked, used_by, "legacy", "archive_safe", 95, "legacy backup/debug pattern without references")

    if any(tok in name for tok in LEGACY_TOKENS):
        return Item(path, tracked, used_by, "legacy", "archive_review", 75, "legacy-like name but needs quick review")

    return Item(path, tracked, used_by, "unknown", "manual_review", 60, "no direct reference found")


def build_markdown(payload: Dict[str, object]) -> str:
    items = payload["items"]
    lines = [
        "# Config Inventory (Advanced)",
        "",
        f"Generated: {payload['generated_at']}",
        f"Total: {payload['total']}",
        "",
        "## Summary",
        f"- keep: {payload['counts']['keep']}",
        f"- archive_safe: {payload['counts']['archive_safe']}",
        f"- archive_review: {payload['counts']['archive_review']}",
        f"- manual_review: {payload['counts']['manual_review']}",
        "",
        "## Archive Safe",
    ]

    for r in items:
        if r["recommendation"] == "archive_safe":
            lines.append(f"- `{r['path']}` (conf={r['confidence']}): {r['reason']}")

    lines.extend(["", "## Archive Review", ""])
    for r in items:
        if r["recommendation"] == "archive_review":
            lines.append(f"- `{r['path']}` (conf={r['confidence']}): {r['reason']}")

    lines.extend(["", "## Manual Review", ""])
    for r in items:
        if r["recommendation"] == "manual_review":
            lines.append(f"- `{r['path']}` (conf={r['confidence']}): {r['reason']}")

    lines.extend(["", "## Keep", ""])
    for r in items:
        if r["recommendation"] == "keep":
            lines.append(f"- `{r['path']}` (conf={r['confidence']}): {r['reason']}")

    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    tracked = tracked_files()
    candidates = candidate_files()
    corpus = searchable_text_files()

    result: List[Item] = []
    for path in candidates:
        usage = find_usage(path, corpus)
        result.append(classify(path, path in tracked, usage))

    result = sorted(result, key=lambda x: (x.recommendation, -x.confidence, x.path))

    payload: Dict[str, object] = {
        "generated_at": datetime.now().isoformat(),
        "total": len(result),
        "counts": {
            "keep": sum(1 for r in result if r.recommendation == "keep"),
            "archive_safe": sum(1 for r in result if r.recommendation == "archive_safe"),
            "archive_review": sum(1 for r in result if r.recommendation == "archive_review"),
            "manual_review": sum(1 for r in result if r.recommendation == "manual_review"),
        },
        "items": [asdict(r) for r in result],
    }

    json_path = OUT_DIR / f"config_inventory_{now}.json"
    md_path = OUT_DIR / f"config_inventory_{now}.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    print(str(json_path))
    print(str(md_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
