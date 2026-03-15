# Incident Response Plan — Nexus Autonomous

**ISO/IEC 27001:2022 — Annex A Controls: A.5.24, A.5.25, A.5.26**
**Owner:** Ronald Santos Assolari (CEO)
**Version:** 1.0 | **Last reviewed:** 2026-03-15

---

## 1. Severity Levels

| Severity | Definition | MTTI | MTTR | Escalation |
|----------|-----------|------|------|-----------|
| P1 | Data breach, RAG corruption, all agents down | < 5 min | < 1h | Immediate to CEO |
| P2 | Single squad failure, API rate limited, stale agents | < 15 min | < 4h | Within 30 min |
| P3 | Config error, single agent failure, log warnings | < 1h | < 24h | Normal queue |

## 2. Detection (A.5.25)

### Automated Monitoring
Run every 5 minutes: `python3 scripts/incident-monitor.py`

| Monitor | Threshold | Severity |
|---------|-----------|----------|
| Agent status stale > 24h | Any agent | P3 |
| Log file > 10MB | Size check | P3 |
| Error mentions > 50 in log | Keyword count | P2 |
| RAG store corrupted | JSON parse failure | P1 |
| Disk usage > 500MB | Total size | P3 |

### Manual Detection
- Weekly review of log_execucao.md
- Dashboard monitoring: `python3 dashboard.py --live`
- CoinGecko API 429 errors (rate limiting)

## 3. Containment (A.5.26)

### P1 — Critical
1. Stop all agents: kill running Python processes
2. Backup current state: `tar -czf emergency-$(date +%s).tar.gz comunicacao/ inteligencia/`
3. Isolate corrupted data (move, don't delete)
4. Notify CEO

### P2 — High
1. Restart failed squad
2. Check API rate limits (Google Trends, CoinGecko)
3. Review last 50 lines of log

### P3 — Medium
1. Log incident in log_execucao.md
2. Fix in next iteration
3. Monitor for recurrence

## 4. Recovery

1. Restore from backup: `tar -xzf emergency-*.tar.gz`
2. Re-run RAG initialization: `python3 rag_engine.py --init`
3. Test pipeline: run all 19 agents
4. Verify dashboard shows all agents as "concluido"
5. Monitor 24h post-recovery

## 5. LGPD Breach Notification (Art. 48)

If personal data compromised (P1):
1. Notify ANPD within reasonable time
2. Notify affected users within 72 hours
3. Document: nature of data, measures taken, recommendations

## 6. Post-Incident Review

Within 48h: timeline, root cause, detection analysis, prevention measures, action items with owners and deadlines.

## 7. Plan Maintenance

| Activity | Frequency |
|----------|-----------|
| Review this plan | Quarterly |
| Test incident response | Semi-annually |
| Dependency audit | Monthly |
| Backup verification | Weekly |
