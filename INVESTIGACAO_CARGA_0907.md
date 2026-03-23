# INVESTIGAÇÃO DE CARGA - Análise de Processos Problemáticos
**Data/Hora:** 2026-03-21 09:07 UTC (06:07 AM BRT)

## 🔍 PROCESSOS CONSUMIDORES DE CPU (TOP 10)

### 1. cloudd (Processo do Sistema)
- **PID:** 32929
- **CPU:** 67.7%
- **Comando:** `/System/Library/PrivateFrameworks/CloudKitDaemon.framework/Support/cloudd`
- **Tempo:** 7:57.68
- **Status:** S (sleeping)
- **Impacto:** Processo do sistema iCloud, possível sincronização em andamento

### 2. Spotify Helper (Renderer)
- **PID:** 744
- **CPU:** 43.1%
- **Memória:** 4.1% (693MB)
- **Tempo:** 3602:00.54 (60+ horas)
- **Status:** R (running)
- **Impacto:** Processo do Spotify consumindo recursos significativos

### 3. bird (Processo do Sistema)
- **PID:** 29975
- **CPU:** 29.9%
- **Comando:** `/System/Library/PrivateFrameworks/CloudDocsDaemon.framework/Versions/A/Support/bird`
- **Tempo:** 12:51.79
- **Status:** R (running)
- **Impacto:** Processo do iCloud Drive (CloudDocs)

### 4. fileproviderd (Processo do Sistema)
- **PID:** 497
- **CPU:** 26.1%
- **Tempo:** 1016:30.68 (42+ dias)
- **Status:** R (running)
- **Impacto:** Processo do File Provider framework

### 5. Google Chrome Helper (Renderer)
- **PID:** 15632
- **CPU:** 21.5%
- **Memória:** 6.7% (1.1GB)
- **Tempo:** 241:43.04
- **Status:** R (running)
- **Impacto:** Processo do Chrome com alto consumo

## 📊 ANÁLISE DOS PROCESSOS DO SISTEMA NEXUS

### Processos Node.js/Python Identificados (12 processos)

#### Serviços Ativos:
1. **ObraSync Backend (port 3100)**
   - PID 49816: `node --require ... src/server.ts`
   - PID 49815: `node .../.bin/tsx src/server.ts`
   - PID 49792: `npm exec tsx src/server.ts`
   - Status: ✅ Ativo e respondendo

2. **ObraSync Watch Mode**
   - PID 47576: `node .../.bin/tsx watch src/server.ts`
   - PID 47556: `npm exec tsx watch src/server.ts`
   - Status: ✅ Ativo (modo desenvolvimento)

3. **Dashboard Master (port 3000)**
   - PID 87327: `sh -c pnpm run verify:node && next start ...`
   - PID 87313: `npm start`
   - Status: ✅ Ativo e respondendo

4. **DimDim Proxy**
   - PID 15072: `node dimdim-proxy.js`
   - Status: ⚠️ Ativo mas serviço não responde (port 3500)

5. **Serviço porta 3600**
   - PID 17691: `npm exec next start -p 3600`
   - Status: ⚠️ Ativo mas retorna erro 500

6. **Cripto Trader (port 3300)**
   - PID 36489: `node .../.bin/next dev -p 3300`
   - PID 36475: `npm run dev`
   - Status: ✅ Ativo e respondendo (404 é resposta válida)

7. **WhatsApp Server**
   - PID 71532: `node server/whatsappServer.js`
   - PID 71519: `npm run whatsapp:dev`
   - Status: ✅ Ativo

#### Serviços Inativos/Problemas:
1. **Clipagem Dashboard (port 3200)**
   - ❌ Nenhum processo identificado na porta 3200
   - Status: Serviço não está em execução

2. **Cripto Trader (port 3400)**
   - ❌ Nenhum processo identificado na porta 3400
   - Status: Serviço não está em execução

## 🎯 DIAGNÓSTICO DA CARGA EXCESSIVA

### Causas Identificadas:

#### 1. Processos do Sistema macOS (PRINCIPAL CAUSA)
- **cloudd (67.7% CPU):** Sincronização iCloud ativa
- **bird (29.9% CPU):** iCloud Drive em operação
- **fileproviderd (26.1% CPU):** File Provider framework
- **Total impacto:** ~123.7% de CPU combinada

