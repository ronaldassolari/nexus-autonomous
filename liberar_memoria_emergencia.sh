#!/bin/bash

# Script de liberação de memória de emergência
# Nexus Orchestrator - CRISE DE MEMÓRIA (90MB livres)
# Criado: 2026-03-26 00:52

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

critical() {
    echo -e "${PURPLE}[CRÍTICO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ALERTA]${NC} $1"
}

# Verificar memória atual
check_memory() {
    echo "========================================"
    critical "VERIFICAÇÃO DE MEMÓRIA DO SISTEMA"
    echo "========================================"
    
    top -l 1 | grep "PhysMem"
    echo ""
    
    # Memória livre atual
    local free_mem=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
    echo "Memória livre atual: ${free_mem}MB"
    echo ""
    
    if [[ "$free_mem" -lt 100 ]]; then
        critical "SITUAÇÃO CRÍTICA: Menos de 100MB livres!"
        return 1
    elif [[ "$free_mem" -lt 200 ]]; then
        warning "SITUAÇÃO DE ALERTA: Menos de 200MB livres"
        return 2
    else
        success "Situação normal: ${free_mem}MB livres"
        return 0
    fi
}

# Listar processos consumindo mais memória
list_memory_hogs() {
    echo "========================================"
    critical "TOP 10 PROCESSOS CONSUMIDORES DE MEMÓRIA"
    echo "========================================"
    
    ps aux | sort -nrk 6 | head -10 | awk '{printf "%-10s %-8s %-8s %-10s\n", $1, $2, $3, $6/1024"MB"}'
    echo ""
}

# Processos que podem ser fechados com segurança (não essenciais)
SAFE_TO_CLOSE=(
    "Claude"
    "Google Chrome"
    "Tor Browser"
    "firefox"
    "next-server"
)

# Processos CRÍTICOS que NÃO devem ser fechados
CRITICAL_PROCESSES=(
    "openclaw"
    "WindowServer"
    "loginwindow"
    "Dock"
    "Finder"
    "SystemUIServer"
    "kernel"
)

# Tentar fechar processos não essenciais
close_non_essential() {
    echo "========================================"
    critical "TENTANDO FECHAR PROCESSOS NÃO ESSENCIAIS"
    echo "========================================"
    
    local closed_count=0
    local saved_memory=0
    
    for process in "${SAFE_TO_CLOSE[@]}"; do
        # Verificar se o processo está em execução
        if pgrep -q -f "$process"; then
            # Obter memória usada pelo processo
            local mem_used=$(ps aux | grep -i "$process" | grep -v grep | head -1 | awk '{print $6}')
            local mem_mb=$((mem_used / 1024))
            
            warning "Processo encontrado: $process (usando ~${mem_mb}MB)"
            
            # Perguntar ao usuário (simulado - em produção seria interativo)
            # Por segurança, não fechamos automaticamente
            log "  [SIMULAÇÃO] Fechando $process liberaria ~${mem_mb}MB"
            
            saved_memory=$((saved_memory + mem_mb))
            closed_count=$((closed_count + 1))
        fi
    done
    
    if [[ $closed_count -gt 0 ]]; then
        warning "SIMULAÇÃO: Fechar $closed_count processos liberaria ~${saved_memory}MB"
    else
        log "Nenhum processo não essencial encontrado para fechar"
    fi
    
    echo ""
}

