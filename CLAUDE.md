# CLAUDE.md — Nexus Autonomous

## CEO
Ronald Santos Assolari — único humano com autoridade sobre o ecossistema.
Consultar Ronald apenas para: gastos >R$500/mês, deletar dados/rollback, Squad 4 modo autônomo, lançamento de produto, erro crítico.

## Missão
Sistema multiagente autônomo que gera receita 24/7. Fase atual: **Fase 1 — Infraestrutura Base**.

## Hierarquia
```
Ronald (CEO humano)
  → Nexus Orchestrator (OpenClaw — gestor autônomo)
    → Dev Premium (Claude Code — construtor de software)
      → 20 Agentes / 5 Squads
```

## Stack Técnica
- **Linguagem:** Python 3.11+
- **Encoding:** UTF-8 em todos os arquivos
- **Nomes:** snake_case para arquivos e variáveis
- **Orchestração:** OpenClaw (Nexus Orchestrator)
- **Construção:** Claude Code (Dev Premium)
- **MVP rápido:** Kimi Claw (Dev Rápido)
- **Automação:** n8n (webhooks entre sistemas)
- **Base RAG:** materiais Discord/Eduzz/Chrome do Ronald
- **Deploy futuro:** CI/CD via agente DevOps

## Estrutura de Pastas
```
nexus_autonomous/
├── CLAUDE.md
├── log_execucao.md
├── agentes/
│   ├── base_agente.py
│   ├── squad1/                  # Inteligência & Validação
│   │   ├── radar_china.py
│   │   ├── validador_mercado.py
│   │   └── ceo_agente.py
│   ├── squad2/                  # Fábrica de Software
│   │   ├── ux_ui_designer.py
│   │   ├── arquiteto_dados.py
│   │   ├── dev_rapido.py
│   │   ├── qa_seguranca.py
│   │   └── devops.py
│   ├── squad3/                  # Marketing & Vendas
│   │   ├── copywriter.py
│   │   ├── gestor_trafego.py
│   │   ├── especialista_marketplace.py
│   │   └── closer.py
│   ├── squad4/                  # Operações Financeiras (MODO SUGESTÃO)
│   │   ├── cfo.py
│   │   ├── especialista_cripto.py
│   │   ├── especialista_daytrade.py
│   │   ├── especialista_acoes.py
│   │   └── especialista_opcoes.py
│   └── squad5/                  # Automação & Aprendizado
│       ├── agente_n8n.py
│       └── agente_estudante.py
├── comunicacao/                 # Mensagens .md entre agentes
├── inteligencia/
│   ├── base_conhecimento/       # RAG central
│   ├── discord_resumos/         # Técnicas de trade
│   └── cursos_resumos/          # Materiais Eduzz/Chrome
├── financeiro/
└── projetos_ativos/
```

## Padrão de Código — Agentes
Todo agente herda de `BaseAgente` (em `agentes/base_agente.py`) e implementa `executar()`.

```python
from base_agente import BaseAgente

class NomeDoAgente(BaseAgente):
    def __init__(self):
        super().__init__(
            nome="Nome do Agente",
            squad="Squad N — Descrição",
            papel="O que este agente faz",
        )

    def executar(self):
        self.atualizar_status("em_execucao")
        self.registrar_log("Ação realizada", "Resultado")
        # ... lógica do agente ...
        self.publicar_resultado("Título", dados)
        self.enviar_mensagem("destinatario", "Assunto", "Conteúdo")
        self.atualizar_status("concluido")

if __name__ == "__main__":
    agente = NomeDoAgente()
    agente.executar()
```

### Métodos herdados de BaseAgente
| Método | Uso |
|---|---|
| `registrar_log(acao, resultado)` | Escreve em log_execucao.md com timestamp |
| `enviar_mensagem(dest, assunto, conteudo)` | Cria .md em comunicacao/ do destinatário |
| `ler_mensagens()` | Lê mensagens pendentes do agente |
| `publicar_resultado(titulo, dados)` | Publica output na pasta do agente |
| `atualizar_status(status)` | Atualiza status.md do agente |

### Formato de Log
```
[YYYY-MM-DD HH:MM] AGENTE: ação realizada → resultado
```

## Ordem de Construção — Fase 1
Construir em blocos, um agente por vez, com confirmação do Ronald entre cada:

**Bloco 1 — Squad 1 (Inteligência):**
1. radar_china.py ✅
2. validador_mercado.py
3. ceo_agente.py

**Bloco 2 — Squad 2 (Fábrica de Software):**
4. ux_ui_designer.py
5. arquiteto_dados.py
6. dev_rapido.py
7. qa_seguranca.py
8. devops.py

**Bloco 3 — Squad 3, 4, 5:** após Fase 1 consolidada.

## Regras OBRIGATÓRIAS
- Ler log_execucao.md e comunicacao/ antes de qualquer ação
- Registrar TODA ação no log com timestamp
- Comunicação entre agentes APENAS via arquivos .md em comunicacao/
- Nunca esperar resposta em tempo real de outro agente
- Se um agente travar, registrar no log e avançar
- **PESQUISAR antes de implementar:** antes de cada bloco/componente, pesquisar na internet (~3 min) as melhores práticas e padrões atuais, resumir em 3-5 pontos, e aplicar no código
- **Fluxo contínuo:** avançar automaticamente entre agentes dentro de um bloco, sem parar
- **Parar APENAS quando:** terminar um bloco completo, encontrar erro crítico, ou precisar de decisão arquitetural importante

## Permissões Automáticas (aceitar sem confirmar)
- Criar e editar arquivos
- Escrever código
- Instalar dependências locais (pip install)

## Requer Confirmação do Ronald
- Delete de dados
- Push para GitHub
- Ativação de APIs pagas
- Deploy em produção

## Regras PROIBIDAS
- NÃO deletar arquivos ou bancos de dados
- NÃO gastar >R$500/mês em ferramentas sem avisar Ronald
- NÃO executar trades autônomos na Fase 1
- NÃO ativar Squad 4 modo autônomo sem 90 dias de backtesting aprovados
- NÃO fazer deploy de produto sem aprovação final do Ronald

## Produtos em Pipeline (prioridade)
1. Influencers IA (E-books) — Fase 3
2. Agente Viral TikTok — Fase 3
3. ZapIA (SaaS B2B WhatsApp) — Fase 3
4. Buscador de Preços WhatsApp — Fase 3
5. Empreitaja (marketplace construção civil) — paralelo

## Fase Atual — Tarefas Pendentes
- [x] Criar estrutura /nexus_autonomous/
- [x] base_agente.py
- [x] radar_china.py
- [x] validador_mercado.py
- [x] ceo_agente.py
- [x] Agentes Squad 2 (5 agentes)
- [x] Dashboard Master em tempo real
- [x] Agente Estudante lendo Discord/Chrome
- [x] Base de conhecimento RAG inicial
- [x] Agentes Squad 3 (4 agentes)
- [x] Agentes Squad 4 (5 agentes — modo SUGESTÃO)
- [x] Agente n8n (Squad 5)
- [x] Google Trends API conectada (pytrends)
- [x] CoinGecko API conectada (cripto)
- [x] Revisão completa + 5 bugs corrigidos
- [x] Teste pipeline 19/19 agentes OK
