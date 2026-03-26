#!/bin/bash

# Script para desabilitar temporariamente o fileproviderd
# Nexus Orchestrator - 25/03/2026

echo "=== DESABILITAÇÃO TEMPORÁRIA FILEPROVIDERD ==="
echo "Hora: $(date)"
echo ""

# Backup do estado atual
echo "1. Fazendo backup do estado atual..."
launchctl list | grep -i fileprovider > /tmp/fileprovider_backup_$(date +%s).txt
ps aux | grep fileproviderd > /tmp/fileprovider_processes_$(date +%s).txt

echo "2. Verificando processos fileproviderd ativos..."
pids=$(pgrep -x fileproviderd)
if [ -n "$pids" ]; then
    echo "  Processos encontrados: $pids"
    echo "  Terminando processos..."
    for pid in $pids; do
        echo "    Terminando PID $pid..."
        kill -15 $pid 2>/dev/null
        sleep 1
        if ps -p $pid > /dev/null 2>&1; then
            echo "    Forçando término (SIGKILL)..."
            kill -9 $pid 2>/dev/null
        fi
    done
else
    echo "  Nenhum processo ativo encontrado."
fi

echo "3. Desabilitando serviço FileProvider..."
# Tentar desabilitar via launchctl
sudo launchctl disable system/com.apple.FileProvider 2>/dev/null || echo "  Nota: Precisa de sudo para desabilitar completamente"

echo "4. Verificando se há outros serviços relacionados..."
launchctl list | grep -i -E "(cloud|bird|file)" | head -10

echo "5. Monitorando por novos processos (30 segundos)..."
for i in {1..30}; do
    new_pids=$(pgrep -x fileproviderd 2>/dev/null)
    if [ -n "$new_pids" ]; then
        echo "  ALERTA: Novo processo fileproviderd detectado: $new_pids"
        echo "  Terminando..."
        kill -9 $new_pids 2>/dev/null
    fi
    sleep 1
done

echo "6. Status final..."
echo "  Load Avg: $(uptime | awk -F'load averages: ' '{print $2}')"
echo "  Processos fileproviderd: $(pgrep -x fileproviderd | wc -l)"
echo "  Top 5 processos por CPU:"
ps aux | sort -nrk 3 | head -5

echo ""
echo "=== INSTRUÇÕES PARA REATIVAÇÃO ==="
echo "Para reativar o fileproviderd quando o sistema estiver estável:"
echo "1. sudo launchctl enable system/com.apple.FileProvider"
echo "2. sudo launchctl load /System/Library/LaunchDaemons/com.apple.FileProvider.plist"
echo "3. Monitorar por 5 minutos para garantir estabilidade"
echo ""
echo "=== ALERTA ==="
echo "Com o fileproviderd desabilitado:"
echo "- iCloud Drive não sincronizará"
echo "- Algumas apps podem não acessar arquivos do iCloud"
echo "- Funcionalidade será restaurada após reativação"
echo ""
echo "Intervenção concluída em: $(date)"