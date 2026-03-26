#!/bin/bash
# Script de contenção para corespotlightd
# Monitora e controla consumo excessivo de CPU pelo corespotlightd

LOG_FILE="corespotlightd_monitor.log"
CRISES_LOG="crises_corespotlightd.log"
MAX_CPU=50  # Limite máximo de CPU (%) antes de intervenção
CHECK_INTERVAL=10  # Segundos entre verificações
ADAPTIVE_THRESHOLD=true  # Ajusta limite baseado em load avg

# Função para log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_crisis() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRISE: $1" >> "$CRISES_LOG"
}

# Função para obter load average
get_load_avg() {
    # Extrai load average de 1 minuto
    uptime | awk -F'load averages: ' '{print $2}' | awk -F', ' '{print $1}' | tr -d ','
}

# Função para ajuste adaptativo de limite
get_adaptive_max_cpu() {
    local load_avg=$(get_load_avg)
    local max_cpu=$MAX_CPU
    
    if [ "$ADAPTIVE_THRESHOLD" = true ]; then
        # Ajusta limite baseado no load average
        if (( $(echo "$load_avg > 5.0" | bc -l) )); then
            max_cpu=30  # Limite mais restritivo sob alta carga
        elif (( $(echo "$load_avg > 3.0" | bc -l) )); then
            max_cpu=40  # Limite moderado
        elif (( $(echo "$load_avg > 2.0" | bc -l) )); then
            max_cpu=45  # Limite normal
        else
            max_cpu=50  # Limite padrão
        fi
    fi
    
    echo "$max_cpu"
}

