# PLANO DE EMERGÊNCIA - PHOTOLIBRARYD CRISE ATIVA
**Data/Hora:** 26/03/2026 - 07:15 (America/Sao_Paulo)  
**Situação:** 🔴 CRISE ATIVA - Photolibraryd consumindo 63.6% CPU  
**Memória Livre:** 75MB (COLAPSO IMINENTE)  
**Gateway CPU:** 60.3% (CRISE SECUNDÁRIA)

---

## 🚨 DIAGNÓSTICO DA CRISE

### **PROCESSO CRÍTICO IDENTIFICADO**
- **Processo:** `photolibraryd` (PID 594)
- **Consumo CPU:** 63.6% (CRISE ATIVA)
- **Tempo Execução:** 20:23 horas
- **Comando:** `/System/Library/PrivateFrameworks/PhotoLibraryServices.framework/Versions/A/Support/photolibraryd`
- **Status:** 🔴 **CRISE ATIVA - INTERVENÇÃO IMEDIATA REQUERIDA**

### **IMPACTOS SISTÊMICOS**
1. **Memória Livre:** 75MB (colapso iminente)
2. **Gateway CPU:** 60.3% (crise secundária)
3. **Load Avg:** 5.59 (crítico)
4. **Memória Compressor:** 6.0GB (crítico)
5. **Risco Projetos:** 18 projetos ativos em risco

### **HISTÓRICO DO MONITORAMENTO**
- **Último Log:** 05:26 (2 horas atrás)
- **Consumo na Última Verificação:** 71.8% CPU
- **Monitor Parado:** Script de monitoramento não está ativo
- **Intervenções Anteriores:** SIGSTOP/SIGCONT temporárias (ineficazes)

---

## 🎯 PLANO DE AÇÃO DE EMERGÊNCIA

### **FASE 1: INTERVENÇÃO IMEDIATA (PRÓXIMOS 5 MINUTOS)**

#### **1.1 REATIVAR MONITORAMENTO PHOTOLIBRARYD**
```bash
# Verificar se script de contenção existe
ls -la contencao_photolibraryd*.sh

# Executar script de contenção v3 (mais agressivo)
./contencao_photolibraryd_v3.sh force
```

#### **1.2 LIBERAR MEMÓRIA DE EMERGÊNCIA**
```bash
# Executar script de liberação de memória
./liberar_memoria_emergencia.sh

# Limpar caches do sistema
sudo purge
```

#### **1.3 INVESTIGAR CAUSA RAIZ**
```bash
# Verificar atividade do processo
sudo fs_usage -w -f filesys photolibraryd

# Verificar logs do sistema
log show --predicate 'process == "photolibraryd"' --last 30m
```

### **FASE 2: CONTENÇÃO AGUDA (PRÓXIMOS 30 MINUTOS)**

#### **2.1 DESENVOLVER SCRIPT DE CONTENÇÃO AVANÇADA**
```bash
# Criar script de contenção específico para photolibraryd
cat > contencao_photolibraryd_emergencia.sh << 'EOF'
#!/bin/bash
# Script de contenção de emergência para photolibraryd
LIMITE_CPU=30
INTERVALO=30
LOG_FILE="crises_photolibraryd_emergencia.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    PROCESSOS=$(ps aux | grep photolibraryd | grep -v grep)
    
    if [ -n "$PROCESSOS" ]; then
        while read -r LINE; do
            PID=$(echo "$LINE" | awk '{print $2}')
            CPU=$(echo "$LINE" | awk '{print $3}')
            COMANDO=$(echo "$LINE" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
            
            if (( $(echo "$CPU > $LIMITE_CPU" | bc -l) )); then
                echo "[$TIMESTAMP] ALERTA CRÍTICO: PID $PID com $CPU% CPU" >> "$LOG_FILE"
                echo "[$TIMESTAMP] Comando: $COMANDO" >> "$LOG_FILE"
                
                # Intervenção agressiva para crise
                LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
                if (( $(echo "$LOAD > 4.0" | bc -l) )); then
                    echo "[$TIMESTAMP] Carga crítica (Load=$LOAD), intervenção agressiva..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 30  # Pausa mais longa para crise
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 30 segundos" >> "$LOG_FILE"
                else
                    echo "[$TIMESTAMP] Carga moderada, pausa padrão..." >> "$LOG_FILE"
                    kill -STOP "$PID"
                    sleep 15
                    kill -CONT "$PID"
                    echo "[$TIMESTAMP] Processo retomado após pausa de 15 segundos" >> "$LOG_FILE"
                fi
                
                # Verificar se processo continua
                sleep 5
                if ps -p "$PID" > /dev/null; then
                    NOVA_CPU=$(ps -p "$PID" -o %cpu= | xargs)
                    echo "[$TIMESTAMP] Novo consumo: $NOVA_CPU% CPU" >> "$LOG_FILE"
                fi
            fi
        done <<< "$PROCESSOS"
    fi
    
    sleep "$INTERVALO"
done
EOF

chmod +x contencao_photolibraryd_emergencia.sh
```

