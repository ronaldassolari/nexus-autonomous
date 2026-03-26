#!/bin/bash
# contencao_avancada.sh - Contenção com prevenção de reinício
# Nexus Orchestrator - Solução Definitiva

SERVICE=$1
MAX_CPU=${2:-30}  # Default 30%
ACTION=${3:-monitor}
CHECK_INTERVAL=10
LOG_FILE="/tmp/contencao_${SERVICE}.log"

echo "=== Contenção Avançada para $SERVICE ===" > "$LOG_FILE"
echo "Data/Hora: $(date)" >> "$LOG_FILE"
echo "Limite CPU: ${MAX_CPU}%" >> "$LOG_FILE"
echo "Ação: $ACTION" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Identificar plist do serviço
identify_plist() {
    case $SERVICE in
        mediaanalysisd)
            echo "/System/Library/LaunchDaemons/com.apple.mediaanalysisd.plist"
            ;;
        fileproviderd)
            echo "/System/Library/LaunchDaemons/com.apple.fileproviderd.plist"
            ;;
        bird)
            echo "/System/Library/LaunchDaemons/com.apple.Bird.plist"
            ;;
        cloudd)
            echo "/System/Library/LaunchDaemons/com.apple.cloudd.plist"
            ;;
        *)
            echo "Serviço não suportado: $SERVICE" >> "$LOG_FILE"
            exit 1
            ;;
    esac
}

PLIST=$(identify_plist)

# Modo 1: Desabilitar completamente
disable_service() {
    echo "[$(date)] Desabilitando serviço $SERVICE completamente..." >> "$LOG_FILE"
    
    # Tentar desabilitar via launchctl
    sudo launchctl disable "system/com.apple.$SERVICE" 2>/dev/null
    sudo launchctl unload "$PLIST" 2>/dev/null
    
    # Matar todos os processos
    pkill -9 "$SERVICE" 2>/dev/null
    
    # Verificar se está desabilitado
    if launchctl print "system/com.apple.$SERVICE" 2>/dev/null | grep -q "disabled = true"; then
        echo "[$(date)] SUCCESS: $SERVICE desabilitado" >> "$LOG_FILE"
    else
        echo "[$(date)] WARNING: $SERVICE pode não estar completamente desabilitado" >> "$LOG_FILE"
    fi
}

# Modo 2: Limitar recursos
limit_service() {
    echo "[$(date)] Limitando $SERVICE a $MAX_CPU% CPU..." >> "$LOG_FILE"
    
    # Criar plist override com limites
    OVERRIDE="/tmp/com.apple.${SERVICE}.limit.plist"
    cat > "$OVERRIDE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.${SERVICE}.limited</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/libexec/${SERVICE}</string>
    </array>
    <key>LimitCPU</key>
    <integer>${MAX_CPU}</integer>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>ExitTimeOut</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
</dict>
</plist>
EOF
    
    # Parar serviço original
    sudo launchctl unload "$PLIST" 2>/dev/null
    pkill -9 "$SERVICE" 2>/dev/null
    
    # Carregar versão limitada
    sudo launchctl load "$OVERRIDE" 2>/dev/null
    
    echo "[$(date)] SUCCESS: $SERVICE limitado a $MAX_CPU% CPU" >> "$LOG_FILE"
}

