#!/bin/bash
# Sistema Integrado de Monitoramento Nexus
# Nexus Orchestrator - Controle Centralizado

LOG_FILE="nexus_monitoramento.log"
ALERTAS_FILE="nexus_alertas.log"
CRISES_FILE="nexus_crises.log"
CHECK_INTERVAL=300  # 5 minutos entre verificações principais

# Função para registrar log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Função para registrar alerta
alerta() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERTA: $1" >> "$ALERTAS_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERTA: $1" >> "$LOG_FILE"
}

# Função para registrar crise
crise() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRISE: $1" >> "$CRISES_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRISE: $1" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRISE: $1" >> "$ALERTAS_FILE"
}

# Inicialização
echo "=== SISTEMA DE MONITORAMENTO NEXUS ===" > "$LOG_FILE"
echo "Iniciado em: $(date)" >> "$LOG_FILE"
echo "Intervalo de verificação: ${CHECK_INTERVAL}s" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "=== HISTÓRICO DE ALERTAS NEXUS ===" > "$ALERTAS_FILE"
echo "Iniciado em: $(date)" >> "$ALERTAS_FILE"
echo "" >> "$ALERTAS_FILE"

echo "=== HISTÓRICO DE CRISES NEXUS ===" > "$CRISES_FILE"
echo "Iniciado em: $(date)" >> "$CRISES_FILE"
echo "" >> "$CRISES_FILE"

log "Sistema de monitoramento Nexus inicializado"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 1. Verificar carga do sistema
    LOAD_AVG=$(uptime | awk -F'load averages: ' '{print $2}')
    LOAD_1=$(echo "$LOAD_AVG" | cut -d' ' -f1)
    LOAD_5=$(echo "$LOAD_AVG" | cut -d' ' -f2)
    LOAD_15=$(echo "$LOAD_AVG" | cut -d' ' -f3)
    
    log "Carga do sistema: $LOAD_1 (1min) $LOAD_5 (5min) $LOAD_15 (15min)"
    
    # Verificar limites de carga
    LOAD_1_NUM=$(echo "$LOAD_1" | sed 's/,//')
    LOAD_5_NUM=$(echo "$LOAD_5" | sed 's/,//')
    
    if (( $(echo "$LOAD_1_NUM > 5.0" | bc -l) )); then
        alerta "Carga elevada (1min): $LOAD_1 - Limite: 5.0"
    fi
    
    if (( $(echo "$LOAD_1_NUM > 6.0" | bc -l) )); then
        crise "CARGA CRÍTICA (1min): $LOAD_1 - Limite: 6.0"
    fi
    
    if (( $(echo "$LOAD_5_NUM > 5.0" | bc -l) )); then
        alerta "Carga elevada (5min): $LOAD_5 - Limite: 5.0"
    fi
    
    # 2. Verificar processos problemáticos
    PROBLEMATIC_PROCESSES=""
    
    # cloudd
    CLOUDD_CPU=$(ps aux | grep cloudd | grep -v grep | grep -v "root.*cloudd" | awk '{print $3}' | head -1)
    if [ -n "$CLOUDD_CPU" ] && (( $(echo "$CLOUDD_CPU > 40" | bc -l) )); then
        PROBLEMATIC_PROCESSES="$PROBLEMATIC_PROCESSES cloudd($CLOUDD_CPU%)"
        alerta "cloudd com CPU elevada: $CLOUDD_CPU%"
    fi
    
    # mediaanalysisd
    MEDIA_CPU=$(ps aux | grep mediaanalysisd | grep -v grep | awk '{print $3}' | head -1)
    if [ -n "$MEDIA_CPU" ] && (( $(echo "$MEDIA_CPU > 50" | bc -l) )); then
        PROBLEMATIC_PROCESSES="$PROBLEMATIC_PROCESSES mediaanalysisd($MEDIA_CPU%)"
        alerta "mediaanalysisd com CPU elevada: $MEDIA_CPU%"
    fi
    
    # fileproviderd
    FILEPROV_CPU=$(ps aux | grep fileproviderd | grep -v grep | awk '{print $3}' | head -1)
    if [ -n "$FILEPROV_CPU" ] && (( $(echo "$FILEPROV_CPU > 30" | bc -l) )); then
        PROBLEMATIC_PROCESSES="$PROBLEMATIC_PROCESSES fileproviderd($FILEPROV_CPU%)"
        alerta "fileproviderd com CPU elevada: $FILEPROV_CPU%"
    fi
    
    if [ -n "$PROBLEMATIC_PROCESSES" ]; then
        log "Processos problemáticos detectados: $PROBLEMATIC_PROCESSES"
    fi
    
    # 3. Verificar serviços Nexus
    log "Verificando serviços Nexus..."
    
    # OpenClaw Gateway
    if pgrep -f "openclaw-gateway" > /dev/null; then
        log "✅ OpenClaw Gateway: ONLINE"
    else
        alerta "❌ OpenClaw Gateway: OFFLINE"
    fi
    
    # WhatsApp Server (verificação simplificada)
    if ps aux | grep -i whatsapp | grep -v grep > /dev/null; then
        log "✅ WhatsApp Server: ONLINE"
    else
        log "❌ WhatsApp Server: OFFLINE"
    fi
    
    # 4. Verificar scripts de contenção
    CONTAINMENT_SCRIPTS=0
    
    if pgrep -f "contencao_mediaanalysisd.sh" > /dev/null; then
        CONTAINMENT_SCRIPTS=$((CONTAINMENT_SCRIPTS + 1))
    else
        alerta "Script de contenção mediaanalysisd OFFLINE"
    fi
    
    if pgrep -f "contencao_cloudd.sh" > /dev/null; then
        CONTAINMENT_SCRIPTS=$((CONTAINMENT_SCRIPTS + 1))
    else
        alerta "Script de contenção cloudd OFFLINE"
    fi
    
    if pgrep -f "contencao_fileproviderd.sh" > /dev/null; then
        CONTAINMENT_SCRIPTS=$((CONTAINMENT_SCRIPTS + 1))
    else
        alerta "Script de contenção fileproviderd OFFLINE"
    fi
    
    log "Scripts de contenção ativos: $CONTAINMENT_SCRIPTS/3"
    
    # 5. Verificar uso de memória
    MEMORY_USED=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
    MEMORY_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    MEMORY_TOTAL=$((MEMORY_USED + MEMORY_FREE))
    MEMORY_PERCENT=$((MEMORY_USED * 100 / MEMORY_TOTAL))
    
    log "Uso de memória: ${MEMORY_PERCENT}% (${MEMORY_USED} páginas ativas)"
    
    if [ "$MEMORY_PERCENT" -gt 85 ]; then
        alerta "Uso de memória elevado: ${MEMORY_PERCENT}%"
    fi
    
    if [ "$MEMORY_PERCENT" -gt 95 ]; then
        crise "MEMÓRIA CRÍTICA: ${MEMORY_PERCENT}%"
    fi
    
    # 6. Resumo do status
    if (( $(echo "$LOAD_1_NUM > 6.0" | bc -l) )) || [ -n "$PROBLEMATIC_PROCESSES" ]; then
        STATUS="⚠️  ATENÇÃO"
    elif (( $(echo "$LOAD_1_NUM > 5.0" | bc -l) )); then
        STATUS="🔶 ALERTA"
    else
        STATUS="✅ NORMAL"
    fi
    
    log "Status do sistema: $STATUS"
    log "--- Fim da verificação ---"
    echo "" >> "$LOG_FILE"
    
    # Aguardar próximo ciclo
    sleep "$CHECK_INTERVAL"
done