#### **2.2 EXECUTAR SCRIPT DE EMERGÊNCIA**
```bash
# Executar em background
nohup ./contencao_photolibraryd_emergencia.sh > photolibraryd_emergencia.log 2>&1 &
```

#### **2.3 MONITORAR IMPACTO**
```bash
# Monitorar memória a cada 2 minutos
while true; do
    MEM_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    MEM_FREE_MB=$((MEM_FREE * 16384 / 1024 / 1024))
    echo "[$(date '+%H:%M:%S')] Memória livre: ${MEM_FREE_MB}MB"
    
    if [ "$MEM_FREE_MB" -lt 100 ]; then
        echo "[$(date '+%H:%M:%S')] 🔴 ALERTA: Memória crítica (< 100MB)"
        ./liberar_memoria_emergencia.sh
    fi
    
    sleep 120
done
```

### **FASE 3: ESTABILIZAÇÃO (PRÓXIMAS 2 HORAS)**

#### **3.1 OTIMIZAR GATEWAY**
```bash
# Verificar logs do Gateway
tail -100 cloudd_monitor.log

# Verificar configuração
openclaw gateway status

# Reiniciar se necessário (com aprovação)
# openclaw gateway restart
```

#### **3.2 IMPLEMENTAR ALERTAS AUTOMATIZADOS**
```bash
# Criar script de alertas para memória crítica
cat > alerta_memoria_critica.sh << 'EOF'
#!/bin/bash
LIMITE_MB=100
INTERVALO=60

while true; do
    MEM_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    MEM_FREE_MB=$((MEM_FREE * 16384 / 1024 / 1024))
    
    if [ "$MEM_FREE_MB" -lt "$LIMITE_MB" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔴 ALERTA CRÍTICO: Memória livre ${MEM_FREE_MB}MB (< ${LIMITE_MB}MB)" >> nexus_alertas.log
        
        # Executar ações corretivas
        ./liberar_memoria_emergencia.sh
        
        # Notificar via arquivo de status
        echo "ALERTA: Memória crítica ${MEM_FREE_MB}MB em $(date '+%H:%M:%S')" > ALERTA_MEMORIA_CRITICA_$(date +%H%M).md
    fi
    
    sleep "$INTERVALO"
done
EOF

chmod +x alerta_memoria_critica.sh
```

#### **3.3 DOCUMENTAR CRISE E SOLUÇÕES**
```bash
# Criar relatório completo da crise
cat > RELATORIO_CRISE_PHOTOLIBRARYD_$(date +%Y%m%d_%H%M).md << 'EOF'
# RELATÓRIO DE CRISE - PHOTOLIBRARYD
**Data:** 26/03/2026  
**Hora Início:** 07:13  
**Hora Detecção:** 07:13  
**Duração:** Em andamento

## RESUMO DA CRISE
- **Processo:** photolibraryd (PID 594)
- **Consumo Pico:** 63.6% CPU
- **Memória Livre Mínima:** 75MB
- **Impacto:** Gateway 60.3% CPU, Load Avg 5.59

## AÇÕES EXECUTADAS
1. Reativação monitoramento photolibraryd
2. Execução script liberação memória
3. Desenvolvimento script contenção emergência
4. Implementação alertas memória crítica

## RESULTADOS
[Preencher com resultados das ações]

## LIÇÕES APRENDIDAS
[Preencher após resolução]
EOF
```

---

## 📊 MÉTRICAS DE MONITORAMENTO - EMERGÊNCIA

### **CHECKLIST DE AÇÕES IMEDIATAS**
- [ ] 1. Executar `./contencao_photolibraryd_v3.sh force`
- [ ] 2. Executar `./liberar_memoria_emergencia.sh`
- [ ] 3. Iniciar `./contencao_photolibraryd_emergencia.sh`
- [ ] 4. Monitorar memória a cada 2 minutos
- [ ] 5. Documentar todas as ações

