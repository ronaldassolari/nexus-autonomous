#!/bin/bash

# Script de contenção agressiva para photolibraryd
# Nexus Orchestrator - Monitoramento Intensivo
# Criado: 2026-03-25 23:48

set -e

# Configurações
PROCESS_NAME="photolibraryd"
MAX_CPU_PERCENT=30  # Limite máximo de CPU
CHECK_INTERVAL=5    # Verificar a cada 5 segundos
MAX_CHECKS=12       # Máximo de verificações (1 minuto)
FORCE_MODE=false

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ALERTA]${NC} $1"
}

# Verificar modo force
if [[ "$1" == "force" ]]; then
    FORCE_MODE=true
    warning "Modo FORCE ativado - contenção mais agressiva"
fi

# Verificar se o processo existe
check_process() {
    if pgrep -q "$PROCESS_NAME"; then
        return 0
    else
        return 1
    fi
}

# Obter consumo de CPU do processo
get_cpu_usage() {
    local pid=$1
    ps -p "$pid" -o %cpu | tail -n 1 | awk '{print $1}'
}

# Obter consumo de memória do processo
get_mem_usage() {
    local pid=$1
    ps -p "$pid" -o rss | tail -n 1 | awk '{print $1/1024}'  # Em MB
}

# Suspender processo (SIGSTOP)
suspend_process() {
    local pid=$1
    log "Suspending processo $PROCESS_NAME (PID: $pid)..."
    kill -STOP "$pid"
    sleep 2
}

# Retomar processo (SIGCONT)
resume_process() {
    local pid=$1
    log "Resuming processo $PROCESS_NAME (PID: $pid)..."
    kill -CONT "$pid"
    sleep 1
}

# Conter processo de forma inteligente
contain_process() {
    local pid=$1
    local cpu_usage=$2
    
    log "Processo $PROCESS_NAME (PID: $pid) com $cpu_usage% CPU"
    
    if (( $(echo "$cpu_usage > $MAX_CPU_PERCENT" | bc -l) )); then
        warning "CPU acima do limite ($MAX_CPU_PERCENT%) - aplicando contenção"
        
        # Estratégia de contenção baseada no nível de CPU
        if (( $(echo "$cpu_usage > 80" | bc -l) )); then
            # Nível CRÍTICO: suspensão mais longa
            suspend_process "$pid"
            sleep 5
            resume_process "$pid"
            log "Contenção CRÍTICA aplicada (5s suspenso)"
            
        elif (( $(echo "$cpu_usage > 50" | bc -l) )); then
            # Nível ALTO: suspensão média
            suspend_process "$pid"
            sleep 3
            resume_process "$pid"
            log "Contenção ALTA aplicada (3s suspenso)"
            
        else
            # Nível MODERADO: suspensão curta
            suspend_process "$pid"
            sleep 1
            resume_process "$pid"
            log "Contenção MODERADA aplicada (1s suspenso)"
        fi
        
        return 1  # Contenção aplicada
    else
        success "CPU dentro do limite ($cpu_usage% <= $MAX_CPU_PERCENT%)"
        return 0  # Sem contenção necessária
    fi
}

# Modo de monitoramento contínuo
monitor_loop() {
    local checks=0
    
    log "Iniciando monitoramento do $PROCESS_NAME"
    log "Limite de CPU: $MAX_CPU_PERCENT%"
    log "Intervalo de verificação: $CHECK_INTERVAL segundos"
    log "Máximo de verificações: $MAX_CHECKS"
    
    while [[ $checks -lt $MAX_CHECKS ]]; do
        checks=$((checks + 1))
        
        if ! check_process; then
            warning "Processo $PROCESS_NAME não encontrado"
            break
        fi
        
        # Obter todos os PIDs do processo
        pids=$(pgrep "$PROCESS_NAME")
        
        for pid in $pids; do
            cpu_usage=$(get_cpu_usage "$pid")
            mem_usage=$(get_mem_usage "$pid")
            
            echo "----------------------------------------"
            log "Verificação #$checks - PID: $pid"
            log "CPU: ${cpu_usage}% | Memória: ${mem_usage}MB"
            
            # Aplicar contenção se necessário
            if contain_process "$pid" "$cpu_usage"; then
                # Sem contenção aplicada
                if [[ "$FORCE_MODE" == true ]] && (( $(echo "$cpu_usage > 20" | bc -l) )); then
                    warning "Modo FORCE: aplicando contenção preventiva"
                    suspend_process "$pid"
                    sleep 1
                    resume_process "$pid"
                fi
            fi
        done
        
        # Aguardar próximo ciclo (exceto na última iteração)
        if [[ $checks -lt $MAX_CHECKS ]]; then
            sleep "$CHECK_INTERVAL"
        fi
    done
    
    log "Monitoramento concluído ($checks verificações)"
}

# Modo de contenção única (one-shot)
one_shot_containment() {
    if ! check_process; then
        error "Processo $PROCESS_NAME não está em execução"
        exit 1
    fi
    
    pids=$(pgrep "$PROCESS_NAME")
    local contained=0
    
    for pid in $pids; do
        cpu_usage=$(get_cpu_usage "$pid")
        
        if (( $(echo "$cpu_usage > $MAX_CPU_PERCENT" | bc -l) )); then
            warning "Aplicando contenção one-shot no PID $pid ($cpu_usage% CPU)"
            suspend_process "$pid"
            sleep 2
            resume_process "$pid"
            contained=$((contained + 1))
        fi
    done
    
    if [[ $contained -gt 0 ]]; then
        success "Contenção one-shot aplicada em $contained processo(s)"
    else
        log "Nenhuma contenção necessária (CPU dentro dos limites)"
    fi
}

# Menu principal
case "${1:-monitor}" in
    monitor)
        monitor_loop
        ;;
    oneshot)
        one_shot_containment
        ;;
    status)
        if check_process; then
            pids=$(pgrep "$PROCESS_NAME")
            success "Processo $PROCESS_NAME está em execução"
            echo "PIDs: $pids"
            for pid in $pids; do
                cpu=$(get_cpu_usage "$pid")
                mem=$(get_mem_usage "$pid")
                echo "  PID $pid: CPU=${cpu}%, Mem=${mem}MB"
            done
        else
            warning "Processo $PROCESS_NAME não está em execução"
        fi
        ;;
    help|--help|-h)
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos:"
        echo "  monitor     - Monitoramento contínuo (padrão)"
        echo "  oneshot     - Contenção única"
        echo "  status      - Verificar status do processo"
        echo "  force       - Modo de monitoramento com contenção agressiva"
        echo "  help        - Mostrar esta ajuda"
        echo ""
        echo "Exemplos:"
        echo "  $0 monitor      # Monitorar continuamente"
        echo "  $0 oneshot      # Aplicar contenção uma vez"
        echo "  $0 force monitor # Monitorar com contenção agressiva"
        ;;
    *)
        error "Comando inválido: $1"
        echo "Use '$0 help' para ver os comandos disponíveis"
        exit 1
        ;;
esac

exit 0