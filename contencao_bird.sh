#!/bin/bash

# Script de contenção para processo bird (iCloud Document Sync)
# Monitora e termina processos bird que consomem CPU excessiva
# Nexus Orchestrator - 2026-03-25

LOG_FILE="crises_bird.log"
CPU_THRESHOLD=30  # Percentual de CPU acima do qual o processo é terminado
CHECK_INTERVAL=5  # Segundos entre verificações
MAX_TERMINATIONS_PER_HOUR=30  # Limite de terminações por hora

# Função para registrar crise
log_crisis() {
    local pid=$1
    local cpu=$2
    local mem=$3
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRISE: bird terminado - CPU: CPU=${cpu}%, MEM=${mem}MB, PID: $pid" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: bird terminado - CPU: ${cpu}%, PID: $pid" >&2
}

# Função para verificar limite de terminações
check_termination_limit() {
    local current_hour=$(date '+%Y-%m-%d %H')
    local terminations_this_hour=$(grep -c "CRISE: bird terminado.*$(echo "$current_hour" | cut -c12-13):" "$LOG_FILE" 2>/dev/null || echo 0)
    
    if [ "$terminations_this_hour" -ge "$MAX_TERMINATIONS_PER_HOUR" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERTA: Limite de $MAX_TERMINATIONS_PER_HOUR terminações por hora atingido. Aguardando próximo ciclo." >> "$LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERTA: Limite de terminações atingido. Aguardando próximo ciclo." >&2
        return 1
    fi
    return 0
}

# Função para obter uso de CPU e memória do processo bird
get_process_stats() {
    local pid=$1
    # Usar ps para obter CPU e memória
    ps -p "$pid" -o %cpu,rss 2>/dev/null | tail -1 | awk '{print $1, $2/1024}'
}

# Função principal de monitoramento
monitor_bird() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Iniciando monitoramento do processo bird. Threshold: ${CPU_THRESHOLD}% CPU, Intervalo: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Script de contenção bird iniciado. PID: $$" >&2
    
    local consecutive_high_cpu=0
    local max_consecutive=3  # Número de verificações consecutivas antes de terminar
    
    while true; do
        # Encontrar todos os processos bird
        local bird_pids=$(pgrep -f "bird$" 2>/dev/null)
        
        if [ -n "$bird_pids" ]; then
            for pid in $bird_pids; do
                # Obter estatísticas do processo
                local stats=$(get_process_stats "$pid")
                local cpu=$(echo "$stats" | awk '{print int($1+0.5)}')  # Arredondar
                local mem=$(echo "$stats" | awk '{print int($2+0.5)}')  # Arredondar
                
                if [ -n "$cpu" ] && [ "$cpu" -gt 0 ]; then
                    # Verificar se CPU está acima do threshold
                    if [ "$cpu" -gt "$CPU_THRESHOLD" ]; then
                        ((consecutive_high_cpu++))
                        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: bird PID $pid com CPU alta: ${cpu}% (${consecutive_high_cpu}/${max_consecutive})" >> "$LOG_FILE"
                        
                        # Se CPU alta por verificações consecutivas, terminar
                        if [ "$consecutive_high_cpu" -ge "$max_consecutive" ]; then
                            # Verificar limite de terminações
                            if check_termination_limit; then
                                # Terminar processo
                                kill -TERM "$pid" 2>/dev/null
                                sleep 0.5
                                
                                # Verificar se processo ainda existe
                                if ps -p "$pid" > /dev/null 2>&1; then
                                    # Forçar terminação se ainda existir
                                    kill -KILL "$pid" 2>/dev/null
                                    sleep 0.5
                                fi
                                
                                # Registrar crise
                                log_crisis "$pid" "$cpu" "$mem"
                                
                                # Resetar contador
                                consecutive_high_cpu=0
                                
                                # Log adicional
                                echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Processo bird terminado. CPU estava em ${cpu}%." >&2
                            fi
                        fi
                    else
                        # Resetar contador se CPU estiver normal
                        if [ "$consecutive_high_cpu" -gt 0 ]; then
                            echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: bird PID $pid CPU normalizada: ${cpu}%. Resetando contador." >> "$LOG_FILE"
                            consecutive_high_cpu=0
                        fi
                    fi
                fi
            done
        else
            # Resetar contador se não houver processos bird
            consecutive_high_cpu=0
        fi
        
        # Aguardar próximo ciclo
        sleep "$CHECK_INTERVAL"
    done
}

# Manipulador de sinal para limpeza
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Encerrando script de contenção bird." >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Script de contenção bird encerrado." >&2
    exit 0
}

# Configurar trap para sinais
trap cleanup SIGINT SIGTERM

# Executar monitoramento
monitor_bird