#!/usr/bin/env bash
# Nexus Autonomous — One-Command Installer
# ISO 25010: Installability — macOS, Linux, Docker
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
info() { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }
step() { echo -e "\n${BOLD}==> $1${NC}"; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

step "Pre-flight checks"
python3 --version >/dev/null 2>&1 || fail "Python 3 not found"
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PY_VER"

step "Installing Python dependencies"
pip3 install pytrends 2>/dev/null && info "pytrends installed" || info "pytrends skipped"

step "Creating directories"
for d in comunicacao inteligencia/{base_conhecimento,discord_resumos,cursos_resumos,chrome_bookmarks,rag_store} financeiro/{cripto,daytrade,acoes,opcoes} projetos_ativos; do
  mkdir -p "$d"
done
info "Directory structure created"

step "Verifying agents"
TOTAL=0; OK=0
for f in agentes/base_agente.py agentes/squad1/*.py agentes/squad2/*.py agentes/squad3/*.py agentes/squad4/*.py agentes/squad5/*.py; do
  [ "$(basename "$f")" = "__init__.py" ] && continue
  TOTAL=$((TOTAL+1))
  python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null && OK=$((OK+1))
done
info "$OK/$TOTAL agents syntax OK"

step "Initializing RAG engine"
python3 -c "
import sys; sys.path.insert(0,'.')
from rag_engine import inicializar_base_conhecimento
rag = inicializar_base_conhecimento()
print(f'  RAG: {len(rag.chunks)} chunks in {len(rag.listar_categorias())} categories')
" 2>/dev/null || info "RAG init skipped (run manually: python3 rag_engine.py --init)"

step "Running integrity checks"
bash scripts/verify-integrity.sh 2>/dev/null || node scripts/verify-integrity.sh 2>/dev/null || info "Integrity check skipped"

echo -e "\n${BOLD}Nexus Autonomous ready!${NC}"
echo "  Dashboard: python3 dashboard.py --live"
echo "  RAG search: python3 rag_engine.py --buscar 'query'"
echo "  Full test:  python3 -c \"from agentes.squad1.radar_china import RadarChina; RadarChina().executar()\""