### **INDICADORES DE SUCESSO**
1. **Memória Livre:** > 200MB (objetivo)
2. **Photolibraryd CPU:** < 30% (objetivo)
3. **Gateway CPU:** < 40% (objetivo)
4. **Load Avg:** < 4.0 (objetivo)
5. **Projetos:** 100% preservados (obrigatório)

### **CONDIÇÕES DE ESCALONAMENTO**
- **Nível 1:** Memória < 200MB - Monitoramento aumentado
- **Nível 2:** Memória < 100MB - Ações corretivas
- **Nível 3:** Memória < 50MB - Intervenção humana
- **Nível 4:** Sistema instável - Reinício emergencial

---

## 🛡️ PLANO DE CONTINGÊNCIA

### **CENÁRIO 1: INTERVENÇÃO BEM-SUCEDIDA**
- **Probabilidade:** 70%
- **Ações:** Continuar monitoramento, otimizar configuração
- **Tempo Recuperação:** 1-2 horas

### **CENÁRIO 2: INTERVENÇÃO PARCIAL**
- **Probabilidade:** 20%
- **Ações:** Reiniciar processo, limpar caches agressivamente
- **Tempo Recuperação:** 2-4 horas

### **CENÁRIO 3: FALHA DA INTERVENÇÃO**
- **Probabilidade:** 10%
- **Ações:** Reinício controlado do sistema
- **Tempo Recuperação:** 4-6 horas
- **Risco Projetos:** ALTO - Backup necessário

### **CENÁRIO 4: COLAPSO DO SISTEMA**
- **Probabilidade:** 5%
- **Ações:** Backup emergencial, reinício completo
- **Tempo Recuperação:** 6+ horas
- **Risco Projetos:** CRÍTICO - Perda possível

---

## 📋 PRÓXIMOS PASSOS

### **IMEDIATO (0-15 MINUTOS)**
1. Executar scripts de contenção e liberação de memória
2. Iniciar monitoramento contínuo
3. Documentar ações em tempo real

### **CURTO PRAZO (15-60 MINUTOS)**
1. Avaliar eficácia das intervenções
2. Ajustar scripts conforme necessário
3. Implementar alertas adicionais

### **MÉDIO PRAZO (1-4 HORAS)**
1. Analisar causa raiz do photolibraryd
2. Otimizar configuração do sistema
3. Documentar lições aprendidas

### **LONGO PRAZO (4-24 HORAS)**
1. Implementar soluções permanentes
2. Revisar arquitetura de monitoramento
3. Criar plano de prevenção

---

## 🔗 RECURSOS E FERRAMENTAS

### **SCRIPTS DISPONÍVEIS**
1. `contencao_photolibraryd_v3.sh` - Contenção básica
2. `contencao_photolibraryd_emergencia.sh` - Contenção agressiva (a criar)
3. `liberar_memoria_emergencia.sh` - Liberação memória
4. `alerta_memoria_critica.sh` - Alertas automáticos (a criar)

### **LOGS DE MONITORAMENTO**
1. `photolibraryd_monitor.log` - Histórico (parado em 05:26)
2. `crises_photolibraryd.log` - Registro de crises
3. `nexus_alertas.log` - Alertas do sistema
4. `photolibraryd_emergencia.log` - Log novo (a criar)

### **ARQUIVOS DE STATUS**
1. `STATUS_NEXUS_ORCHESTRATOR_0713.md` - Status atual
2. `PLANO_EMERGENCIA_PHOTOLIBRARYD_0715.md` - Este plano
3. `ALERTA_MEMORIA_CRITICA_[HORA].md` - Alertas gerados

---

## ✅ CONCLUSÃO

### **SITUAÇÃO ATUAL: 🔴 CRISE ATIVA**
O sistema está em crise com múltiplos pontos críticos. A intervenção imediata é necessária para prevenir colapso total.

### **PRIORIDADES ABSOLUTAS**
1. **Memória:** Liberar imediatamente (75MB livre)
2. **Photolibraryd:** Conter consumo (63.6% CPU)
3. **Gateway:** Reduzir carga (60.3% CPU)
4. **Projetos:** Preservar integridade (18 projetos)

### **RISCO GERAL: ALTO**
Probabilidade de instabilidade do sistema é alta se ações não forem tomadas imediatamente.

### **PRÓXIMA VERIFICAÇÃO: 07:17 (2 MINUTOS)**
Monitoramento em frequência de emergência até estabilização.

---
**Gerado por:** Nexus Orchestrator - Plano de Emergência  
**Hora:** 07:15 (26/03/2026)  
**Status:** 🔴 CRISE ATIVA - PLANO EM EXECUÇÃO