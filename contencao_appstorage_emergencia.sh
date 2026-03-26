#!/bin/bash

# Script de contenção de emergência para ApplicationsStorageExtension
# Nexus Orchestrator - Monitoramento Intensivo - CRISE DE CPU
# Criado: 2026-03-26 10:15

set -e

# Configurações de emergência
PROCESS_NAME="ApplicationsStorageExtension"
PROCESS_PID="14423"  # PID específico identificado
MAX_CPU_PERCENT=30    # Limite muito baixo para emergência
CHECK_INTERVAL=5      # Verificar a cada 5 segundos
MAX_CHECKS=15         # Máximo de verificações
FORCE_MODE=true       # Sempre modo force

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

emergency() {
    echo -e "${CYAN}[EMERGÊNCIA SISTÊMICA]${NC} $1"
}

# Banner de emergência
echo "========================================"
emergency "NEXUS ORCHESTRATOR - CONTENÇÃO DE EMERGÊNCIA"
emergency "CRISE: ApplicationsStorageExtension = 100% CPU"
emergency "PID: $PROCESS_PID - Tempo execução: 7:33 horas"
emergency "Iniciando intervenção de emergência..."
echo "========================================"

# Verificar se processo ainda existe
check_process_exists() {
    if ps -p "$PROCESS_PID" > /dev/null 2>&1; then
        return 0
    else
        error "Processo $PROCESS_PID não encontrado!"
        return 1
    fi
}

# Obter uso de CPU do processo
get_cpu_usage() {
    ps -p "$PROCESS_PID" -o %cpu= 2>/dev/null | awk '{print $1}' || echo "0"
}

# Obter uso de memória do processo
get_mem_usage() {
    ps -p "$PROCESS_PID" -o rss= 2>/dev/null | awk '{printf "%.1f", $1/1024}' || echo "0"
}

# Obter tempo de execução
get_process_time() {
    ps -p "$PROCESS_PID" -o time= 2>/dev/null || echo "00:00"
}

# Suspender processo (SIGSTOP)
suspend_process() {
    log "Suspensão de emergência do PID $PROCESS_PID (SIGSTOP)"
    kill -STOP "$PROCESS_PID" 2>/dev/null || {
        error "Falha ao suspender processo $PROCESS_PID"
        return 1
    }
}

# Retomar processo (SIGCONT)
resume_process() {
    log "Retomando PID $PROCESS_PID (SIGCONT)"
    kill -CONT "$PROCESS_PID" 2>/dev/null || {
        error "Falha ao retomar processo $PROCESS_PID"
        return 1
    }
}

# Matar processo completamente (último recurso)
kill_process() {
    critical "MATANDO processo $PROCESS_PID (SIGKILL) - ÚLTIMO RECURSO!"
    kill -9 "$PROCESS_PID" 2>/dev/null || {
        error "Falha ao matar processo $PROCESS_PID"
        return 1
    }
}

# Reiniciar serviço (se aplicável)
restart_service() {
    critical "Tentando reinício do serviço ApplicationsStorageExtension"
    
    # Tentar parar via launchctl
    sudo launchctl stop com.apple.ApplicationsStorageExtension 2>/dev/null || true
    sleep 3
    
    # Matar qualquer processo remanescente
    pkill -9 "$PROCESS_NAME" 2>/dev/null || true
    sleep 2
    
    # Tentar iniciar novamente
    sudo launchctl start com.apple.ApplicationsStorageExtension 2>/dev/null || true
    sleep 5
    
    critical "Reinício do serviço tentado"
}

# Verificar status do sistema
check_system_status() {
    local cpu_idle=$(top -l 1 | grep "CPU usage" | awk '{print $7}' | sed 's/%//')
    local load_avg=$(top -l 1 | grep "Load Avg" | awk '{print $3}' | sed 's/,//')
    local free_mem=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
    
    echo "CPU Idle: ${cpu_idle}% | Load Avg: ${load_avg} | Memória Livre: ${free_mem}MB"
}

