#!/bin/bash

# Script de monitoramento preventivo da Parallels VM
# Verifica se a VM está consumindo recursos excessivos e a interrompe se necessário

# Configurações
VM_PROCESS="prl_vm_app"
CPU_THRESHOLD=30.0   # Limite de consumo de CPU (%) - Configuração original solicitada
LOAD_THRESHOLD=8.0   # Limite de carga do sistema - Configuração original solicitada
LOG_FILE="memory/parallels_monitor.log"
ALERT_FILE="memory/parallels_alerts.md"

# Função para log
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

# Função para criar alerta
create_alert() {
    local message="$1"
    echo "## ⚠️ ALERTA PARALLELS VM - $(date '+%Y-%m-%d %H:%M:%S')" >> "$ALERT_FILE"
    echo "$message" >> "$ALERT_FILE"
    echo "" >> "$ALERT_FILE"
}

# Verificar se o processo da VM está em execução
vm_pid=$(pgrep "$VM_PROCESS")

if [ -z "$vm_pid" ]; then
    log_message "✅ Parallels VM não está em execução"
    exit 0
fi

# Obter consumo de CPU da VM
vm_cpu=$(ps -p "$vm_pid" -o %cpu | tail -1 | tr -d ' ')

# Obter carga do sistema (macOS)
load_avg=$(uptime | sed 's/.*load averages: //' | awk '{print $1}' | tr -d ',')

log_message "📊 Monitoramento: VM PID=$vm_pid, CPU=${vm_cpu}%, Load=$load_avg"

# Verificar condições para intervenção
need_intervention=false
reason=""

if (( $(echo "$vm_cpu > $CPU_THRESHOLD" | bc -l) )); then
    need_intervention=true
    reason="Consumo de CPU alto (${vm_cpu}% > ${CPU_THRESHOLD}%)"
elif (( $(echo "$load_avg > $LOAD_THRESHOLD" | bc -l) )); then
    need_intervention=true
    reason="Carga do sistema alta ($load_avg > $LOAD_THRESHOLD)"
fi

if [ "$need_intervention" = true ]; then
    log_message "🚨 INTERVENÇÃO NECESSÁRIA: $reason"
    
    # Interromper a VM e processos relacionados
    log_message "🔧 Interrompendo VM e processos relacionados..."
    
    # Interromper a VM principal
    if pkill -9 "$VM_PROCESS"; then
        log_message "✅ Parallels VM interrompida com sucesso"
    
    # Interromper outros processos do Parallels que podem reiniciar a VM
    pkill -9 "prl_client_app" 2>/dev/null && log_message "✅ Processo prl_client_app interrompido"
    pkill -9 "prl_disp_service" 2>/dev/null && log_message "✅ Processo prl_disp_service interrompido"
        
        # Criar alerta detalhado
        alert_message="**Intervenção executada:**\n"
        alert_message+="- Processo: $VM_PROCESS (PID: $vm_pid)\n"
        alert_message+="- Consumo CPU: ${vm_cpu}%\n"
        alert_message+="- Carga sistema: $load_avg\n"
        alert_message+="- Motivo: $reason\n"
        alert_message+="- Ação: VM interrompida (pkill -9)\n"
        alert_message+="- Hora: $(date '+%H:%M:%S BRT')"
        
        create_alert "$alert_message"
        
        # Registrar no arquivo de memória diária
        echo "## ⚠️ INTERVENÇÃO AUTOMÁTICA PARALLELS VM - $(date '+%H:%M BRT')" >> "memory/$(date '+%Y-%m-%d').md"
        echo "VM interrompida automaticamente: $reason" >> "memory/$(date '+%Y-%m-%d').md"
        echo "" >> "memory/$(date '+%Y-%m-%d').md"
    else
        log_message "❌ Falha ao interromper Parallels VM"
    fi
else
    log_message "✅ Status OK: VM em execução dentro dos limites"
fi

# Verificar configuração de auto-inicialização
vm_config="/Users/ronaldsantosassolari/Parallels/Windows 11.pvm/config.pvs"
if [ -f "$vm_config" ]; then
    autostart_setting=$(grep -A1 "<AutoStart>" "$vm_config" | tail -1 | tr -d ' ')
    if [ "$autostart_setting" = "1" ]; then
        log_message "⚠️ AVISO: VM configurada para auto-inicialização (AutoStart=1)"
    else
        log_message "✅ VM NÃO configurada para auto-inicialização (AutoStart=$autostart_setting)"
    fi
fi