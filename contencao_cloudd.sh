#!/bin/bash
# Script de contenção para cloudd (CloudKit Daemon)
# Nexus Orchestrator - Monitoramento Intensivo

LOG_FILE="cloudd_monitor.log"
MAX_CPU=40  # Limite máximo de CPU permitido para cloudd
CHECK_INTERVAL=15  # Verificar a cada 15 segundos
MAX_KILL_ATTEMPTS=2  # Máximo de tentativas de kill por ciclo

echo "=== Iniciando Monitoramento Cloudd (CloudKit) ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}%" >> "$LOG_FILE"
echo "Intervalo: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Encontrar processos cloudd (exceto o processo do sistema root)
    PROCESSES=$(ps aux | grep cloudd | grep -v grep | grep -v "$0" | grep -v "root.*cloudd")
    
    if [ -n "$PROCESSES" ]; then
        echo "[$TIMESTAMP] Processos cloudd encontrados:" >> "$LOG_FILE"
        echo "$PROCESSES" >> "$LOG_FILE"
        
        # Analisar cada processo
        KILL_COUNT=0
        echo "$PROCESSES" | while read LINE; do
            PID=$(echo "$LINE" | awk '{print $2}')
            CPU=$(echo "$LINE" | awk '{print $3}')
            USER=$(echo "$LINE" | awk '{print $1}')
            COMMAND=$(echo "$LINE" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
            
            # Converter CPU para número inteiro
            CPU_INT=${CPU%.*}
            
            if [ "$CPU_INT" -gt "$MAX_CPU" ]; then
                echo "[$TIMESTAMP] ALERTA: PID $PID (usuário: $USER) com ${CPU}% CPU (limite: ${MAX_CPU}%)" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Comando: $COMMAND" >> "$LOG_FILE"
                
                if [ "$KILL_COUNT" -lt "$MAX_KILL_ATTEMPTS" ] && [ "$USER" != "root" ]; then
                    echo "[$TIMESTAMP] Tentando kill -15 (SIGTERM) no PID $PID..." >> "$LOG_FILE"
                    kill -15 "$PID" 2>/dev/null
                    sleep 3
                    
                    # Verificar se processo ainda existe
                    if ps -p "$PID" > /dev/null 2>&1; then
                        echo "[$TIMESTAMP] Processo ainda ativo, tentando kill -9 (SIGKILL)..." >> "$LOG_FILE"
                        kill -9 "$PID" 2>/dev/null
                        sleep 2
                        
                        if ! ps -p "$PID" > /dev/null 2>&1; then
                            echo "[$TIMESTAMP] SUCESSO: PID $PID eliminado" >> "$LOG_FILE"
                            ((KILL_COUNT++))
                            
                            # Registrar no log de crises
                            CRISIS_LOG="crises_cloudd.log"
                            echo "[$TIMESTAMP] CRISE: cloudd eliminado - CPU: ${CPU}%, PID: $PID" >> "$CRISIS_LOG"
                        else
                            echo "[$TIMESTAMP] FALHA: Não foi possível eliminar PID $PID" >> "$LOG_FILE"
                        fi
                    else
                        echo "[$TIMESTAMP] SUCESSO: PID $PID terminado com SIGTERM" >> "$LOG_FILE"
                        ((KILL_COUNT++))
                        
                        # Registrar no log de crises
                        CRISIS_LOG="crises_cloudd.log"
                        echo "[$TIMESTAMP] CRISE: cloudd terminado - CPU: ${CPU}%, PID: $PID" >> "$CRISIS_LOG"
                    fi
                else
                    if [ "$USER" == "root" ]; then
                        echo "[$TIMESTAMP] AVISO: Processo root não será eliminado (PID $PID)" >> "$LOG_FILE"
                    else
                        echo "[$TIMESTAMP] Limite de tentativas de kill atingido para este ciclo" >> "$LOG_FILE"
                    fi
                fi
            else
                echo "[$TIMESTAMP] OK: PID $PID com ${CPU}% CPU (abaixo do limite)" >> "$LOG_FILE"
            fi
        done
    else
        echo "[$TIMESTAMP] Nenhum processo cloudd ativo (exceto root)" >> "$LOG_FILE"
    fi
    
    # Verificar status geral do sistema
    LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1)
    echo "[$TIMESTAMP] Status Sistema: Load=$LOAD_AVG" >> "$LOG_FILE"
    
    # Verificar se há múltiplos processos cloudd (possível vazamento)
    CLOUDD_COUNT=$(ps aux | grep cloudd | grep -v grep | grep -v "$0" | wc -l)
    if [ "$CLOUDD_COUNT" -gt 3 ]; then
        echo "[$TIMESTAMP] ALERTA: $CLOUDD_COUNT processos cloudd detectados (possível vazamento)" >> "$LOG_FILE"
    fi
    
    echo "---" >> "$LOG_FILE"
    
    sleep "$CHECK_INTERVAL"
done