# Conter processo com base no uso de CPU
contain_process() {
    local cpu_usage=$(get_cpu_usage)
    local mem_usage=$(get_mem_usage)
    local process_time=$(get_process_time)
    
    log "Processo $PROCESS_PID - CPU: ${cpu_usage}% | Mem: ${mem_usage}MB | Tempo: $process_time"
    
    # Verificar uso de CPU crítico
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        emergency "CPU CRÍTICA: ${cpu_usage}% - APLICANDO CONTENÇÃO MÁXIMA"
        
        # Suspensão muito longa para processo crítico
        suspend_process
        sleep 12  # 12 segundos de suspensão
        resume_process
        emergency "Contenção MÁXIMA aplicada (12s suspenso)"
        return 3
        
    elif (( $(echo "$cpu_usage > 50" | bc -l) )); then
        warning "CPU MUITO ALTA: ${cpu_usage}% - APLICANDO CONTENÇÃO FORTE"
        
        # Suspensão longa
        suspend_process
        sleep 8  # 8 segundos de suspensão
        resume_process
        warning "Contenção FORTE aplicada (8s suspenso)"
        return 2
        
    elif (( $(echo "$cpu_usage > $MAX_CPU_PERCENT" | bc -l) )); then
        warning "CPU ALTA: ${cpu_usage}% > ${MAX_CPU_PERCENT}%"
        
        # Suspensão padrão
        suspend_process
        sleep 5  # 5 segundos de suspensão
        resume_process
        log "Contenção aplicada (5s suspenso)"
        return 1
        
    else
        success "CPU dentro do limite ($cpu_usage% <= $MAX_CPU_PERCENT%)"
        return 0
    fi
}

# Loop principal de monitoramento
monitor_loop() {
    local checks=0
    local total_containments=0
    
    emergency "Iniciando monitoramento de emergência..."
    check_system_status
    
    while [[ $checks -lt $MAX_CHECKS ]]; do
        checks=$((checks + 1))
        
        echo "========================================"
        log "Verificação #$checks - PID: $PROCESS_PID"
        
        # Verificar se processo ainda existe
        if ! check_process_exists; then
            warning "Processo $PROCESS_PID não existe mais"
            break
        fi
        
        # Verificar status do sistema
        check_system_status
        
        # Conter processo se necessário
        if contain_process; then
            : # Nada a fazer - dentro dos limites
        else
            total_containments=$((total_containments + 1))
        fi
        
        log "Contenções aplicadas: $total_containments"
        
        # Verificar se precisamos de ação mais drástica
        if [[ $total_containments -ge 5 ]]; then
            emergency "Múltiplas contenções falharam - considerando ação drástica"
            
            # Se CPU ainda muito alta após múltiplas contenções
            local current_cpu=$(get_cpu_usage)
            if (( $(echo "$current_cpu > 70" | bc -l) )); then
                critical "CPU ainda em $current_cpu% após $total_containments contenções"
                critical "Considerando reinício do serviço..."
                
                # Última tentativa: reiniciar serviço
                restart_service
                sleep 10
                
                # Verificar se ajudou
                local new_cpu=$(get_cpu_usage 2>/dev/null || echo "0")
                if (( $(echo "$new_cpu < 30" | bc -l) )); then
                    success "Reinício ajudou! CPU agora em $new_cpu%"
                    break
                else
                    error "Reinício não ajudou suficientemente"
                fi
            fi
        fi
        
        # Aguardar próximo ciclo
        if [[ $checks -lt $MAX_CHECKS ]]; then
            sleep $CHECK_INTERVAL
        fi
    done
    
    echo "========================================"
    if [[ $total_containments -eq 0 ]]; then
        success "Monitoramento concluído - Nenhuma contenção necessária"
    else
        warning "Monitoramento concluído - $total_containments contenções aplicadas"
    fi
    
    # Status final
    check_system_status
    
    if check_process_exists; then
        local final_cpu=$(get_cpu_usage)
        local final_mem=$(get_mem_usage)
        success "Processo final - CPU: ${final_cpu}% | Mem: ${final_mem}MB"
    fi
}

# Executar baseado no argumento
case "${1:-}" in
    "force"|"emergency")
        emergency "MODO DE EMERGÊNCIA ATIVADO"
        monitor_loop
        ;;
    "kill")
        emergency "MODO KILL ATIVADO - MATANDO PROCESSO"
        kill_process
        ;;
    "restart")
        emergency "MODO REINÍCIO ATIVADO"
        restart_service
        ;;
    *)
        echo "Uso: $0 [force|kill|restart]"
        echo "  force/emergency: Monitoramento e contenção de emergência"
        echo "  kill: Matar processo imediatamente (último recurso)"
        echo "  restart: Tentar reiniciar serviço"
        exit 1
        ;;
esac

exit 0