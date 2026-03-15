#!/usr/bin/env bash
# Build Integrity Verification — OWASP A08
# Nexus Autonomous Agent Ecosystem
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PASS=0; FAIL=0

check() {
  if [ "$1" = "true" ]; then echo "  [PASS] $2"; PASS=$((PASS+1))
  else echo "  [FAIL] $2: $3"; FAIL=$((FAIL+1)); fi
}

echo "=== Nexus Autonomous — Integrity Verification ==="

# 1. Python version
PY_OK=$(python3 -c "import sys; print('true' if sys.version_info >= (3,11) else 'false')" 2>/dev/null || echo "false")
check "$PY_OK" "Python >= 3.11" "$(python3 --version 2>/dev/null)"

# 2. Base agent exists
check "$([ -f agentes/base_agente.py ] && echo true || echo false)" "base_agente.py exists" "Missing"

# 3. All 20 agents compile
AGENT_COUNT=$(find agentes -name "*.py" -not -name "__init__.py" | wc -l | tr -d ' ')
COMPILE_OK=$(python3 -c "
import py_compile, os, glob
files = [f for f in glob.glob('agentes/**/*.py', recursive=True) if '__init__' not in f]
ok = sum(1 for f in files if not py_compile.compile(f, doraise=False) is None or True)
try:
  [py_compile.compile(f, doraise=True) for f in files]
  print(len(files))
except: print(0)
" 2>/dev/null || echo "0")
check "$([ "$COMPILE_OK" -ge 20 ] && echo true || echo false)" "$AGENT_COUNT agents compile" "Only $COMPILE_OK compile"

# 4. No secrets in source
SECRETS=$(grep -r "sk-[a-zA-Z0-9]\{20,\}\|password\s*=\s*['\"][^'\"]\{8,\}" agentes/ --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
check "$([ "$SECRETS" -eq 0 ] && echo true || echo false)" "No hardcoded secrets in agents" "$SECRETS found"

# 5. CLAUDE.md exists
check "$([ -f CLAUDE.md ] && echo true || echo false)" "CLAUDE.md exists" "Missing"

# 6. Dashboard exists
check "$([ -f dashboard.py ] && echo true || echo false)" "dashboard.py exists" "Missing"

# 7. RAG engine exists
check "$([ -f rag_engine.py ] && echo true || echo false)" "rag_engine.py exists" "Missing"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
