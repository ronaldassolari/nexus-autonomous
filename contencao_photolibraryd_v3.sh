#!/bin/bash

# Script de contenção ULTRA AGRESSIVA para photolibraryd
# Nexus Orchestrator - Monitoramento Intensivo - CRISE DE MEMÓRIA
# Criado: 2026-03-26 00:51

set -e

# Configurações ULTRA AGRESSIVAS
PROCESS_NAME="photolibraryd"
MAX_CPU_PERCENT=20           # Limite MUITO baixo
CHECK_INTERVAL=3            # Verificar a cada 3 segundos
MAX_CHECKS=20               # Máximo de verificações
FORCE_MODE=true             # Sempre modo force
AGGRESSIVE_SUSPENSION=true  # Suspensões mais longas

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

error() {
    echo -e "${RED}[ERRO CRÍTICO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ALERTA MÁXIMO]${NC} $1"
}

critical() {
    echo -e "${PURPLE}[CRÍTICO - AÇÃO IMEDIATA]${NC} $1"
}

# Verificar memória do sistema
check_system_memory() {
    local free_mem=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
    echo "$free_mem"
}

# Funções de contenção
suspend_process() {
    local pid=$1
    log "Suspensão ULTRA AGRESSIVA do PID $pid (SIGSTOP)"
    kill -STOP "$pid" 2>/dev/null || true
}

resume_process() {
    local pid=$1
    log "Retomando PID $pid (SIGCONT)"
    kill -CONT "$pid" 2>/dev/null || true
}

# Reiniciar serviço completamente (último recurso)
restart_service() {
    critical "Tentando reinício COMPLETO do serviço photolibraryd"
    
    # Parar serviço via launchctl
    sudo launchctl stop com.apple.photolibraryd 2>/dev/null || true
    sleep 5
    
    # Matar qualquer processo remanescente
    pkill -9 "$PROCESS_NAME" 2>/dev/null || true
    sleep 3
    
    # Iniciar serviço
    sudo launchctl start com.apple.photolibraryd 2>/dev/null || true
    sleep 10
    
    critical "Reinício do serviço tentado. Verificando status..."
}

# Obter uso de CPU de um PID
get_cpu_usage() {
    local pid=$1
    ps -p "$pid" -o %cpu= 2>/dev/null | awk '{print $1}' || echo "0"
}

# Obter uso de memória de um PID
get_mem_usage() {
    local pid=$1
    ps -p "$pid" -o rss= 2>/dev/null | awk '{printf "%.1f", $1/1024}' || echo "0"
}

# Verificar e conter processo individual
contain_process() {
    local pid=$1
    local cpu_usage=$(get_cpu_usage "$pid")
    local mem_usage=$(get_mem_usage "$pid")
    
    # Verificar memória do sistema primeiro
    local system_free_mem=$(check_system_memory)
    
    if [[ "$system_free_mem" -lt 100 ]]; then
        critical "MEMÓRIA CRÍTICA DO SISTEMA: ${system_free_mem}MB livre!"
        critical "Aplicando contenção MÁXIMA independente do uso de CPU"
        
        # Suspensão EXTREMAMENTE longa
        suspend_process "$pid"
        sleep 15  # 15 segundos de suspensão
        resume_process "$pid"
        critical "Contenção MÁXIMA aplicada (15s suspenso) - Memória crítica!"
        return 2
        
    elif (( $(echo "$cpu_usage > $MAX_CPU_PERCENT" | bc -l) )); then
        warning "CPU ALTA: ${cpu_usage}% > ${MAX_CPU_PERCENT}%"
        
        if (( $(echo "$cpu_usage > 70" | bc -l) )); then
            # Nível CRÍTICO: suspensão MUITO longa
            suspend_process "$pid"
            sleep 10  # 10 segundos
            resume_process "$pid"
            critical "Contenção CRÍTICA aplicada (10s suspenso)"
            
        elif (( $(echo "$cpu_usage > 50" | bc -l) )); then
            # Nível ALTO: suspensão longa
            suspend_process "$pid"
            sleep 7  # 7 segundos
            resume_process "$pid"
            warning "Contenção ALTA aplicada (7s suspenso)"
            
        else
            # Nível MODERADO: suspensão média
            suspend_process "$pid"
            sleep 5  # 5 segundos
            resume_process "$pid"
            log "Contenção MODERADA aplicada (5s suspenso)"
        fi
        
        return 1  # Contenção aplicada
    else
        success "CPU dentro do limite ($cpu_usage% <= $MAX_CPU_PERCENT%)"
        return 0  # Sem contenção necessária
    fi
}