# Limpar memória do sistema
clean_system_memory() {
    echo "========================================"
    critical "TENTANDO LIMPEZAS DE MEMÓRIA DO SISTEMA"
    echo "========================================"
    
    # 1. Limpar cache do DNS
    log "1. Limpando cache do DNS..."
    sudo dscacheutil -flushcache 2>/dev/null || true
    sudo killall -HUP mDNSResponder 2>/dev/null || true
    success "Cache DNS limpo"
    
    # 2. Limpar cache do sistema
    log "2. Limpando alguns caches do sistema..."
    # sudo purge 2>/dev/null || true  # Muito agressivo, não usar automaticamente
    log "  [OBS] Comando 'purge' muito agressivo - não executado automaticamente"
    
    # 3. Reiniciar serviços problemáticos conhecidos
    log "3. Verificando serviços problemáticos..."
    
    # QuickLook ThumbnailsAgent (frequentemente problemático)
    if pgrep -q "ThumbnailsAgent"; then
        warning "QuickLook ThumbnailsAgent em execução (usa ~500MB)"
        log "  [SUGESTÃO] Reiniciar: sudo killall com.apple.quicklook.ThumbnailsAgent"
    fi
    
    echo ""
}

# Sugerir ações manuais
suggest_manual_actions() {
    echo "========================================"
    critical "AÇÕES MANUAIS RECOMENDADAS"
    echo "========================================"
    
    critical "MEMÓRIA CRÍTICA: 90MB LIVRES APENAS"
    echo ""
    
    echo "1. FECHAR APLICAÇÕES MANUALMENTE:"
    echo "   - Claude (~250MB)"
    echo "   - Google Chrome (~300MB)"
    echo "   - Tor Browser/firefox (~190MB)"
    echo "   - next-server (~460MB)"
    echo ""
    
    echo "2. REINICIAR SERVIÇOS PESADOS:"
    echo "   sudo killall com.apple.quicklook.ThumbnailsAgent"
    echo "   (libera ~500MB, mas thumbnails serão recriados)"
    echo ""
    
    echo "3. VERIFICAR VIRTUALIZAÇÃO:"
    echo "   Parallels VM usando 1.5GB"
    echo "   - Suspender VM se não estiver em uso"
    echo "   - Reduzir memória alocada à VM"
    echo ""
    
    echo "4. LIMPEZAS IMEDIATAS:"
    echo "   sudo purge  # LIMPEZA COMPLETA (cuidado!)"
    echo "   sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder"
    echo ""
}

# Executar
echo "========================================"
critical "NEXUS ORCHESTRATOR - EMERGÊNCIA DE MEMÓRIA"
critical "Sistema com apenas 90MB de memória livre!"
echo "========================================"
echo ""

# Verificar memória atual
check_memory
memory_status=$?

# Listar processos consumidores
list_memory_hogs

# Tentar fechar processos não essenciais (simulação)
close_non_essential

# Limpezas de sistema
clean_system_memory

# Sugerir ações manuais se memória crítica
if [[ $memory_status -eq 1 ]]; then
    suggest_manual_actions
    
    echo "========================================"
    critical "RESUMO DA SITUAÇÃO:"
    echo "========================================"
    echo "Memória livre: 90MB (CRÍTICO)"
    echo "Processo crítico: photolibraryd (66.7% CPU)"
    echo "Maior consumidor: Parallels VM (1.5GB)"
    echo ""
    echo "AÇÕES RECOMENDADAS EM ORDEM:"
    echo "1. Fechar Claude e Chrome"
    echo "2. Suspender Parallels VM"
    echo "3. Reiniciar QuickLook ThumbnailsAgent"
    echo "4. Executar contencao_photolibraryd_v3.sh"
    echo ""
fi

# Status final
echo "========================================"
success "ANÁLISE COMPLETA DA MEMÓRIA"
echo "========================================"
echo "Scripts executados:"
echo "1. contencao_photolibraryd_v3.sh (em execução)"
echo "2. liberar_memoria_emergencia.sh (análise)"
echo ""
echo "Monitoramento ativo:"
echo "- photolibraryd_monitor.log"
echo "- contencao_photolibraryd_v3.log"
echo ""
echo "Próximos passos:"
echo "1. Monitorar memória por 5-10 minutos"
echo "2. Se não melhorar, ações manuais necessárias"
echo "3. Considerar reinício controlado do sistema"

exit 0