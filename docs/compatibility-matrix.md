# Compatibility Matrix — Nexus Autonomous

ISO 25010:2023 — Compatibility: Co-existence & Interoperability

## Co-existence

| Aspect | Implementation |
|--------|---------------|
| Process | Single Python process per agent, no background daemons |
| Storage | Local filesystem only (comunicacao/, inteligencia/) |
| Ports | Dashboard on configurable port, no other listeners |
| Dependencies | pip packages only, no system-level installs |
| Isolation | Each agent has own comunicacao/ subfolder |

## Interoperability

| System | Protocol | Direction | Status |
|--------|----------|-----------|--------|
| Google Trends | HTTP (pytrends) | Outbound | Active |
| CoinGecko API | HTTP REST | Outbound | Active (free tier) |
| SEMrush API | HTTP REST | Outbound | Configured (needs key) |
| Nexus Command Center | REST + WebSocket | Bidirectional | Active (port 18789) |
| Nexus Finance | File system | Agent → Project | Active |
| File system | .md/.json files | Inter-agent | Core mechanism |

## Data Formats

| Format | Usage |
|--------|-------|
| JSON | Tendências, scores, validações, configs |
| Markdown | Comunicação entre agentes, logs, relatórios |
| Python dict | In-memory data passing |
| SQL (PostgreSQL) | Generated schemas (arquiteto_dados) |

## Agent Communication Protocol

```
Agent A writes: comunicacao/{agent_b}/de_{agent_a}_{timestamp}.md
Agent B reads:  comunicacao/{agent_b}/*.md
Agent B status: comunicacao/{agent_b}/status.md
```
