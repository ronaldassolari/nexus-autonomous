# ⚠️ ALERTA: Carga do Sistema Nexus Excede Limite

**Data/Hora:** 25/03/2026 - 20:02 BRT
**Job Cron:** Monitoramento Carga Nexus - 10min
**ID do Job:** 3a9ca179-e006-47b6-af50-1ca8723b82fb

## 📊 Dados da Carga do Sistema:
- **Carga 1 minuto:** 4.31
- **Carga 5 minutos:** 5.09 ⚠️ **EXCEDE LIMITE DE 5.0**
- **Carga 15 minutos:** 4.97

## 🎯 Limites Configurados:
- **Alerta:** > 5.0
- **Urgente:** > 6.0

## 🔍 Análise:
A carga média de 5 minutos (5.09) ultrapassou o limite de alerta estabelecido (5.0). Embora ainda esteja abaixo do limite crítico de 6.0, o sistema requer atenção.

## 🔥 Principais Processos Consumidores:
1. **openclaw-gateway** - 21.4% CPU
2. **WindowServer** (SkyLight.framework) - 19.6% CPU
3. **Claude.app** (Framework) - 16.9% CPU
4. **cloudd** (CloudKitDaemon) - 16.1% CPU
5. **Claude.app** (Framework) - 15.6% CPU

## 🛠️ Status dos Serviços Nexus:
- ✅ **OpenClaw Gateway:** ONLINE (mas consumindo 21.4% CPU)
- ❌ **WhatsApp Server:** OFFLINE
- ❌ **DimDim Proxy:** OFFLINE

## 📈 Tendência:
- Carga de 5 minutos aumentou de 3.38 (19:44) para 5.09 (20:02)
- Carga de 1 minuto aumentou de 2.11 (19:44) para 4.31 (20:02)
- Tendência: **CRESCENTE**

## 🚨 Ações Recomendadas:
1. **Monitorar próximo ciclo** (próximo check em ~20:12)
2. **Verificar openclaw-gateway** - alto consumo pode indicar atividade intensa
3. **Avaliar Claude.app** - dois processos consumindo ~32.5% CPU combinados
4. **Considerar reiniciar serviços** se carga continuar subindo

## 📝 Observações:
- Sistema ainda está operacional, mas com carga elevada
- Nenhuma notificação urgente necessária (abaixo de 6.0)
- Documentado em: `memory/2026-03-25.md`

---
*Alerta gerado automaticamente pelo sistema de monitoramento Nexus*