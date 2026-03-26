#!/bin/bash
# Script de contenção v2 para mediaanalysisd - Mais agressivo
# Nexus Orchestrator - Monitoramento Intensivo

LOG_FILE="mediaanalysisd_monitor_v2.log"
MAX_CPU=30           # Limite reduzido para 30% (era 50%)
CHECK_INTERVAL=5     # Verificar a cada 5 segundos (era 10s)
MAX_KILL_ATTEMPTS=5  # Máximo de tentativas de kill por ciclo
RESTART_TRACK_FILE="/tmp/mediaanalysisd_restarts.tmp"

echo "=== Iniciando Monitoramento Mediaanalysisd v2 ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}% (mais agressivo)" >> "$LOG_FILE"
echo "Intervalo: ${CHECK_INTERVAL}s (mais frequente)" >> "$LOG_FILE"
echo "Max Tentativas: ${MAX_KILL_ATTEMPTS}" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Inicializar tracking de reinícios
echo "0" > "$RESTART_TRACK_FILE"
LAST_MINUTE_COUNT=0
LAST_MINUTE_TIME=$(date +%s)

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    CURRENT_TIME=$(date +%s)
    
    # Resetar contador de reinícios a cada minuto
    if [ $((CURRENT_TIME - LAST_MINUTE_TIME)) -ge 60 ]; then
        LAST_MINUTE_COUNT=0
        LAST_MINUTE_TIME=$CURRENT_TIME
        echo "0" > "$RESTART_TRACK_FILE"
    fi
    
    # Encontrar processos mediaanalysisd
    PROCESSES=$(ps aux | grep mediaanalysisd | grep -v grep | grep -v "$0")
    
    if [ -n "$PROCESSES" ]; then
        echo "[$TIMESTAMP] Processos mediaanalysisd encontrados:" >> "$LOG_FILE"
        echo "$PROCESSES" >> "$LOG_FILE"
        
        # Analisar cada processo
        KILL_COUNT=0
        echo "$PROCESSES" | while read LINE; do
            PID=$(echo "$LINE" | awk '{print $2}')
            CPU=$(echo "$LINE" | awk '{print $3}')
            COMMAND=$(echo "$LINE" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
            
            # Converter CPU para número inteiro
            CPU_INT=${CPU%.*}
            
            # Critério 1: CPU acima do limite
            # Critério 2: Processo existe há menos de 10s (possível reinício recente)
            PROCESS_AGE=$(ps -o etime= -p "$PID" 2>/dev/null | awk -F: '{if (NF==2) print $1*60+$2; else if (NF==3) print $1*3600+$2*60+$3; else print 0}')
            
            if [ "$CPU_INT" -gt "$MAX_CPU" ] || [ "${PROCESS_AGE:-0}" -lt 10 ]; then
                echo "[$TIMESTAMP] ALERTA: PID $PID com ${CPU}% CPU, idade ${PROCESS_AGE}s (limite: ${MAX_CPU}%)" >> "$LOG_FILE"
                
                if [ "$KILL_COUNT" -lt "$MAX_KILL_ATTEMPTS" ]; then
                    echo "[$TIMESTAMP] Tentando kill -15 (SIGTERM) no PID $PID..." >> "$LOG_FILE"
                    kill -15 "$PID" 2>/dev/null
                    sleep 1
                    
                    # Verificar se processo ainda existe
                    if ps -p "$PID" > /dev/null 2>&1; then
                        echo "[$TIMESTAMP] Processo ainda ativo, tentando kill -9 (SIGKILL)..." >> "$LOG_FILE"
                        kill -9 "$PID" 2>/dev/null
                        sleep 1
                        
                        if ! ps -p "$PID" > /dev/null 2>&1; then
                            echo "[$TIMESTAMP] SUCESSO: PID $PID eliminado" >> "$LOG_FILE"
                            ((KILL_COUNT++))
                            
                            # Incrementar contador de reinícios
                            LAST_MINUTE_COUNT=$((LAST_MINUTE_COUNT + 1))
                            echo "$LAST_MINUTE_COUNT" > "$RESTART_TRACK_FILE"
                            
                            # Alertar se muitos reinícios
                            if [ "$LAST_MINUTE_COUNT" -ge 3 ]; then
                                echo "[$TIMESTAMP] ⚠️ ALERTA: $LAST_MINUTE_COUNT reinícios no último minuto!" >> "$LOG_FILE"
                            fi
                        else
                            echo "[$TIMESTAMP] FALHA: Não foi possível eliminar PID $PID" >> "$LOG_FILE"
                        fi
                    else
                        echo "[$TIMESTAMP] SUCESSO: PID $PID terminado com SIGTERM" >> "$LOG_FILE"
                        ((KILL_COUNT++))
                        
                        # Incrementar contador de reinícios
                        LAST_MINUTE_COUNT=$((LAST_MINUTE_COUNT + 1))
                        echo "$LAST_MINUTE_COUNT" > "$RESTART_TRACK_FILE"
                    fi
                else
                    echo "[$TIMESTAMP] Limite de tentativas de kill atingido para este ciclo" >> "$LOG_FILE"
                fi
            else
                echo "[$TIMESTAMP] OK: PID $PID com ${CPU}% CPU, idade ${PROCESS_AGE}s (abaixo/fora dos critérios)" >> "$LOG_FILE"
            fi
        done
    else
        echo "[$TIMESTAMP] Nenhum processo mediaanalysisd ativo" >> "$LOG_FILE"
    fi
    
    # Verificar status geral do sistema
    LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1)
    CPU_IDLE=$(top -l 1 | grep "CPU usage" | awk '{print $7}' | sed 's/%//')
    FREE_MEM=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    FREE_MEM_MB=$((FREE_MEM * 16384 / 1024 / 1024))
    
    # Verificar contador de reinícios
    RESTART_COUNT=$(cat "$RESTART_TRACK_FILE" 2>/dev/null || echo "0")
    
    echo "[$TIMESTAMP] Status Sistema: Load=$LOAD_AVG, CPU Idle=${CPU_IDLE}%, Mem Livre=${FREE_MEM_MB}MB" >> "$LOG_FILE"
    echo "[$TIMESTAMP] Reinícios último minuto: $RESTART_COUNT" >> "$LOG_FILE"
    
    # Alertas baseados em métricas
    if [ "$(echo "$LOAD_AVG > 4.0" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "[$TIMESTAMP] ⚠️ ALERTA: Load Avg alto ($LOAD_AVG)" >> "$LOG_FILE"
    fi
    
    if [ "$(echo "$CPU_IDLE < 50" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
        echo "[$TIMESTAMP] ⚠️ ALERTA: CPU Idle baixo (${CPU_IDLE}%)" >> "$LOG_FILE"
    fi
    
    if [ "$FREE_MEM_MB" -lt 300 ]; then
        echo "[$TIMESTAMP] ⚠️ ALERTA: Memória livre baixa (${FREE_MEM_MB}MB)" >> "$LOG_FILE"
    fi
    
    echo "---" >> "$LOG_FILE"
    
    sleep "$CHECK_INTERVAL"
done