#### 2. Aplicações de Usuário
- **Spotify Helper (43.1% CPU):** Consumo excessivo prolongado
- **Google Chrome (21.5% CPU):** Múltiplos processos renderer

#### 3. Serviços Nexus
- **Consumo baixo:** Processos Node.js consomem < 0.1% CPU cada
- **Impacto mínimo:** Não são a causa da carga excessiva

### Conclusão da Investigação:
**A carga excessiva NÃO é causada pelos serviços Nexus**, mas sim por:
1. Processos do sistema macOS (iCloud sync)
2. Aplicações de usuário (Spotify, Chrome)
3. Possível atividade de sincronização em background

## 🛠️ RECOMENDAÇÕES DE AÇÃO

### Ação Imediata (Redução de Carga):
1. **Pausar sincronização iCloud temporariamente:**
   ```bash
   # Verificar status do cloudd
   sudo kill -STOP 32929  # Pausar processo cloudd
   sudo kill -STOP 29975  # Pausar processo bird
   
   # Monitorar impacto na carga
   uptime
   ```

2. **Reduzir consumo do Spotify:**
   - Fechar aplicativo Spotify
   - Ou matar processo problemático:
   ```bash
   kill 744  # Spotify Helper (Renderer)
   ```

3. **Otimizar Chrome:**
   - Fechar abas não utilizadas
   - Desativar extensões pesadas

### Recuperação de Serviços Nexus:

#### 1. Clipagem Dashboard (port 3200)
```bash
# Verificar se há processo na porta
lsof -i :3200

# Iniciar serviço (se existir script)
cd /caminho/para/clipagem-dashboard
npm start  # ou comando apropriado
```

#### 2. Cripto Trader (port 3400)
```bash
# Verificar configuração do serviço
find . -name "*cripto*" -type d

# Iniciar serviço
cd /caminho/para/cripto-trader
npm run dev  # ou comando apropriado
```

#### 3. DimDim (port 3500) e Serviço 3600
```bash
# Verificar logs dos serviços
tail -f /caminho/para/dimdim/logs/*.log
tail -f /caminho/para/servico-3600/logs/*.log

# Reiniciar serviços
cd /caminho/para/dimdim && npm restart
cd /caminho/para/servico-3600 && npm restart
```

## 📈 PLANO DE RECUPERAÇÃO

### Fase 1: Redução de Carga (0-15 minutos)
1. [ ] Pausar processos do sistema problemáticos
2. [ ] Reduzir consumo de aplicações de usuário
3. [ ] Monitorar impacto no load average

### Fase 2: Recuperação de Serviços (15-60 minutos)
1. [ ] Iniciar Clipagem Dashboard (3200)
2. [ ] Iniciar Cripto Trader (3400)
3. [ ] Reiniciar DimDim (3500) e serviço 3600
4. [ ] Validar conectividade

### Fase 3: Estabilização (60-120 minutos)
1. [ ] Monitorar carga por 30 minutos
2. [ ] Validar disponibilidade de serviços
3. [ ] Documentar ações tomadas
4. [ ] Estabelecer monitoramento proativo

## ⚠️ CONSIDERAÇÕES DE SEGURANÇA

### Ao pausar processos do sistema:
1. **cloudd/bird:** Pode interromper sincronização iCloud temporariamente
2. **Impacto:** Arquivos não sincronizados até processo retomado
3. **Recomendação:** Retomar processos após estabilização do sistema

### Ao matar processos de aplicação:
1. **Spotify/Chrome:** Pode causar perda de dados não salvos
2. **Impacto:** Aplicações fechadas abruptamente
3. **Recomendação:** Fechar normalmente quando possível

## 📋 CHECKLIST DE VALIDAÇÃO

### Após Ações de Recuperação:
- [ ] Load average < 4.0
- [ ] Todos serviços Nexus respondendo
- [ ] Processos do sistema consumindo < 20% CPU combinada
- [ ] Memória livre > 2GB
- [ ] Uptime estável

### Monitoramento Contínuo:
- [ ] Configurar alerta para load average > 5.0
- [ ] Monitorar consumo de processos do sistema
- [ ] Implementar health checks automáticos
- [ ] Documentar procedimentos para incidentes futuros

---
*Análise de processos e plano de recuperação - 09:07 UTC*
*Relacionado: STATUS_NEXUS_0907.md, MONITORAMENTO_NEXUS_RESUMO_0907.md*