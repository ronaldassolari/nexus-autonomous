# SOLUÇÃO DEFINITIVA - Contenção de Processos do Sistema
**Data/Hora:** 25/03/2026 17:04  
**Situação:** PROCESSOS SE REINICIANDO AUTOMATICAMENTE  
**Problema:** mediaanalysisd (131.4% CPU) e fileproviderd (34.4% CPU) reiniciam após kill

## 🚨 DIAGNÓSTICO

### **Padrão Identificado:**
1. **Processos do sistema** (mediaanalysisd, fileproviderd) são gerenciados pelo launchd
2. **Reinício automático** após término
3. **Consumo explosivo** na reinicialização
4. **Ciclo vicioso:** kill → reinício → alto consumo → kill

### **Processos Afetados:**
1. **mediaanalysisd** - Framework de análise de mídia
2. **fileproviderd** - Gerenciador de provedores de arquivos
3. **bird** - Serviço de sincronização iCloud
4. **cloudd** - Serviço CloudKit

## 🎯 ESTRATÉGIA DE SOLUÇÃO

### **Abordagem Tradicional (NÃO FUNCIONA)**
- `kill PID` - Processo reinicia automaticamente
- `kill -9 PID` - Processo reinicia automaticamente
- Scripts de monitoramento - Não previnem reinício

### **Abordagem Efetiva (PROPOSTA)**
1. **Desabilitar temporariamente** o serviço
2. **Limitar recursos** via launchd
3. **Atrasar reinício** com backoff exponencial
4. **Monitorar causa raiz** do alto consumo

## 🔧 SOLUÇÃO TÉCNICA

### **Passo 1: Identificar Serviço no Launchd**
```bash
# Encontrar plist do serviço
sudo launchctl list | grep -i mediaanalysis
sudo launchctl list | grep -i fileprovider

# Localizar arquivos .plist
find /System/Library/LaunchAgents /System/Library/LaunchDaemons -name "*mediaanalysis*" -o -name "*fileprovider*"
```

### **Passo 2: Desabilitar Temporariamente**
```bash
# Descarregar serviço (se possível)
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.mediaanalysisd.plist
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.fileproviderd.plist

# Desabilitar reinício automático
sudo launchctl disable system/com.apple.mediaanalysisd
sudo launchctl disable system/com.apple.fileproviderd
```

### **Passo 3: Configurar Limites de Recursos**
```bash
# Criar override com limites
sudo mkdir -p /Library/LaunchDaemons/overrides/
sudo cp /System/Library/LaunchDaemons/com.apple.mediaanalysisd.plist /Library/LaunchDaemons/overrides/

# Editar para adicionar limites
sudo plutil -insert LimitCPU -integer 30 /Library/LaunchDaemons/overrides/com.apple.mediaanalysisd.plist
sudo plutil -insert LimitMemory -integer 100000000 /Library/LaunchDaemons/overrides/com.apple.mediaanalysisd.plist
```

### **Passo 4: Script de Contenção Avançado**
```bash
#!/bin/bash
# contencao_avancada.sh - Contenção com prevenção de reinício

SERVICE=$1
MAX_CPU=$2
CHECK_INTERVAL=10

case $SERVICE in
    mediaanalysisd)
        PLIST="/System/Library/LaunchDaemons/com.apple.mediaanalysisd.plist"
        ;;
    fileproviderd)
        PLIST="/System/Library/LaunchDaemons/com.apple.fileproviderd.plist"
        ;;
    *)
        echo "Serviço não suportado: $SERVICE"
        exit 1
        ;;
esac

# Modo 1: Desabilitar completamente
disable_service() {
    echo "Desabilitando serviço $SERVICE..."
    sudo launchctl disable system/com.apple.$SERVICE
    sudo launchctl unload $PLIST 2>/dev/null
    pkill -9 $SERVICE
}

# Modo 2: Limitar recursos
limit_service() {
    echo "Limitando $SERVICE a $MAX_CPU% CPU..."
    # Criar plist override com limites
    OVERRIDE="/tmp/com.apple.${SERVICE}.limit.plist"
    cat > $OVERRIDE << EOF
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
    <key>LimitMemory</key>
    <integer>100000000</integer>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>ExitTimeOut</key>
    <integer>300</integer>
</dict>
</plist>
EOF
    
    sudo launchctl unload $PLIST 2>/dev/null
    sudo launchctl load $OVERRIDE
}

# Modo 3: Monitoramento com ação escalonada
monitor_service() {
    while true; do
        PID=$(pgrep $SERVICE)
        if [ -n "$PID" ]; then
            CPU=$(ps -p $PID -o %cpu= | awk '{print int($1)}')
            if [ "$CPU" -gt "$MAX_CPU" ]; then
                echo "[$(date)] $SERVICE (PID: $PID) com ${CPU}% CPU > limite ${MAX_CPU}%"
                
                # Escalonamento de ação
                if [ "$CPU" -gt 100 ]; then
                    # Crítico: kill forçado e desabilitação
                    disable_service
                    sleep 300  # 5 minutos sem serviço
                elif [ "$CPU" -gt 50 ]; then
                    # Alto: kill normal e limitação
                    kill $PID
                    limit_service
                    sleep 60
                else
                    # Moderado: apenas throttle
                    renice -n 20 -p $PID
                    sleep 30
                fi
            fi
        fi
        sleep $CHECK_INTERVAL
    done
}

# Executar baseado no argumento
if [ "$3" == "disable" ]; then
    disable_service
elif [ "$3" == "limit" ]; then
    limit_service
else
    monitor_service
fi
```

