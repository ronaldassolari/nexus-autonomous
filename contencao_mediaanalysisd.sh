#!/bin/bash
# Script de contenção para mediaanalysisd
# Nexus Orchestrator - Monitoramento Intensivo

LOG_FILE="mediaanalysisd_monitor.log"
MAX_CPU=50  # Limite máximo de CPU permitido
CHECK_INTERVAL=10  # Verificar a cada 10 segundos
MAX_KILL_ATTEMPTS=3  # Máximo de tentativas de kill por ciclo

echo "=== Iniciando Monitoramento Mediaanalysisd ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}%" >> "$LOG_FILE"
echo "Intervalo: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
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
            
            if [ "$CPU_INT" -gt "$MAX_CPU" ]; then
                echo "[$TIMESTAMP] ALERTA: PID $PID com ${CPU}% CPU (limite: ${MAX_CPU}%)" >> "$LOG_FILE"
                
                if [ "$KILL_COUNT" -lt "$MAX_KILL_ATTEMPTS" ]; then
                    echo "[$TIMESTAMP] Tentando kill -15 (SIGTERM) no PID $PID..." >> "$LOG_FILE"
                    kill -15 "$PID" 2>/dev/null
                    sleep 2
                    
                    # Verificar se processo ainda existe
                    if ps -p "$PID" > /dev/null 2>&1; then
                        echo "[$TIMESTAMP] Processo ainda ativo, tentando kill -9 (SIGKILL)..." >> "$LOG_FILE"
                        kill -9 "$PID" 2>/dev/null
                        sleep 1
                        
                        if ! ps -p "$PID" > /dev/null 2>&1; then
                            echo "[$TIMESTAMP] SUCESSO: PID $PID eliminado" >> "$LOG_FILE"
                            ((KILL_COUNT++))
                        else
                            echo "[$TIMESTAMP] FALHA: Não foi possível eliminar PID $PID" >> "$LOG_FILE"
                        fi
                    else
                        echo "[$TIMESTAMP] SUCESSO: PID $PID terminado com SIGTERM" >> "$LOG_FILE"
                        ((KILL_COUNT++))
                    fi
                else
                    echo "[$TIMESTAMP] Limite de tentativas de kill atingido para este ciclo" >> "$LOG_FILE"
                fi
            else
                echo "[$TIMESTAMP] OK: PID $PID com ${CPU}% CPU (abaixo do limite)" >> "$LOG_FILE"
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
    
    echo "[$TIMESTAMP] Status Sistema: Load=$LOAD_AVG, CPU Idle=${CPU_IDLE}%, Mem Livre=${FREE_MEM_MB}MB" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
    
    sleep "$CHECK_INTERVAL"
done