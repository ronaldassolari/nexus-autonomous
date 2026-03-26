#!/bin/bash
# Script de contenção para Virtual Machine (com.apple.Virtualization.VirtualMachine)
# Nexus Orchestrator - Monitoramento Intensivo

LOG_FILE="virtualmachine_monitor.log"
MAX_CPU=50  # Limite máximo de CPU permitido para VM
CHECK_INTERVAL=60  # Verificar a cada 60 segundos
MAX_KILL_ATTEMPTS=2  # Máximo de tentativas de kill por ciclo

echo "=== Iniciando Monitoramento Virtual Machine ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}%" >> "$LOG_FILE"
echo "Intervalo: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
echo "AVISO: Este processo pode ser crítico - intervenção cuidadosa" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Encontrar processos de Virtual Machine
    PROCESSES=$(ps aux | grep "com.apple.Virtualization.VirtualMachine" | grep -v grep | grep -v "$0")
    
    if [ -n "$PROCESSES" ]; then
        echo "[$TIMESTAMP] Processos Virtual Machine encontrados:" >> "$LOG_FILE"
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
                echo "[$TIMESTAMP] ALERTA CRÍTICO: PID $PID com ${CPU}% CPU (limite: ${MAX_CPU}%)" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Comando: $COMMAND" >> "$LOG_FILE"
                
                # Verificar carga do sistema
                LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1 | sed 's/,//')
                LOAD_INT=${LOAD_AVG%.*}
                
                # Intervir apenas se carga do sistema estiver alta
                if [ "$LOAD_INT" -ge 4 ] && [ "$KILL_COUNT" -lt "$MAX_KILL_ATTEMPTS" ]; then
                    echo "[$TIMESTAMP] Carga do sistema CRÍTICA (Load=$LOAD_AVG), tomando ação..." >> "$LOG_FILE"
                    
                    # Primeiro tentar sinal SIGTERM (graceful shutdown)
                    echo "[$TIMESTAMP] Tentando shutdown gracioso (SIGTERM)..." >> "$LOG_FILE"
                    kill -TERM "$PID" 2>/dev/null
                    sleep 5
                    
                    # Verificar se processo ainda está ativo
                    if ps -p "$PID" > /dev/null 2>&1; then
                        echo "[$TIMESTAMP] Processo ainda ativo após SIGTERM, tentando SIGKILL..." >> "$LOG_FILE"
                        kill -KILL "$PID" 2>/dev/null
                        sleep 2
                        
                        if ! ps -p "$PID" > /dev/null 2>&1; then
                            echo "[$TIMESTAMP] SUCCESS: Processo $PID terminado com SIGKILL" >> "$LOG_FILE"
                            
                            # Registrar no log de crises
                            CRISIS_LOG="crises_virtualmachine.log"
                            echo "[$TIMESTAMP] CRISE RESOLVIDA: Virtual Machine terminada - CPU: ${CPU}%, Load: $LOAD_AVG, PID: $PID" >> "$CRISIS_LOG"
                        else
                            echo "[$TIMESTAMP] WARNING: Não foi possível terminar processo $PID" >> "$LOG_FILE"
                        fi
                    else
                        echo "[$TIMESTAMP] SUCCESS: Processo $PID terminado graciosamente" >> "$LOG_FILE"
                        
                        # Registrar no log de crises
                        CRISIS_LOG="crises_virtualmachine.log"
                        echo "[$TIMESTAMP] CRISE RESOLVIDA: Virtual Machine terminada graciosamente - CPU: ${CPU}%, Load: $LOAD_AVG, PID: $PID" >> "$CRISIS_LOG"
                    fi
                    
                    ((KILL_COUNT++))
                else
                    if [ "$LOAD_INT" -lt 4 ]; then
                        echo "[$TIMESTAMP] Carga do sistema aceitável (Load=$LOAD_AVG), apenas monitorando" >> "$LOG_FILE"
                    else
                        echo "[$TIMESTAMP] Limite de tentativas atingido para este ciclo" >> "$LOG_FILE"
                    fi
                fi
            else
                echo "[$TIMESTAMP] OK: PID $PID com ${CPU}% CPU (abaixo do limite)" >> "$LOG_FILE"
            fi
        done
    else
        echo "[$TIMESTAMP] Nenhum processo Virtual Machine ativo" >> "$LOG_FILE"
    fi
    
    # Verificar status geral do sistema
    LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1)
    echo "[$TIMESTAMP] Status Sistema: Load=$LOAD_AVG" >> "$LOG_FILE"
    
    # Verificar memória livre
    FREE_MEM=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
    if [ -n "$FREE_MEM" ] && [ "$FREE_MEM" -lt 300 ]; then
        echo "[$TIMESTAMP] ALERTA MEMÓRIA: Apenas ${FREE_MEM}MB livres" >> "$LOG_FILE"
    fi
    
    echo "---" >> "$LOG_FILE"
    
    sleep "$CHECK_INTERVAL"
done