#!/usr/bin/env python3
"""
Incident Monitor — Nexus Autonomous
ISO 27001 A.5.25 — Automated detection and alerting

Checks:
- Agent communication health (stale status files)
- Log file anomalies (error spikes)
- RAG store integrity
- Disk usage of data directories

Run via cron every 5 minutes: python3 scripts/incident-monitor.py
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMUNICACAO = ROOT / "comunicacao"
LOG_FILE = ROOT / "log_execucao.md"
RAG_STORE = ROOT / "inteligencia" / "rag_store"

alerts = []

def check(name, condition, severity="P3", detail=""):
    if not condition:
        alerts.append({"severity": severity, "type": name, "detail": detail})

# 1. Agent status freshness (stale > 24h = warning)
if COMUNICACAO.exists():
    now = time.time()
    for agent_dir in COMUNICACAO.iterdir():
        if not agent_dir.is_dir():
            continue
        status_file = agent_dir / "status.md"
        if status_file.exists():
            age_hours = (now - status_file.stat().st_mtime) / 3600
            if age_hours > 24:
                check(f"STALE_AGENT_{agent_dir.name}", False, "P3",
                      f"{agent_dir.name} status not updated in {age_hours:.0f}h")

# 2. Log file size (> 10MB = warning)
if LOG_FILE.exists():
    size_mb = LOG_FILE.stat().st_size / (1024 * 1024)
    check("LOG_SIZE", size_mb < 10, "P3", f"log_execucao.md is {size_mb:.1f}MB")

# 3. Log error spike (> 50 errors in last section)
if LOG_FILE.exists():
    content = LOG_FILE.read_text(encoding="utf-8", errors="ignore")
    error_count = content.lower().count("erro")
    check("LOG_ERRORS", error_count < 50, "P2", f"{error_count} error mentions in log")

# 4. RAG store integrity
if RAG_STORE.exists():
    chunks_file = RAG_STORE / "rag_chunks.json"
    if chunks_file.exists():
        try:
            data = json.loads(chunks_file.read_text(encoding="utf-8"))
            check("RAG_INTEGRITY", isinstance(data, list), "P2", "rag_chunks.json is not a valid array")
        except json.JSONDecodeError:
            check("RAG_CORRUPT", False, "P1", "rag_chunks.json is corrupted")

# 5. Disk usage of data directories
total_size = 0
for dirpath, _, filenames in os.walk(ROOT):
    if "node_modules" in dirpath or ".git" in dirpath:
        continue
    for f in filenames:
        total_size += os.path.getsize(os.path.join(dirpath, f))
total_mb = total_size / (1024 * 1024)
check("DISK_USAGE", total_mb < 500, "P3", f"Total size {total_mb:.0f}MB")

# Output
now_str = datetime.now().isoformat()
if not alerts:
    print(f"[MONITOR] {now_str} — All clear. No incidents detected.")
else:
    print(f"[MONITOR] {now_str} — {len(alerts)} ALERT(S):")
    for a in alerts:
        print(f"  [{a['severity']}] {a['type']}: {a['detail']}")
    exit(1)
