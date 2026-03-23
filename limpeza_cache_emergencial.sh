#!/bin/bash

# Script de limpeza emergencial de cache - Nexus Orchestrator
# Data: 2026-03-22 09:20 BRT
# Situação: Memória crítica (40M livre), serviços financeiros offline

echo "🔧 INICIANDO LIMPEZA EMERGENCIONAL DE CACHE"
echo "=========================================="
echo "Situação: Memória livre: 40M (meta: > 500M)"
echo "Cache total identificado: 17G"
echo ""

# 1. Backup do estado atual de memória
echo "📊 ESTADO INICIAL DA MEMÓRIA:"
top -l 1 -n 0 | grep -E "PhysMem|Load Avg"

# 2. Limpeza cache Google (9.2G)
echo ""
echo "🧹 LIMPANDO CACHE GOOGLE (9.2G)..."
if [ -d "$HOME/Library/Caches/Google" ]; then
    du -sh "$HOME/Library/Caches/Google"
    rm -rf "$HOME/Library/Caches/Google"/*
    echo "✅ Cache Google limpo"
else
    echo "⚠️ Diretório Google não encontrado"
fi

# 3. Limpeza cache Spotify (4.5G)
echo ""
echo "🎵 LIMPANDO CACHE SPOTIFY (4.5G)..."
if [ -d "$HOME/Library/Caches/com.spotify.client" ]; then
    du -sh "$HOME/Library/Caches/com.spotify.client"
    rm -rf "$HOME/Library/Caches/com.spotify.client"/*
    echo "✅ Cache Spotify limpo"
else
    echo "⚠️ Diretório Spotify não encontrado"
fi

# 4. Limpeza cache Homebrew (1.1G)
echo ""
echo "🍺 LIMPANDO CACHE HOMEBREW (1.1G)..."
if command -v brew &> /dev/null; then
    brew cleanup --prune=all
    echo "✅ Cache Homebrew limpo"
else
    echo "⚠️ Homebrew não encontrado"
fi

# 5. Limpeza cache pip (314M)
echo ""
echo "🐍 LIMPANDO CACHE PIP (314M)..."
if command -v pip &> /dev/null; then
    pip cache purge
    echo "✅ Cache pip limpo"
elif command -v pip3 &> /dev/null; then
    pip3 cache purge
    echo "✅ Cache pip3 limpo"
else
    echo "⚠️ Pip não encontrado"
fi

# 6. Limpeza cache npm/pnpm (110M)
echo ""
echo "📦 LIMPANDO CACHE NPM/PNPM (110M)..."
if command -v npm &> /dev/null; then
    npm cache clean --force
    echo "✅ Cache npm limpo"
fi

if command -v pnpm &> /dev/null; then
    pnpm store prune
    echo "✅ Cache pnpm limpo"
fi

# 7. Limpeza cache Docker (se existir)
echo ""
echo "🐳 VERIFICANDO CACHE DOCKER..."
if command -v docker &> /dev/null; then
    docker system prune -af --volumes
    echo "✅ Cache Docker limpo"
else
    echo "ℹ️ Docker não encontrado"
fi

# 8. Estado final da memória
echo ""
echo "📊 ESTADO FINAL DA MEMÓRIA:"
sleep 5  # Aguardar sistema processar limpeza
top -l 1 -n 0 | grep -E "PhysMem|Load Avg"

# 9. Estimativa de espaço liberado
echo ""
echo "📈 ESTIMATIVA DE ESPAÇO LIBERADO:"
echo "- Google Chrome: ~9.2G"
echo "- Spotify: ~4.5G"
echo "- Homebrew: ~1.1G"
echo "- Outros: ~500M"
echo "-------------------"
echo "TOTAL ESTIMADO: ~15.3G"

# 10. Recomendações
echo ""
echo "🎯 RECOMENDAÇÕES PÓS-LIMPEZA:"
echo "1. Reiniciar serviços financeiros (Cripto Trader, DimDim)"
echo "2. Monitorar memória por 30 minutos"
echo "3. Verificar estabilidade serviços"
echo "4. Documentar lições aprendidas"

echo ""
echo "✅ LIMPEZA EMERGENCIONAL CONCLUÍDA"
echo "Próximos passos no COORDENACAO_EQUIPES_NEXUS_0918.md"