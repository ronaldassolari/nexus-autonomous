from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
import os

load_dotenv()

# ── MODELO PADRÃO ─────────────────────────────────────────────────
MODEL = os.getenv("MODEL", "anthropic/claude-sonnet-4-6")

# ── AGENTES ───────────────────────────────────────────────────────

nexus_orchestrator = Agent(
    role="CEO Operacional / Chefe dos Agentes",
    goal="Receber missões, identificar o perfil necessário e delegar para o agente certo",
    backstory="Você é o orquestrador central do ecossistema Nexus. Analisa cada missão, decide qual squad ou agente é o mais adequado e garante que a execução aconteça com qualidade.",
    verbose=True,
    allow_delegation=True,
    model=MODEL,
)

ceo_agente = Agent(
    role="CEO Estratégico",
    goal="Definir escopo, quebrar em subtarefas e acionar os squads corretos",
    backstory="Você define a estratégia e distribui o trabalho entre os times de desenvolvimento, marketing e financeiro.",
    verbose=True,
    allow_delegation=True,
    model=MODEL,
)

dev_rapido = Agent(
    role="Desenvolvedor Rápido (MVP)",
    goal="Entregar MVPs funcionais em 24-48h com código limpo",
    backstory="Especialista em protótipos rápidos. Foca em funcionar primeiro, otimizar depois.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

dev_premium = Agent(
    role="Desenvolvedor Premium",
    goal="Refatorar, otimizar e fazer deploy em produção",
    backstory="Cuida da qualidade final do código, performance e deploy seguro em produção.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

ux_ui_designer = Agent(
    role="UX/UI Designer",
    goal="Criar design systems e interfaces mobile-first de alta conversão",
    backstory="Especialista em interfaces que convertem. Mobile-first, dark mode, componentes reutilizáveis.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

arquiteto_dados = Agent(
    role="Arquiteto de Dados",
    goal="Modelar banco de dados, criar tabelas Supabase e garantir integridade dos dados",
    backstory="Define a estrutura de dados de todos os projetos. Cria schemas SQL, migrations e políticas RLS.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

devops = Agent(
    role="DevOps",
    goal="Gerenciar CI/CD, monitoramento e rollback dos projetos",
    backstory="Responsável por deploy, pipelines, monitoramento de uptime e rollback em caso de falha.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

qa_seguranca = Agent(
    role="QA e Segurança",
    goal="Testar funcionalidades e identificar vulnerabilidades",
    backstory="Garante qualidade e segurança. Faz testes E2E, analisa vulnerabilidades OWASP e valida fluxos.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

copywriter = Agent(
    role="Copywriter",
    goal="Criar copies de alta conversão no estilo direto e persuasivo",
    backstory="Especialista em copy para landing pages, anúncios e emails. Foco em gatilhos mentais e conversão.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

gestor_trafego = Agent(
    role="Gestor de Tráfego",
    goal="Criar e otimizar campanhas no Facebook, Google e TikTok Ads",
    backstory="Especialista em tráfego pago. Cria criativos, segmentações e otimiza ROAS.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

cfo = Agent(
    role="CFO",
    goal="Gerenciar caixa, alocar capital e monitorar saúde financeira",
    backstory="Controla fluxo de caixa, analisa custos e sugere alocação de capital para maximizar ROI.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

esp_cripto = Agent(
    role="Especialista Cripto",
    goal="Analisar mercado cripto, identificar oportunidades e gerenciar posições",
    backstory="Opera exchanges cripto, analisa on-chain data e identifica entradas e saídas.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

esp_daytrade = Agent(
    role="Especialista Day Trade",
    goal="Operar mini-índice, mini-dólar e forex com consistência",
    backstory="Day trader focado em B3. Opera mini-contratos com gestão de risco rigorosa.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

agente_n8n = Agent(
    role="Agente de Automação (n8n)",
    goal="Conectar sistemas via webhooks e criar fluxos de automação",
    backstory="Especialista em n8n e automações. Conecta APIs, cria webhooks e automatiza processos repetitivos.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

radar_china = Agent(
    role="Radar China",
    goal="Identificar hypes e tendências em Douyin, WeChat e Bilibili antes de chegarem ao ocidente",
    backstory="Monitora redes sociais chinesas em busca de produtos e tendências virais para antecipar o mercado.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)

validador_mercado = Agent(
    role="Validador de Mercado",
    goal="Validar demanda de produtos/ideias usando Google Trends e dados de mercado",
    backstory="Antes de qualquer projeto ser executado, valida se há demanda real usando ferramentas de pesquisa.",
    verbose=True,
    allow_delegation=False,
    model=MODEL,
)


# ── FUNÇÃO PRINCIPAL — CRIAR E RODAR UMA MISSÃO ──────────────────

def rodar_missao(missao: str):
    """
    Envia uma missão pro nexus_orchestrator que delega pro agente certo.
    """

    tarefa_orquestrador = Task(
        description=f"""
        Missão recebida: {missao}

        1. Analise a missão e identifique qual(is) agente(s) do squad devem executar
        2. Delegue a tarefa para o(s) agente(s) certos
        3. Consolide os resultados e apresente o relatório final
        """,
        expected_output="Relatório completo com o resultado da missão executada pelo agente delegado.",
        agent=nexus_orchestrator,
    )

    crew = Crew(
        agents=[
            nexus_orchestrator,
            ceo_agente,
            dev_rapido,
            dev_premium,
            ux_ui_designer,
            arquiteto_dados,
            devops,
            qa_seguranca,
            copywriter,
            gestor_trafego,
            cfo,
            esp_cripto,
            esp_daytrade,
            agente_n8n,
            radar_china,
            validador_mercado,
        ],
        tasks=[tarefa_orquestrador],
        process=Process.hierarchical,  # nexus_orchestrator delega automaticamente
        manager_agent=nexus_orchestrator,
        verbose=True,
    )

    resultado = crew.kickoff()
    return resultado


# ── RODAR ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    missao = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Faça um resumo dos projetos ativos no ecossistema Nexus"
    print("\n🚀 Iniciando missão...\n")
    resultado = rodar_missao(missao)
    print("\n✅ Resultado final:\n")
    print(resultado)