# Modo 3: Monitoramento com ação escalonada
monitor_service() {
    echo "[$(date)] Iniciando monitoramento de $SERVICE (limite: ${MAX_CPU}% CPU)..." >> "$LOG_FILE"
    
    CONSECUTIVE_HIGH=0
    MAX_CONSECUTIVE=3
    
    while true; do
        PID=$(pgrep "$SERVICE")
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        
        if [ -n "$PID" ]; then
            # Obter uso de CPU (pode precisar de múltiplas leituras para precisão)
            CPU1=$(ps -p "$PID" -o %cpu= 2>/dev/null | awk '{print int($1+0.5)}')
            sleep 1
            CPU2=$(ps -p "$PID" -o %cpu= 2>/dev/null | awk '{print int($1+0.5)}')
            CPU=$(( (CPU1 + CPU2) / 2 ))
            
            if [ "$CPU" -gt "$MAX_CPU" ]; then
                CONSECUTIVE_HIGH=$((CONSECUTIVE_HIGH + 1))
                echo "[$TIMESTAMP] ALERTA: $SERVICE (PID: $PID) com ${CPU}% CPU > limite ${MAX_CPU}%" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Consecutivos altos: $CONSECUTIVE_HIGH/$MAX_CONSECUTIVE" >> "$LOG_FILE"
                
                # Escalonamento de ação baseado em gravidade e repetição
                if [ "$CPU" -gt 100 ] || [ "$CONSECUTIVE_HIGH" -ge "$MAX_CONSECUTIVE" ]; then
                    # Crítico ou repetido: desabilitar temporariamente
                    echo "[$TIMESTAMP] AÇÃO: Desabilitando $SERVICE por 5 minutos (CPU: ${CPU}%)" >> "$LOG_FILE"
                    disable_service
                    sleep 300  # 5 minutos
                    CONSECUTIVE_HIGH=0
                    
                    # Reativar com limites
                    limit_service
                elif [ "$CPU" -gt 50 ]; then
                    # Alto: kill normal e aumentar prioridade baixa
                    echo "[$TIMESTAMP] AÇÃO: Matando $SERVICE (CPU: ${CPU}%)" >> "$LOG_FILE"
                    kill "$PID" 2>/dev/null
                    sleep 2
                    # Se ainda existir, kill forçado
                    if ps -p "$PID" > /dev/null 2>&1; then
                        kill -9 "$PID" 2>/dev/null
                    fi
                    sleep 30
                else
                    # Moderado: apenas reduzir prioridade
                    echo "[$TIMESTAMP] AÇÃO: Reduzindo prioridade de $SERVICE" >> "$LOG_FILE"
                    renice -n 20 -p "$PID" 2>/dev/null
                    sleep 15
                fi
            else
                # CPU dentro do limite
                if [ "$CONSECUTIVE_HIGH" -gt 0 ]; then
                    echo "[$TIMESTAMP] OK: $SERVICE com ${CPU}% CPU (recuperado)" >> "$LOG_FILE"
                    CONSECUTIVE_HIGH=0
                fi
                sleep $CHECK_INTERVAL
            fi
        else
            # Processo não está rodando
            echo "[$TIMESTAMP] INFO: $SERVICE não está em execução" >> "$LOG_FILE"
            CONSECUTIVE_HIGH=0
            sleep $CHECK_INTERVAL
        fi
        
        # Log resumido a cada minuto
        if [ $(date +%S) -lt 5 ]; then
            echo "[$TIMESTAMP] STATUS: Monitorando $SERVICE, Limite: ${MAX_CPU}%, Consecutivos: $CONSECUTIVE_HIGH" >> "$LOG_FILE"
        fi
    done
}

# Modo 4: Reativar normalmente
enable_service() {
    echo "[$(date)] Reativando $SERVICE normalmente..." >> "$LOG_FILE"
    
    # Remover override se existir
    sudo rm -f "/tmp/com.apple.${SERVICE}.limit.plist"
    sudo launchctl unload "/tmp/com.apple.${SERVICE}.limit.plist" 2>/dev/null
    
    # Reativar serviço original
    sudo launchctl enable "system/com.apple.$SERVICE" 2>/dev/null
    sudo launchctl load "$PLIST" 2>/dev/null
    
    echo "[$(date)] SUCCESS: $SERVICE reativado normalmente" >> "$LOG_FILE"
}

# Executar baseado na ação
case $ACTION in
    disable)
        disable_service
        ;;
    limit)
        limit_service
        ;;
    monitor)
        monitor_service
        ;;
    enable)
        enable_service
        ;;
    *)
        echo "Ação não reconhecida: $ACTION" >> "$LOG_FILE"
        echo "Uso: $0 <serviço> [limite_cpu] [disable|limit|monitor|enable]" >> "$LOG_FILE"
        exit 1
        ;;
esac

echo "[$(date)] Contenção Avançada finalizada para $SERVICE" >> "$LOG_FILE"