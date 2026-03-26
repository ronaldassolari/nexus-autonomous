#!/bin/bash
# Script de contenção para photolibraryd (Photo Library Daemon)
# Nexus Orchestrator - Monitoramento Intensivo

LOG_FILE="photolibraryd_monitor.log"
MAX_CPU=25  # Limite máximo de CPU permitido para photolibraryd (mais restritivo)
CHECK_INTERVAL=20  # Verificar a cada 20 segundos (mais frequente)
MAX_KILL_ATTEMPTS=2  # Máximo de tentativas de kill por ciclo

echo "=== Iniciando Monitoramento Photolibraryd ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}%" >> "$LOG_FILE"
echo "Intervalo: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
echo "AVISO: Este é um processo crítico do sistema - intervenção limitada" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Encontrar processos photolibraryd (usuário não-root)
    PROCESSES=$(ps aux | grep photolibraryd | grep -v grep | grep -v "$0" | grep -v "root.*photolibraryd")
    
    if [ -n "$PROCESSES" ]; then
        echo "[$TIMESTAMP] Processos photolibraryd encontrados:" >> "$LOG_FILE"
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
                echo "[$TIMESTAMP] ALERTA: PID $PID com ${CPU}% CPU (limite: ${MAX_CPU}%)" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Comando: $COMMAND" >> "$LOG_FILE"
                
                # Verificar carga do sistema antes de intervir
                LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1 | sed 's/,//')
                LOAD_INT=${LOAD_AVG%.*}
                
                # Intervir se carga do sistema estiver alta OU CPU muito alta
                if ( [ "$LOAD_INT" -ge 3 ] || [ "$CPU_INT" -ge 60 ] ) && [ "$KILL_COUNT" -lt "$MAX_KILL_ATTEMPTS" ]; then
                    echo "[$TIMESTAMP] Carga do sistema alta (Load=$LOAD_AVG), tentando intervenção limitada..." >> "$LOG_FILE"
                    
                    # Primeiro tentar pausar o processo (SIGSTOP) por tempo variável baseado na CPU
                    PAUSE_TIME=15
                    if [ "$CPU_INT" -ge 70 ]; then
                        PAUSE_TIME=20
                    elif [ "$CPU_INT" -ge 80 ]; then
                        PAUSE_TIME=25
                    fi
                    
                    echo "[$TIMESTAMP] Tentando pausar processo (SIGSTOP) por ${PAUSE_TIME} segundos..." >> "$LOG_FILE"
                    kill -STOP "$PID" 2>/dev/null
                    
                    # Registrar no log de crises
                    CRISIS_LOG="crises_photolibraryd.log"
                    echo "[$TIMESTAMP] INTERVENÇÃO: photolibraryd pausado - CPU: ${CPU}%, Load: $LOAD_AVG, PID: $PID, Pausa: ${PAUSE_TIME}s" >> "$CRISIS_LOG"
                    
                    # Esperar tempo variável
                    sleep "$PAUSE_TIME"
                    
                    # Retomar o processo (SIGCONT)
                    echo "[$TIMESTAMP] Retomando processo (SIGCONT)..." >> "$LOG_FILE"
                    kill -CONT "$PID" 2>/dev/null
                    
                    echo "[$TIMESTAMP] Processo retomado após pausa de ${PAUSE_TIME} segundos" >> "$LOG_FILE"
                    ((KILL_COUNT++))
                    
                    # Adicionar ao log de crises
                    echo "[$TIMESTAMP] RECUPERAÇÃO: photolibraryd retomado após pausa" >> "$CRISIS_LOG"
                else
                    if [ "$LOAD_INT" -lt 3 ]; then
                        echo "[$TIMESTAMP] Carga do sistema aceitável (Load=$LOAD_AVG), mantendo monitoramento apenas" >> "$LOG_FILE"
                    else
                        echo "[$TIMESTAMP] Limite de tentativas de intervenção atingido para este ciclo" >> "$LOG_FILE"
                    fi
                fi
            else
                echo "[$TIMESTAMP] OK: PID $PID com ${CPU}% CPU (abaixo do limite)" >> "$LOG_FILE"
            fi
        done
    else
        echo "[$TIMESTAMP] Nenhum processo photolibraryd ativo (usuário)" >> "$LOG_FILE"
    fi
    
    # Verificar status geral do sistema
    LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}' | cut -d' ' -f1)
    echo "[$TIMESTAMP] Status Sistema: Load=$LOAD_AVG" >> "$LOG_FILE"
    
    # Verificar memória livre
    FREE_MEM=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
    if [ -n "$FREE_MEM" ] && [ "$FREE_MEM" -lt 200 ]; then
        echo "[$TIMESTAMP] ALERTA MEMÓRIA: Apenas ${FREE_MEM}MB livres" >> "$LOG_FILE"
    fi
    
    echo "---" >> "$LOG_FILE"
    
    sleep "$CHECK_INTERVAL"
done