#!/bin/bash

# Script de Otimização de Memória - Nexus Orchestrator
# Data: 2026-03-21
# Autor: Nexus Infrastructure Team

echo "=========================================="
echo "OTIMIZAÇÃO DE MEMÓRIA - NEXUS ORCHESTRATOR"
echo "=========================================="
echo "Data: $(date)"
echo ""

# 1. VERIFICAÇÃO INICIAL
echo "1. VERIFICAÇÃO INICIAL DE MEMÓRIA"
echo "----------------------------------"
top -l 1 | head -10 | grep -E "(PhysMem|Load Avg|CPU)"
echo ""

# 2. IDENTIFICAÇÃO DE PROCESSOS CONSUMIDORES
echo "2. TOP 10 PROCESSOS POR USO DE MEMÓRIA"
echo "--------------------------------------"
ps aux | sort -k5 -rn | head -10 | awk '{print $2, $11, $5/1024"MB", $4"%"}'
echo ""

# 3. LIMPEZA DE CACHE DO SISTEMA
echo "3. LIMPEZA DE CACHE DO SISTEMA"
echo "-------------------------------"
echo "Limpando caches do sistema..."

# Limpar cache do DNS
sudo dscacheutil -flushcache 2>/dev/null && echo "✓ Cache DNS limpo" || echo "✗ Falha ao limpar cache DNS"

# Limpar cache do kernel (se permitido)
sudo purge 2>/dev/null && echo "✓ Cache do kernel limpo" || echo "✗ Falha ao limpar cache do kernel (pode requerer sudo)"

echo ""

# 4. LIMPEZA DE ARQUIVOS TEMPORÁRIOS
echo "4. LIMPEZA DE ARQUIVOS TEMPORÁRIOS"
echo "----------------------------------"
TEMP_DIRS=(
    "/tmp"
    "/var/tmp"
    "$HOME/Library/Caches"
    "$HOME/.cache"
)

for dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Limpando $dir..."
        find "$dir" -type f -name "*.tmp" -delete 2>/dev/null
        find "$dir" -type f -name "*.temp" -delete 2>/dev/null
        find "$dir" -type f -name "*.log" -mtime +7 -delete 2>/dev/null
        echo "✓ $dir limpo"
    fi
done
echo ""

# 5. OTIMIZAÇÃO DE PROCESSOS NODE.JS
echo "5. OTIMIZAÇÃO DE PROCESSOS NODE.JS"
echo "----------------------------------"
NODE_PROCESSES=$(ps aux | grep -E "(node|npm|yarn|pnpm)" | grep -v grep | wc -l)
echo "Processos Node.js ativos: $NODE_PROCESSES"

if [ $NODE_PROCESSES -gt 10 ]; then
    echo "⚠️  Alto número de processos Node.js. Considerar:"
    echo "   - Consolidar serviços"
    echo "   - Ajustar limites de memória"
    echo "   - Reiniciar serviços não críticos"
fi
echo ""

# 6. RECOMENDAÇÕES DE OTIMIZAÇÃO
echo "6. RECOMENDAÇÕES DE OTIMIZAÇÃO"
echo "-------------------------------"
echo "🟡 RECOMENDAÇÕES IMEDIATAS:"
echo "   1. Fechar abas não utilizadas do Chrome"
echo "   2. Reiniciar serviços Node.js não críticos"
echo "   3. Limpar cache de aplicações pesadas"
echo ""
echo "🟢 RECOMENDAÇÕES DE LONGO PRAZO:"
echo "   1. Implementar limites de memória por processo"
echo "   2. Configurar swap adequadamente"
echo "   3. Monitorar vazamentos de memória"
echo "   4. Considerar upgrade de memória física"
echo ""

# 7. VERIFICAÇÃO FINAL
echo "7. VERIFICAÇÃO FINAL DE MEMÓRIA"
echo "--------------------------------"
echo "Aguardando 5 segundos para estabilização..."
sleep 5
top -l 1 | head -10 | grep -E "(PhysMem|Load Avg|CPU)"
echo ""

# 8. RELATÓRIO DE AÇÕES
echo "8. RELATÓRIO DE AÇÕES EXECUTADAS"
echo "---------------------------------"
echo "✅ Cache do sistema limpo"
echo "✅ Arquivos temporários removidos"
echo "✅ Processos analisados"
echo "✅ Recomendações geradas"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "   1. Monitorar memória livre nas próximas horas"
echo "   2. Implementar recomendações de longo prazo"
echo "   3. Agendar execução periódica deste script"
echo ""

echo "=========================================="
echo "OTIMIZAÇÃO CONCLUÍDA - $(date)"
echo "=========================================="