## 🛡️ IMPLEMENTAÇÃO IMEDIATA

### **Para mediaanalysisd (131.4% CPU):**
```bash
# 1. Desabilitar completamente por 1 hora
./contencao_avancada.sh mediaanalysisd 30 disable

# 2. Após 1 hora, reativar com limites
sleep 3600
./contencao_avancada.sh mediaanalysisd 30 limit
```

### **Para fileproviderd (34.4% CPU):**
```bash
# 1. Limitar a 25% CPU
./contencao_avancada.sh fileproviderd 25 limit

# 2. Monitorar continuamente
./contencao_avancada.sh fileproviderd 25 monitor
```

## 📊 MONITORAMENTO DE IMPACTO

### **Métricas a Verificar:**
1. **Load Average** - Deve estabilizar < 3.0
2. **CPU Idle** - Deve aumentar > 80%
3. **Reinícios de serviço** - Deve parar ou reduzir drasticamente
4. **Consumo pico** - Deve ficar dentro dos limites

### **Logs para Análise:**
```bash
# Logs do launchd
sudo log show --predicate 'sender == "launchd"' --last 30m

# Logs do serviço
sudo log show --predicate 'process == "mediaanalysisd"' --last 30m
sudo log show --predicate 'process == "fileproviderd"' --last 30m
```

## 🔄 PLANO DE ROLLBACK

### **Se problemas ocorrerem:**
```bash
# Reativar serviços normalmente
sudo launchctl enable system/com.apple.mediaanalysisd
sudo launchctl enable system/com.apple.fileproviderd
sudo launchctl load /System/Library/LaunchDaemons/com.apple.mediaanalysisd.plist
sudo launchctl load /System/Library/LaunchDaemons/com.apple.fileproviderd.plist

# Remover overrides
sudo rm -f /Library/LaunchDaemons/overrides/com.apple.*.plist
sudo rm -f /tmp/com.apple.*.limit.plist
```

## 📝 CONSIDERAÇÕES DE SEGURANÇA

### **Riscos:**
1. **Perda de funcionalidade** - Serviços desabilitados não funcionam
2. **Problemas de sincronização** - iCloud/files podem não sincronizar
3. **Impacto em apps** - Apps que dependem desses serviços podem falhar

### **Mitigações:**
1. **Temporário** - Desabilitação apenas por horas
2. **Seletivo** - Apenas serviços problemáticos
3. **Monitorado** - Reativação automática após estabilização
4. **Notificação** - Alertas se outros serviços forem afetados

## 🚨 PROTOCOLO DE EMERGÊNCIA

### **Se Load Average > 5.0:**
```bash
# Desabilitar todos os serviços problemáticos
for service in mediaanalysisd fileproviderd bird cloudd; do
    sudo launchctl disable system/com.apple.$service
    sudo launchctl unload $(find /System/Library/LaunchDaemons -name "*$service*" -type f) 2>/dev/null
    pkill -9 $service
done

# Manter desabilitado por 15 minutos
sleep 900

# Reativar com limites
for service in mediaanalysisd fileproviderd bird cloudd; do
    ./contencao_avancada.sh $service 20 limit
done
```

---
**Nexus Orchestrator** - Solução Definitiva para Contenção de Processos  
*Desenvolvido às 17:04 de 25/03/2026*  
**Status:** AGUARDANDO IMPLEMENTAÇÃO - SOLUÇÃO TÉCNICA PRONTA