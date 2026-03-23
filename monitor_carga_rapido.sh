#!/bin/bash

# Script de monitoramento rápido da carga do sistema Nexus
# Executar a cada 10 minutos para verificação proativa

echo "=== MONITORAMENTO RÁPIDO DE CARGA - $(date) ==="
echo ""

# 1. Carga do sistema
echo "📊 CARGA DO SISTEMA:"
uptime | awk -F'load averages: ' '{print $2}'
echo ""

# 2. Top 5 processos por CPU
echo "🔥 TOP 5 PROCESSOS POR CPU:"
ps aux | sort -nrk 3 | head -6 | tail -5 | awk '{printf "%-10s %-6s %-8s %s\n", $11, $3"%", $4"%", $2}'
echo ""

# 3. Serviços críticos do Nexus
echo "🔧 SERVIÇOS CRÍTICOS NEXUS:"
if ps aux | grep -q "[o]penclaw-gateway"; then
    echo "✅ OpenClaw Gateway: ONLINE"
else
    echo "❌ OpenClaw Gateway: OFFLINE"
fi

if pgrep -f "whatsappServer.js" > /dev/null; then
    echo "✅ WhatsApp Server: ONLINE"
else
    echo "❌ WhatsApp Server: OFFLINE"
fi

if pgrep -f "dimdim-proxy.js" > /dev/null; then
    echo "✅ DimDim Proxy: ONLINE"
else
    echo "❌ DimDim Proxy: OFFLINE"
fi
echo ""

# 4. Status do ObraSync
echo "💻 STATUS OBRASYNC:"
if [ -d "projetos_ativos/obrasync" ]; then
    cd projetos_ativos/obrasync
    git status --short | wc -l | awk '{if ($1 == 0) print "✅ Git: Working tree clean"; else print "⚠️  Git: " $1 " mudanças pendentes"}'
    cd - > /dev/null
else
    echo "❌ Diretório ObraSync não encontrado"
fi
echo ""

# 5. Uso de memória
echo "🧠 USO DE MEMÓRIA:"
top -l 1 | grep "PhysMem" | awk '{print $2 " usado (" $5 " wired, " $7 " compressor), " $9 " livre"}'
echo ""

# 6. Alertas baseados em thresholds
LOAD=$(uptime | awk -F'load averages: ' '{print $2}' | awk -F', ' '{print $1}')
if (( $(echo "$LOAD > 5.0" | bc -l) )); then
    echo "🚨 ALERTA: Carga elevada ($LOAD) - Investigar imediatamente"
elif (( $(echo "$LOAD > 4.0" | bc -l) )); then
    echo "⚠️  AVISO: Carga moderada ($LOAD) - Monitorar"
else
    echo "✅ OK: Carga normal ($LOAD)"
fi

echo ""
echo "=== FIM DO MONITORAMENTO ==="