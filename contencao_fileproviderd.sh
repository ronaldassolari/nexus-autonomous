#!/bin/bash
# Script de Contenção para fileproviderd
# Nexus Orchestrator - Monitoramento Intensivo
# Data: 26/03/2026 - 10:38

set -e

# Configurações
PROCESS_NAME="fileproviderd"
MAX_CPU_PERCENT=30
MAX_RETRIES=5
CHECK_INTERVAL=10
LOG_FILE="contencao_fileproviderd.log"
FORCE_MODE="${1:-normal}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de logging
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO") color=$GREEN ;;
        "WARN") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "DEBUG") color=$BLUE ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}"
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Função para verificar se o processo existe
check_process() {
    local pid=$(pgrep -x "$PROCESS_NAME" | head -1)
    if [ -n "$pid" ]; then
        echo "$pid"
        return 0
    else
        return 1
    fi
}

# Função para obter consumo CPU do processo
get_cpu_usage() {
    local pid="$1"
    local cpu_usage=$(ps -p "$pid" -o %cpu= | awk '{print int($1+0.5)}')
    echo "$cpu_usage"
}

# Função para obter consumo memória do processo
get_mem_usage() {
    local pid="$1"
    local mem_usage=$(ps -p "$pid" -o rss= | awk '{print int($1/1024)}')
    echo "$mem_usage"
}

# Função para aplicar contenção (renice + cgroups se disponível)
apply_containment() {
    local pid="$1"
    local cpu_usage="$2"
    
    log "INFO" "Aplicando contenção ao processo $PROCESS_NAME (PID: $pid)"
    log "INFO" "Consumo atual: ${cpu_usage}% CPU"
    
    # 1. Renice para prioridade mais baixa
    renice -n 19 -p "$pid" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log "INFO" "Prioridade ajustada para 19 (muito baixa)"
    else
        log "WARN" "Não foi possível ajustar prioridade (pode requerer sudo)"
    fi
    
    # 2. Tentar usar cgroups se disponível
    if command -v cgclassify >/dev/null 2>&1; then
        # Criar cgroup se não existir
        if ! cgget -g cpu:nexus_containment >/dev/null 2>&1; then
            cgcreate -g cpu:nexus_containment
            # Limitar para 30% de CPU
            echo "30000 100000" > /sys/fs/cgroup/cpu/nexus_containment/cpu.cfs_quota_us
            echo "100000" > /sys/fs/cgroup/cpu/nexus_containment/cpu.cfs_period_us
            log "INFO" "Cgroup nexus_containment criado com limite de 30% CPU"
        fi
        
        # Mover processo para cgroup
        cgclassify -g cpu:nexus_containment "$pid"
        if [ $? -eq 0 ]; then
            log "INFO" "Processo movido para cgroup nexus_containment"
        fi
    else
        log "DEBUG" "cgclassify não disponível, usando apenas renice"
    fi
    
    # 3. Em modo force, tentar kill se consumo muito alto
    if [ "$FORCE_MODE" = "force" ] && [ "$cpu_usage" -gt 80 ]; then
        log "WARN" "MODO FORCE: Consumo >80%, tentando kill -STOP"
        kill -STOP "$pid"
        sleep 2
        kill -CONT "$pid"
        log "INFO" "Processo pausado e retomado para reset"
    fi
    
    log "INFO" "Contenção aplicada com sucesso"
}

# Função para monitorar após contenção
monitor_after_containment() {
    local pid="$1"
    local initial_cpu="$2"
    
    log "INFO" "Iniciando monitoramento pós-contenção..."
    
    for i in {1..6}; do
        sleep 5
        if ! check_process >/dev/null; then
            log "WARN" "Processo não encontrado após contenção"
            return 1
        fi
        
        current_cpu=$(get_cpu_usage "$pid")
        current_mem=$(get_mem_usage "$pid")
        
        log "INFO" "Monitoramento $i/6: ${current_cpu}% CPU, ${current_mem}MB RAM"
        
        if [ "$current_cpu" -lt "$MAX_CPU_PERCENT" ]; then
            log "INFO" "✅ SUCCESSO: Consumo reduzido para ${current_cpu}% (meta: <${MAX_CPU_PERCENT}%)"
            return 0
        fi
    done
    
    log "WARN" "⚠️  Consumo ainda alto após monitoramento: ${current_cpu}% CPU"
    return 1
}

# Função principal
main() {
    log "INFO" "=========================================="
    log "INFO" "SCRIPT DE CONTENÇÃO: $PROCESS_NAME"
    log "INFO" "Modo: $FORCE_MODE"
    log "INFO" "Data/Hora: $(date)"
    log "INFO" "=========================================="
    
    # Verificar se processo existe
    PID=$(check_process)
    if [ -z "$PID" ]; then
        log "ERROR" "Processo $PROCESS_NAME não encontrado"
        exit 1
    fi
    
    log "INFO" "Processo encontrado: PID $PID"
    
    # Obter métricas iniciais
    INITIAL_CPU=$(get_cpu_usage "$PID")
    INITIAL_MEM=$(get_mem_usage "$PID")
    
    log "INFO" "Métricas iniciais: ${INITIAL_CPU}% CPU, ${INITIAL_MEM}MB RAM"
    
    # Verificar se precisa de contenção
    if [ "$INITIAL_CPU" -lt "$MAX_CPU_PERCENT" ]; then
        log "INFO" "✅ Processo dentro dos limites (<${MAX_CPU_PERCENT}% CPU)"
        exit 0
    fi
    
    log "WARN" "⚠️  Processo excedendo limite: ${INITIAL_CPU}% > ${MAX_CPU_PERCENT}%"
    
    # Aplicar contenção
    apply_containment "$PID" "$INITIAL_CPU"
    
    # Monitorar resultado
    if monitor_after_containment "$PID" "$INITIAL_CPU"; then
        log "INFO" "✅ CONTENÇÃO BEM-SUCEDIDA"
        log "INFO" "Consumo reduzido de ${INITIAL_CPU}% para <${MAX_CPU_PERCENT}%"
    else
        log "WARN" "⚠️  CONTENÇÃO PARCIALMENTE EFETIVA"
        log "WARN" "Consumo ainda pode estar elevado"
    fi
    
    # Métricas finais
    FINAL_CPU=$(get_cpu_usage "$PID")
    FINAL_MEM=$(get_mem_usage "$PID")
    
    log "INFO" "Métricas finais: ${FINAL_CPU}% CPU, ${FINAL_MEM}MB RAM"
    log "INFO" "Redução CPU: $((INITIAL_CPU - FINAL_CPU))%"
    
    # Status final
    if [ "$FINAL_CPU" -lt "$MAX_CPU_PERCENT" ]; then
        log "INFO" "✅ STATUS FINAL: CONTROLE ESTABELECIDO"
        exit 0
    else
        log "ERROR" "❌ STATUS FINAL: CONTROLE INSUFICIENTE"
        log "ERROR" "Consumo ainda alto: ${FINAL_CPU}% CPU"
        exit 2
    fi
}

# Executar
main "$@"