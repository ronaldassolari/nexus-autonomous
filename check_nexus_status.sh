#!/bin/bash

echo "=== STATUS DO SISTEMA NEXUS ==="
echo "Data/Hora: $(date)"
echo ""

echo "📊 CARGA DO SISTEMA:"
uptime
echo ""

echo "🧠 USO DE MEMÓRIA:"
free -h 2>/dev/null || sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}'
echo ""

echo "💾 ESPAÇO EM DISCO:"
df -h / | tail -1
echo ""

echo "🔧 PROCESSOS CRÍTICOS:"
echo "1. OpenClaw Gateway:"
ps aux | grep -i openclaw | grep -v grep || echo "Não encontrado"
echo ""

echo "2. WhatsApp Server:"
ps aux | grep -i whatsapp | grep -v grep || echo "Não encontrado"
echo ""

echo "3. DimDim Proxy:"
ps aux | grep -i dimdim | grep -v grep || echo "Não encontrado"
echo ""

echo "📁 PROJETOS ATIVOS:"
echo "Verificando workspace..."
ls -la | grep -E "\.(md|json|yaml|yml)$" | wc -l | xargs echo "Arquivos de projeto/dados:"
echo ""

echo "🔄 STATUS GIT:"
git status 2>/dev/null || echo "Não é um repositório git"
echo ""

echo "🌐 CONEXÕES ATIVAS:"
netstat -an | grep ESTABLISHED | wc -l | xargs echo "Conexões estabelecidas:"
echo ""

echo "=== FIM DO STATUS ==="