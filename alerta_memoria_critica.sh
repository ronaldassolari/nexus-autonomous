#!/bin/bash
# Script de alertas para memória crítica
LIMITE_MB=100
INTERVALO=60
LOG_FILE="nexus_alertas_memoria.log"

echo "========================================"
echo "[ALERTA] NEXUS ORCHESTRATOR - MONITORAMENTO DE MEMÓRIA"
echo "[ALERTA] Iniciando monitoramento de memória crítica"
echo "========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limite: ${LIMITE_MB}MB livre"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Intervalo: ${INTERVALO} segundos"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log: $LOG_FILE"
echo "========================================"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Obter memória livre
    MEM_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    MEM_FREE_MB=$((MEM_FREE * 16384 / 1024 / 1024))
    
    # Obter carga do sistema
    LOAD_1MIN=$(sysctl -n vm.loadavg | awk '{print $2}')
    
    # Verificar photolibraryd
    PHOTO_CPU=$(ps aux | grep photolibraryd | grep -v grep | awk '{print $3}' | head -1)
    if [ -z "$PHOTO_CPU" ]; then
        PHOTO_CPU="0.0"
    fi
    
    # Determinar nível de alerta
    if [ "$MEM_FREE_MB" -lt 50 ]; then
        NIVEL="🔴 CRÍTICO"
        COR="\033[0;31m"
        ACAO="INTERVENÇÃO IMEDIATA REQUERIDA"
    elif [ "$MEM_FREE_MB" -lt 100 ]; then
        NIVEL="🟠 ALTO"
        COR="\033[0;33m"
        ACAO="AÇÃO CORRETIVA NECESSÁRIA"
    elif [ "$MEM_FREE_MB" -lt 200 ]; then
        NIVEL="🟡 MODERADO"
        COR="\033[0;33m"
        ACAO="MONITORAMENTO AUMENTADO"
    else
        NIVEL="🟢 NORMAL"
        COR="\033[0;32m"
        ACAO="SITUAÇÃO ESTÁVEL"
    fi
    
    # Registrar no log
    echo "[$TIMESTAMP] $NIVEL: Memória livre ${MEM_FREE_MB}MB (< ${LIMITE_MB}MB)" >> "$LOG_FILE"
    echo "[$TIMESTAMP] Load Avg: $LOAD_1MIN | Photolibraryd CPU: ${PHOTO_CPU}%" >> "$LOG_FILE"
    echo "[$TIMESTAMP] Ação: $ACAO" >> "$LOG_FILE"
    
    # Tomar ação se necessário
    if [ "$MEM_FREE_MB" -lt "$LIMITE_MB" ]; then
        echo "[$TIMESTAMP] 🔴 ALERTA CRÍTICO: Memória livre ${MEM_FREE_MB}MB (< ${LIMITE_MB}MB)" >> nexus_alertas.log
        
        # Criar arquivo de alerta
        ALERTA_FILE="ALERTA_MEMORIA_CRITICA_$(date +%H%M).md"
        cat > "$ALERTA_FILE" << EOF
# ALERTA DE MEMÓRIA CRÍTICA
**Data/Hora:** $(date '+%d/%m/%Y - %H:%M')  
**Memória Livre:** ${MEM_FREE_MB}MB  
**Limite:** ${LIMITE_MB}MB  
**Nível:** $NIVEL

## STATUS DO SISTEMA
- **Load Avg (1min):** $LOAD_1MIN
- **Photolibraryd CPU:** ${PHOTO_CPU}%
- **Ação Recomendada:** $ACAO

## AÇÕES IMEDIATAS
1. Verificar scripts de contenção
2. Executar liberação de memória
3. Monitorar processos críticos
4. Documentar situação

## PRÓXIMOS PASSOS
1. Investigar causa do consumo
2. Otimizar configuração
3. Implementar soluções permanentes

---
**Gerado por:** Nexus Orchestrator - Alerta de Memória  
**Status:** $NIVEL
EOF
        
        echo "[$TIMESTAMP] Arquivo de alerta criado: $ALERTA_FILE" >> "$LOG_FILE"
        
        # Executar ações corretivas se memória muito baixa
        if [ "$MEM_FREE_MB" -lt 80 ]; then
            echo "[$TIMESTAMP] Executando limpeza de memória de emergência..." >> "$LOG_FILE"
            if [ -f "./liberar_memoria_emergencia.sh" ]; then
                ./liberar_memoria_emergencia.sh >> "$LOG_FILE" 2>&1
                echo "[$TIMESTAMP] Script de liberação de memória executado" >> "$LOG_FILE"
            else
                echo "[$TIMESTAMP] Script de liberação não encontrado" >> "$LOG_FILE"
            fi
        fi
    fi
    
    # Verificar se photolibraryd está alto
    PHOTO_CPU_INT=$(echo "$PHOTO_CPU" | cut -d. -f1)
    if [ "$PHOTO_CPU_INT" -gt 40 ]; then
        echo "[$TIMESTAMP] ⚠️ ALERTA PHOTOLIBRARYD: ${PHOTO_CPU}% CPU" >> "$LOG_FILE"
        echo "[$TIMESTAMP] Verificando scripts de contenção..." >> "$LOG_FILE"
        
        # Verificar se scripts de contenção estão ativos
        if ! ps aux | grep -q "contencao_photolibraryd"; then
            echo "[$TIMESTAMP] ⚠️ Nenhum script de contenção ativo - iniciando..." >> "$LOG_FILE"
            if [ -f "./contencao_photolibraryd_v3.sh" ]; then
                nohup ./contencao_photolibraryd_v3.sh force > /dev/null 2>&1 &
                echo "[$TIMESTAMP] Script de contenção iniciado" >> "$LOG_FILE"
            fi
        fi
    fi
    
    echo "---" >> "$LOG_FILE"
    
    # Exibir status no console (opcional)
    echo -e "${COR}[$TIMESTAMP] Memória: ${MEM_FREE_MB}MB | Load: $LOAD_1MIN | Photo: ${PHOTO_CPU}% | Nível: $NIVEL\033[0m"
    
    sleep "$INTERVALO"
done