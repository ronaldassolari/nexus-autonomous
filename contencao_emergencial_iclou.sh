#!/bin/bash

# Script de contenção emergencial para processos iCloud
# Nexus Orchestrator - 25/03/2026

echo "=== CONTENÇÃO EMERGENCIAL iCLOUD ==="
echo "Hora: $(date)"
echo ""

# Função para verificar e conter processo
conter_processo() {
    local nome=$1
    local limite_cpu=$2
    
    echo "Verificando $nome..."
    
    # Encontrar PIDs
    pids=$(pgrep -x "$nome")
    
    if [ -z "$pids" ]; then
        echo "  Nenhum processo $nome encontrado."
        return 0
    fi
    
    for pid in $pids; do
        # Verificar consumo de CPU
        cpu_usage=$(ps -p $pid -o %cpu= | awk '{print int($1)}')
        
        if [ "$cpu_usage" -gt "$limite_cpu" ]; then
            echo "  ALERTA: PID $pid com $cpu_usage% CPU (limite: $limite_cpu%)"
            
            # Tentar SIGTERM primeiro (graceful)
            echo "  Enviando SIGTERM..."
            kill -15 $pid
            sleep 2
            
            # Verificar se ainda existe
            if ps -p $pid > /dev/null 2>&1; then
                echo "  Processo ainda ativo. Enviando SIGKILL..."
                kill -9 $pid
                sleep 1
                
                if ps -p $pid > /dev/null 2>&1; then
                    echo "  ERRO: Não foi possível terminar PID $pid"
                    return 1
                else
                    echo "  SUCESSO: PID $pid terminado com SIGKILL"
                fi
            else
                echo "  SUCESSO: PID $pid terminado com SIGTERM"
            fi
        else
            echo "  OK: PID $pid com $cpu_usage% CPU (abaixo do limite)"
        fi
    done
    
    return 0
}

# Verificar status do sistema antes
echo "=== STATUS ANTES DA INTERVENÇÃO ==="
load_avg=$(sysctl -n vm.loadavg | awk '{print $2}')
cpu_idle=$(top -l 1 | grep "CPU usage" | awk '{print $7}' | sed 's/%//')
mem_free=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')

echo "Load Avg (1min): $load_avg"
echo "CPU Idle: $cpu_idle%"
echo "Memória Livre: $mem_free MB"
echo ""

# Conter processos problemáticos
echo "=== APLICANDO CONTENÇÃO ==="

conter_processo "fileproviderd" 30
conter_processo "bird" 20
conter_processo "cloudd" 25

echo ""
echo "=== STATUS APÓS INTERVENÇÃO ==="
sleep 3

load_avg_after=$(sysctl -n vm.loadavg | awk '{print $2}')
cpu_idle_after=$(top -l 1 | grep "CPU usage" | awk '{print $7}' | sed 's/%//')
mem_free_after=$(top -l 1 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')

echo "Load Avg (1min): $load_avg_after"
echo "CPU Idle: $cpu_idle_after%"
echo "Memória Livre: $mem_free_after MB"
echo ""

# Calcular melhoria
load_diff=$(echo "$load_avg - $load_avg_after" | bc)
cpu_diff=$(echo "$cpu_idle_after - $cpu_idle" | bc)
mem_diff=$(echo "$mem_free_after - $mem_free" | bc)

echo "=== RESULTADO ==="
echo "Redução Load Avg: $load_diff"
echo "Aumento CPU Idle: $cpu_diff%"
echo "Aumento Memória Livre: $mem_diff MB"

if [ $(echo "$load_avg_after < 5" | bc) -eq 1 ] && [ $(echo "$cpu_idle_after > 70" | bc) -eq 1 ]; then
    echo "✅ INTERVENÇÃO BEM-SUCEDIDA"
else
    echo "⚠️  INTERVENÇÃO PARCIALMENTE BEM-SUCEDIDA"
    echo "   Considerar ações adicionais"
fi

echo ""
echo "=== PROCESSOS RESTANTES ==="
ps aux | grep -E "(fileproviderd|bird|cloudd)" | grep -v grep | head -10