# Modo de monitoramento contínuo ULTRA AGRESSIVO
monitor_loop() {
    local checks=0
    local containment_count=0
    local last_restart_time=0
    local current_time=$(date +%s)
    
    critical "INICIANDO CONTENÇÃO ULTRA AGRESSIVA PARA photolibraryd"
    critical "SISTEMA EM CRISE DE MEMÓRIA - 90MB LIVRES APENAS"
    log "Limite de CPU: $MAX_CPU_PERCENT%"
    log "Intervalo de verificação: $CHECK_INTERVAL segundos"
    log "Máximo de verificações: $MAX_CHECKS"
    
    while [[ $checks -lt $MAX_CHECKS ]]; do
        checks=$((checks + 1))
        current_time=$(date +%s)
        
        # Verificar memória do sistema a cada ciclo
        local system_free_mem=$(check_system_memory)
        log "Memória livre do sistema: ${system_free_mem}MB"
        
        if [[ "$system_free_mem" -lt 50 ]]; then
            critical "MEMÓRIA EXTREMAMENTE CRÍTICA: ${system_free_mem}MB"
            critical "Considerando reinício de emergência do serviço"
            
            # Se já passou mais de 5 minutos desde o último reinício
            if [[ $((current_time - last_restart_time)) -gt 300 ]]; then
                restart_service
                last_restart_time=$current_time
                checks=0  # Resetar contador após reinício
                continue
            fi
        fi
        
        if ! pgrep -q "$PROCESS_NAME"; then
            warning "Processo $PROCESS_NAME não encontrado"
            break
        fi
        
        # Obter todos os PIDs do processo
        pids=$(pgrep "$PROCESS_NAME")
        
        for pid in $pids; do
            cpu_usage=$(get_cpu_usage "$pid")
            mem_usage=$(get_mem_usage "$pid")
            
            echo "========================================"
            log "Verificação #$checks - PID: $pid"
            log "CPU: ${cpu_usage}% | Memória: ${mem_usage}MB"
            log "Contenções aplicadas: $containment_count"
            
            if contain_process "$pid"; then
                if [[ $? -eq 1 ]]; then
                    containment_count=$((containment_count + 1))
                fi
            fi
        done
        
        # Se aplicou muitas contenções seguidas, considerar reinício
        if [[ $containment_count -ge 5 ]]; then
            warning "Múltiplas contenções aplicadas ($containment_count)"
            warning "Processo pode estar em loop infinito"
            
            if [[ $((current_time - last_restart_time)) -gt 600 ]]; then  # 10 minutos
                critical "Reiniciando serviço após múltiplas contenções"
                restart_service
                last_restart_time=$current_time
                containment_count=0
                checks=0
            fi
        fi
        
        echo ""
        sleep "$CHECK_INTERVAL"
    done
    
    log "Monitoramento concluído após $checks verificações"
    log "Total de contenções aplicadas: $containment_count"
    
    # Verificar status final
    if pgrep -q "$PROCESS_NAME"; then
        pids=$(pgrep "$PROCESS_NAME")
        for pid in $pids; do
            cpu_usage=$(get_cpu_usage "$pid")
            mem_usage=$(get_mem_usage "$pid")
            log "Status final - PID $pid: CPU=${cpu_usage}%, Mem=${mem_usage}MB"
        done
    fi
}

# Executar
echo "========================================"
critical "NEXUS ORCHESTRATOR - CONTENÇÃO ULTRA AGRESSIVA"
critical "CRISE: Memória livre = 90MB, photolibraryd = 66.7% CPU"
critical "Iniciando intervenção de emergência..."
echo "========================================"

monitor_loop

# Status final do sistema
echo ""
critical "STATUS FINAL DO SISTEMA:"
uptime
top -l 1 | grep "PhysMem"

exit 0