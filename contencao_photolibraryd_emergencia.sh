#!/bin/bash
# Script de contenção de emergência para photolibraryd
LIMITE_CPU=30
INTERVALO=30
LOG_FILE="crises_photolibraryd_emergencia.log"

echo "========================================"
echo "[EMERGÊNCIA] NEXUS ORCHESTRATOR - CONTENÇÃO PHOTOLIBRARYD"
echo "[EMERGÊNCIA] Iniciando monitoramento de emergência"
echo "========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limite CPU: $LIMITE_CPU%"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Intervalo: $INTERVALO segundos"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log: $LOG_FILE"
echo "========================================"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    PROCESSOS=$(ps aux | grep photolibraryd | grep -v grep)
    
    # Verificar memória livre
    MEM_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    MEM_FREE_MB=$((MEM_FREE * 16384 / 1024 / 1024))
    
    echo "[$TIMESTAMP] Memória livre: ${MEM_FREE_MB}MB" >> "$LOG_FILE"
    
    if [ -n "$PROCESSOS" ]; then
        while read -r LINE; do
            PID=$(echo "$LINE" | awk '{print $2}')
            CPU=$(echo "$LINE" | awk '{print $3}')
            MEM=$(echo "$LINE" | awk '{print $4}')
            COMANDO=$(echo "$LINE" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
            
            # Converter CPU para número inteiro para comparação
            CPU_INT=$(echo "$CPU" | cut -d. -f1)
            
            if [ "$CPU_INT" -gt "$LIMITE_CPU" ]; then
                echo "[$TIMESTAMP] 🔴 ALERTA CRÍTICO: PID $PID com $CPU% CPU" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Comando: $COMANDO" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Memória: $MEM% RAM" >> "$LOG_FILE"
                
                # Verificar carga do sistema - método alternativo se sysctl falhar
                if command -v sysctl >/dev/null 2>&1; then
                    LOAD_1MIN=$(sysctl -n vm.loadavg | awk '{print $2}')
                    LOAD_5MIN=$(sysctl -n vm.loadavg | awk '{print $3}')
                else
                    # Método alternativo usando uptime
                    LOAD_1MIN=$(uptime | awk -F'load averages: ' '{print $2}' | awk -F', ' '{print $1}')
                    LOAD_5MIN=$(uptime | awk -F'load averages: ' '{print $2}' | awk -F', ' '{print $2}')
                fi
                
                echo "[$TIMESTAMP] Load Avg: $LOAD_1MIN (1min), $LOAD_5MIN (5min)" >> "$LOG_FILE"
                
                # Intervenção baseada na severidade
                if (( $(echo "$LOAD_1MIN > 5.0" | bc -l) )); then
                    echo "[$TIMESTAMP] 🔴 Carga CRÍTICA (Load=$LOAD_1MIN), intervenção ULTRA AGRESSIVA..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 45  # Pausa muito longa para crise extrema
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 45 segundos" >> "$LOG_FILE"
                elif (( $(echo "$LOAD_1MIN > 4.0" | bc -l) )); then
                    echo "[$TIMESTAMP] 🟠 Carga ALTA (Load=$LOAD_1MIN), intervenção agressiva..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 30  # Pausa longa para crise
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 30 segundos" >> "$LOG_FILE"
                elif (( $(echo "$LOAD_1MIN > 3.0" | bc -l) )); then
                    echo "[$TIMESTAMP] 🟡 Carga MODERADA (Load=$LOAD_1MIN), intervenção padrão..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 15
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 15 segundos" >> "$LOG_FILE"
                else
                    echo "[$TIMESTAMP] 🟢 Carga BAIXA (Load=$LOAD_1MIN), intervenção leve..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 10
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 10 segundos" >> "$LOG_FILE"
                fi
                
                # Verificar se processo continua
                sleep 5
                if ps -p "$PID" > /dev/null; then
                    NOVA_CPU=$(ps -p "$PID" -o %cpu= | xargs)
                    NOVA_CPU_INT=$(echo "$NOVA_CPU" | cut -d. -f1)
                    echo "[$TIMESTAMP] Novo consumo: $NOVA_CPU% CPU" >> "$LOG_FILE"
                    
                    # Se ainda alto, intervenção mais agressiva
                    if [ "$NOVA_CPU_INT" -gt "$LIMITE_CPU" ]; then
                        echo "[$TIMESTAMP] ⚠️ Consumo ainda ALTO após intervenção" >> "$LOG_FILE"
                    else
                        echo "[$TIMESTAMP] ✅ Consumo CONTROLADO após intervenção" >> "$LOG_FILE"
                    fi
                else
                    echo "[$TIMESTAMP] ⚠️ Processo terminou após intervenção" >> "$LOG_FILE"
                fi
                
                echo "---" >> "$LOG_FILE"
            else
                echo "[$TIMESTAMP] 🟢 PID $PID com $CPU% CPU (dentro do limite)" >> "$LOG_FILE"
            fi
        done <<< "$PROCESSOS"
    else
        echo "[$TIMESTAMP] ℹ️ Nenhum processo photolibraryd encontrado" >> "$LOG_FILE"
    fi
    
    # Verificar memória crítica e tomar ação adicional
    if [ "$MEM_FREE_MB" -lt 100 ]; then
        echo "[$TIMESTAMP] 🔴 ALERTA MEMÓRIA: ${MEM_FREE_MB}MB livre (< 100MB)" >> "$LOG_FILE"
        echo "[$TIMESTAMP] Executando limpeza de cache de emergência..." >> "$LOG_FILE"
        # Tentar múltiplos métodos de limpeza de cache
        if command -v purge >/dev/null 2>&1; then
            sudo purge 2>/dev/null && echo "[$TIMESTAMP] purge executado com sucesso" >> "$LOG_FILE" || echo "[$TIMESTAMP] purge falhou" >> "$LOG_FILE"
        elif command -v sync >/dev/null 2>&1 && command -v sysctl >/dev/null 2>&1; then
            sync && sudo sysctl -w vm.drop_caches=3 2>/dev/null && echo "[$TIMESTAMP] drop_caches executado" >> "$LOG_FILE" || echo "[$TIMESTAMP] drop_caches não disponível" >> "$LOG_FILE"
        else
            echo "[$TIMESTAMP] Nenhum método de limpeza de cache disponível" >> "$LOG_FILE"
            echo "[$TIMESTAMP] Sugerindo limpeza manual de cache QuickLook..." >> "$LOG_FILE"
            echo "[$TIMESTAMP] Comando sugerido: qlmanage -r cache" >> "$LOG_FILE"
        fi
    fi
    
    sleep "$INTERVALO"
done