# Função para monitorar corespotlightd
monitor_corespotlightd() {
    log "=== Iniciando monitoramento corespotlightd ==="
    log "Limite CPU: $MAX_CPU%"
    log "Intervalo: $CHECK_INTERVAL segundos"
    log "Threshold Adaptativo: $ADAPTIVE_THRESHOLD"
    
    while true; do
        # Obtém limite adaptativo atual
        local current_max_cpu=$(get_adaptive_max_cpu)
        local load_avg=$(get_load_avg)
        
        # Encontra processos corespotlightd
        local processes=$(ps aux | grep -E "corespotlightd" | grep -v grep)
        
        if [ -z "$processes" ]; then
            log "Nenhum processo corespotlightd encontrado"
        else
            echo "$processes" | while read line; do
                local pid=$(echo "$line" | awk '{print $2}')
                local cpu=$(echo "$line" | awk '{print $3}')
                local mem=$(echo "$line" | awk '{print $4}')
                local command=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
                
                # Remove espaços extras
                cpu=$(echo "$cpu" | tr -d ' ')
                mem=$(echo "$mem" | tr -d ' ')
                
                # Converte CPU para número (remove % se existir)
                cpu=${cpu%\%}
                
                # Verifica se CPU é um número válido
                if [[ "$cpu" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                    # Compara com limite
                    if (( $(echo "$cpu > $current_max_cpu" | bc -l) )); then
                        log "ALERTA: PID $pid com $cpu% CPU (limite: $current_max_cpu%)"
                        log "Detalhes: $cpu% CPU, ${mem}MB MEM, Load: $load_avg"
                        log "Comando: $command"
                        
                        # Tenta terminar processo graciosamente primeiro
                        log "Tentando terminar processo $pid graciosamente..."
                        kill -TERM "$pid" 2>/dev/null
                        sleep 2
                        
                        # Verifica se processo ainda existe
                        if ps -p "$pid" > /dev/null 2>&1; then
                            log "Processo $pid ainda ativo após SIGTERM, forçando término..."
                            log_crisis "PID $pid terminado forçadamente: $cpu% CPU > $current_max_cpu%"
                            kill -9 "$pid" 2>/dev/null
                            
                            # Verifica se foi terminado
                            if ! ps -p "$pid" > /dev/null 2>&1; then
                                log "Processo $pid terminado com sucesso"
                                log_crisis "SUCESSO: PID $pid terminado (CPU: $cpu%, Load: $load_avg)"
                            else
                                log "ERRO: Não foi possível terminar processo $pid"
                                log_crisis "FALHA: Não foi possível terminar PID $pid"
                            fi
                        else
                            log "Processo $pid terminado graciosamente"
                            log_crisis "PID $pid terminado graciosamente: $cpu% CPU > $current_max_cpu%"
                        fi
                    else
                        log "OK: PID $pid com $cpu% CPU, ${mem}MB MEM (dentro do limite: $current_max_cpu%)"
                    fi
                else
                    log "ERRO: CPU inválida para PID $pid: '$cpu'"
                fi
            done
        fi
        
        # Log status do sistema
        log "Status Sistema: Load=$load_avg, MAX_CPU=$current_max_cpu%"
        log "---"
        
        # Aguarda próximo ciclo
        sleep "$CHECK_INTERVAL"
    done
}

# Função para exibir ajuda
show_help() {
    echo "Uso: $0 [opção]"
    echo ""
    echo "Opções:"
    echo "  start     Inicia monitoramento em background"
    echo "  stop      Para monitoramento"
    echo "  status    Exibe status atual"
    echo "  log       Exibe log recente"
    echo "  crises    Exibe log de crises"
    echo "  help      Exibe esta ajuda"
    echo ""
    echo "Configuração:"
    echo "  MAX_CPU: $MAX_CPU% (limite padrão)"
    echo "  CHECK_INTERVAL: $CHECK_INTERVAL segundos"
    echo "  ADAPTIVE_THRESHOLD: $ADAPTIVE_THRESHOLD"
}

# Função para iniciar em background
start_background() {
    if [ -f "corespotlightd_monitor.pid" ]; then
        local pid=$(cat "corespotlightd_monitor.pid" 2>/dev/null)
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Monitoramento já está em execução (PID: $pid)"
            exit 0
        fi
    fi
    
    echo "Iniciando monitoramento corespotlightd em background..."
    monitor_corespotlightd &
    local monitor_pid=$!
    echo "$monitor_pid" > "corespotlightd_monitor.pid"
    echo "Monitoramento iniciado com PID: $monitor_pid"
    echo "Logs: $LOG_FILE"
    echo "Crises: $CRISES_LOG"
}

# Função para parar monitoramento
stop_monitor() {
    if [ -f "corespotlightd_monitor.pid" ]; then
        local pid=$(cat "corespotlightd_monitor.pid" 2>/dev/null)
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Parando monitoramento (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null
            fi
            rm -f "corespotlightd_monitor.pid"
            echo "Monitoramento parado"
        else
            echo "Monitoramento não está em execução"
            rm -f "corespotlightd_monitor.pid"
        fi
    else
        echo "Arquivo PID não encontrado. Tentando encontrar processo..."
        local pid=$(ps aux | grep "contencao_corespotlightd.sh" | grep -v grep | awk '{print $2}' | head -1)
        if [ -n "$pid" ]; then
            echo "Encontrado processo (PID: $pid). Parando..."
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null
            fi
            echo "Processo parado"
        else
            echo "Nenhum processo de monitoramento encontrado"
        fi
    fi
}

# Função para status
show_status() {
    echo "=== Status do Monitoramento Corespotlightd ==="
    
    # Verifica se está em execução
    if [ -f "corespotlightd_monitor.pid" ]; then
        local pid=$(cat "corespotlightd_monitor.pid" 2>/dev/null)
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Status: 🟢 EM EXECUÇÃO (PID: $pid)"
        else
            echo "Status: 🔴 PARADO (PID arquivado mas não em execução)"
            rm -f "corespotlightd_monitor.pid"
        fi
    else
        echo "Status: 🔴 PARADO"
    fi
    
    # Verifica processos corespotlightd atuais
    echo ""
    echo "=== Processos Corespotlightd Atuais ==="
    local processes=$(ps aux | grep -E "corespotlightd" | grep -v grep)
    if [ -z "$processes" ]; then
        echo "Nenhum processo corespotlightd encontrado"
    else
        echo "$processes"
    fi
    
    # Exibe configuração
    echo ""
    echo "=== Configuração ==="
    echo "MAX_CPU: $MAX_CPU%"
    echo "CHECK_INTERVAL: $CHECK_INTERVAL segundos"
    echo "ADAPTIVE_THRESHOLD: $ADAPTIVE_THRESHOLD"
    
    # Exibe logs recentes
    echo ""
    echo "=== Log Recente (últimas 5 linhas) ==="
    if [ -f "$LOG_FILE" ]; then
        tail -5 "$LOG_FILE"
    else
        echo "Arquivo de log não encontrado: $LOG_FILE"
    fi
}

# Função para exibir log
show_log() {
    if [ -f "$LOG_FILE" ]; then
        if [ "$1" = "full" ]; then
            cat "$LOG_FILE"
        else
            tail -20 "$LOG_FILE"
        fi
    else
        echo "Arquivo de log não encontrado: $LOG_FILE"
    fi
}

# Função para exibir crises
show_crises() {
    if [ -f "$CRISES_LOG" ]; then
        if [ "$1" = "full" ]; then
            cat "$CRISES_LOG"
        else
            tail -10 "$CRISES_LOG"
        fi
    else
        echo "Arquivo de crises não encontrado: $CRISES_LOG"
    fi
}

# Processa argumentos
case "$1" in
    start)
        start_background
        ;;
    stop)
        stop_monitor
        ;;
    status)
        show_status
        ;;
    log)
        show_log "$2"
        ;;
    crises)
        show_crises "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Uso: $0 {start|stop|status|log|crises|help}"
        echo "Execute '$0 help' para mais informações"
        exit 1
        ;;
esac

exit 0