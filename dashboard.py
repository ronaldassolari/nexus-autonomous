"""
DASHBOARD MASTER — Nexus Autonomous
Painel em tempo real que mostra status de todos os agentes, projetos e métricas.
Modo terminal (Rich) + exportação JSON/HTML para integração futura.
"""

import os
import json
import time
from datetime import datetime

NEXUS_ROOT = os.path.dirname(os.path.abspath(__file__))
COMUNICACAO_DIR = os.path.join(NEXUS_ROOT, "comunicacao")
PROJETOS_DIR = os.path.join(NEXUS_ROOT, "projetos_ativos")
LOG_FILE = os.path.join(NEXUS_ROOT, "log_execucao.md")


# ---------------------------------------------------------------------------
# Mapeamento de agentes
# ---------------------------------------------------------------------------

AGENTES = {
    "squad1": {
        "nome": "Inteligência & Validação",
        "agentes": [
            {"id": "radar_china", "nome": "Radar China", "papel": "Busca hypes plataformas CN"},
            {"id": "validador_mercado", "nome": "Validador Mercado", "papel": "Valida demanda Google Trends/SEMrush"},
            {"id": "ceo_agente", "nome": "CEO Agente", "papel": "Decisor central, prioriza e aciona squads"},
        ],
    },
    "squad2": {
        "nome": "Fábrica de Software",
        "agentes": [
            {"id": "ux_ui_designer", "nome": "UX/UI Designer", "papel": "Wireframes e design system"},
            {"id": "arquiteto_dados", "nome": "Arquiteto Dados", "papel": "Schemas e migrations"},
            {"id": "dev_rapido", "nome": "Dev Rápido", "papel": "MVP scaffolding 24-48h"},
            {"id": "qa_seguranca", "nome": "QA Segurança", "papel": "Testes e scan OWASP"},
            {"id": "devops", "nome": "DevOps", "papel": "CI/CD e monitoramento"},
        ],
    },
    "squad3": {
        "nome": "Marketing & Vendas",
        "agentes": [
            {"id": "copywriter", "nome": "Copywriter", "papel": "Textos e landing pages"},
            {"id": "gestor_trafego", "nome": "Gestor Tráfego", "papel": "Facebook/Google/TikTok Ads"},
            {"id": "especialista_marketplace", "nome": "Esp. Marketplace", "papel": "Hotmart/Kiwify/App Store"},
            {"id": "closer", "nome": "Closer", "papel": "Fecha deals WhatsApp"},
        ],
    },
    "squad4": {
        "nome": "Operações Financeiras [SUGESTÃO]",
        "agentes": [
            {"id": "cfo", "nome": "CFO", "papel": "Gerencia caixa e capital"},
            {"id": "especialista_cripto", "nome": "Esp. Cripto", "papel": "Exchanges e Discord"},
            {"id": "especialista_daytrade", "nome": "Esp. Day Trade", "papel": "Mini-índice/dólar/forex"},
            {"id": "especialista_acoes", "nome": "Esp. Ações", "papel": "B3/NYSE, dividendos"},
            {"id": "especialista_opcoes", "nome": "Esp. Opções", "papel": "Travas, venda coberta"},
        ],
    },
    "squad5": {
        "nome": "Automação & Aprendizado",
        "agentes": [
            {"id": "agente_n8n", "nome": "Agente n8n", "papel": "Webhooks entre sistemas"},
            {"id": "agente_estudante", "nome": "Agente Estudante", "papel": "Alimenta base RAG"},
        ],
    },
}


# ---------------------------------------------------------------------------
# Coleta de Status
# ---------------------------------------------------------------------------

def ler_status_agente(agente_id: str) -> dict:
    """Lê status.md de um agente da pasta de comunicação."""
    status_file = os.path.join(COMUNICACAO_DIR, agente_id, "status.md")
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            conteudo = f.read()
        for linha in conteudo.split("\n"):
            if "**Status:**" in linha:
                return {
                    "status": linha.split("**Status:**")[1].strip(),
                    "arquivo": status_file,
                    "existe": True,
                }
    return {"status": "não inicializado", "arquivo": "", "existe": False}


def contar_mensagens_agente(agente_id: str) -> int:
    """Conta mensagens pendentes de um agente."""
    pasta = os.path.join(COMUNICACAO_DIR, agente_id)
    if not os.path.exists(pasta):
        return 0
    return len([f for f in os.listdir(pasta) if f.endswith(".md") and f != "status.md"])


def ler_ultimas_linhas_log(n: int = 15) -> list[str]:
    """Lê as últimas N linhas do log de execução."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        linhas = f.readlines()
    return [l.strip() for l in linhas[-n:] if l.strip()]


def contar_projetos() -> dict:
    """Conta projetos ativos e seus status."""
    contagem = {"total": 0, "designs": 0, "schemas": 0, "mvps": 0, "qa_reports": 0, "infra": 0}
    for subdir, key in [("designs", "designs"), ("schemas", "schemas"), ("mvps", "mvps"),
                         ("qa_reports", "qa_reports"), ("infra", "infra")]:
        pasta = os.path.join(PROJETOS_DIR, subdir)
        if os.path.exists(pasta):
            contagem[key] = len([d for d in os.listdir(pasta) if os.path.isdir(os.path.join(pasta, d))])

    # Contar JSONs de projeto no root
    if os.path.exists(PROJETOS_DIR):
        contagem["total"] = len([f for f in os.listdir(PROJETOS_DIR) if f.endswith(".json")])
    return contagem


def coletar_dados_dashboard() -> dict:
    """Coleta todos os dados para o dashboard."""
    dados = {
        "timestamp": datetime.now().isoformat(),
        "fase": "Fase 1 — Infraestrutura Base",
        "squads": {},
        "projetos": contar_projetos(),
        "log_recente": ler_ultimas_linhas_log(15),
    }

    total_agentes = 0
    ativos = 0
    for squad_id, squad_info in AGENTES.items():
        squad_data = {
            "nome": squad_info["nome"],
            "agentes": [],
        }
        for agente in squad_info["agentes"]:
            status = ler_status_agente(agente["id"])
            msgs = contar_mensagens_agente(agente["id"])
            squad_data["agentes"].append({
                "id": agente["id"],
                "nome": agente["nome"],
                "papel": agente["papel"],
                "status": status["status"],
                "mensagens_pendentes": msgs,
                "inicializado": status["existe"],
            })
            total_agentes += 1
            if status["existe"]:
                ativos += 1

        dados["squads"][squad_id] = squad_data

    dados["resumo"] = {
        "total_agentes": total_agentes,
        "agentes_ativos": ativos,
        "agentes_pendentes": total_agentes - ativos,
    }
    return dados


# ---------------------------------------------------------------------------
# Renderização Terminal (Rich)
# ---------------------------------------------------------------------------

def render_terminal(dados: dict):
    """Renderiza dashboard no terminal usando Rich."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.layout import Layout
        from rich.text import Text
        from rich import box

        console = Console()
        console.clear()

        # Header
        header = Text("NEXUS AUTONOMOUS — DASHBOARD MASTER", style="bold white on blue", justify="center")
        console.print(Panel(header, box=box.DOUBLE))

        # Resumo
        r = dados["resumo"]
        p = dados["projetos"]
        resumo = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        resumo.add_column("Métrica", style="bold")
        resumo.add_column("Valor", style="cyan")
        resumo.add_row("Fase", dados["fase"])
        resumo.add_row("Agentes Ativos", f"{r['agentes_ativos']}/{r['total_agentes']}")
        resumo.add_row("Projetos", str(p["total"]))
        resumo.add_row("MVPs", str(p["mvps"]))
        resumo.add_row("QA Reports", str(p["qa_reports"]))
        resumo.add_row("Timestamp", dados["timestamp"][:19])
        console.print(Panel(resumo, title="Resumo", box=box.ROUNDED))

        # Squads
        for squad_id, squad_data in dados["squads"].items():
            table = Table(
                title=f"{squad_id.upper()} — {squad_data['nome']}",
                box=box.ROUNDED,
                show_lines=True,
            )
            table.add_column("Agente", style="bold", min_width=20)
            table.add_column("Status", min_width=15)
            table.add_column("Msgs", justify="center", min_width=5)
            table.add_column("Papel", style="dim")

            for ag in squad_data["agentes"]:
                status = ag["status"]
                if "concluido" in status:
                    style = "green"
                elif "execucao" in status:
                    style = "yellow"
                elif "aguardando" in status:
                    style = "blue"
                elif "não inicializado" in status:
                    style = "dim"
                else:
                    style = "white"

                table.add_row(
                    ag["nome"],
                    Text(status, style=style),
                    str(ag["mensagens_pendentes"]),
                    ag["papel"],
                )
            console.print(table)

        # Log recente
        if dados["log_recente"]:
            log_text = "\n".join(dados["log_recente"][-10:])
            console.print(Panel(log_text, title="Log Recente", box=box.ROUNDED, style="dim"))

    except ImportError:
        # Fallback sem Rich
        render_texto_simples(dados)


def render_texto_simples(dados: dict):
    """Fallback: renderiza dashboard em texto puro."""
    r = dados["resumo"]
    print("=" * 60)
    print("  NEXUS AUTONOMOUS — DASHBOARD MASTER")
    print("=" * 60)
    print(f"  Fase: {dados['fase']}")
    print(f"  Agentes: {r['agentes_ativos']}/{r['total_agentes']} ativos")
    print(f"  Projetos: {dados['projetos']['total']}")
    print(f"  Timestamp: {dados['timestamp'][:19]}")
    print("-" * 60)

    for squad_id, squad_data in dados["squads"].items():
        print(f"\n  {squad_id.upper()} — {squad_data['nome']}")
        print(f"  {'Agente':<22} {'Status':<18} {'Msgs':<6}")
        print(f"  {'-'*22} {'-'*18} {'-'*6}")
        for ag in squad_data["agentes"]:
            print(f"  {ag['nome']:<22} {ag['status']:<18} {ag['mensagens_pendentes']:<6}")

    print("\n" + "-" * 60)
    print("  LOG RECENTE:")
    for line in dados["log_recente"][-10:]:
        print(f"  {line}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Exportação
# ---------------------------------------------------------------------------

def exportar_json(dados: dict):
    """Exporta dashboard como JSON."""
    pasta = os.path.join(NEXUS_ROOT, "comunicacao", "dashboard")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "dashboard_latest.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def exportar_markdown(dados: dict):
    """Exporta dashboard como Markdown."""
    r = dados["resumo"]
    p = dados["projetos"]
    md = (
        f"# Dashboard Nexus Autonomous\n"
        f"**Atualizado:** {dados['timestamp'][:19]}\n"
        f"**Fase:** {dados['fase']}\n\n"
        f"## Resumo\n"
        f"- Agentes ativos: {r['agentes_ativos']}/{r['total_agentes']}\n"
        f"- Projetos: {p['total']} | MVPs: {p['mvps']} | QA: {p['qa_reports']}\n\n"
    )
    for squad_id, squad_data in dados["squads"].items():
        md += f"## {squad_id.upper()} — {squad_data['nome']}\n"
        md += f"| Agente | Status | Msgs |\n|---|---|---|\n"
        for ag in squad_data["agentes"]:
            md += f"| {ag['nome']} | {ag['status']} | {ag['mensagens_pendentes']} |\n"
        md += "\n"

    md += "## Log Recente\n```\n"
    for line in dados["log_recente"][-10:]:
        md += f"{line}\n"
    md += "```\n"

    pasta = os.path.join(NEXUS_ROOT, "comunicacao", "dashboard")
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "dashboard.md"), "w", encoding="utf-8") as f:
        f.write(md)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def atualizar_dashboard(modo: str = "terminal"):
    """Atualiza o dashboard uma vez."""
    dados = coletar_dados_dashboard()
    exportar_json(dados)
    exportar_markdown(dados)

    if modo == "terminal":
        render_terminal(dados)
    elif modo == "texto":
        render_texto_simples(dados)

    return dados


def dashboard_live(intervalo: int = 5):
    """Dashboard com atualização contínua (Ctrl+C para sair)."""
    print(f"Dashboard live iniciado (refresh: {intervalo}s) — Ctrl+C para sair")
    try:
        while True:
            atualizar_dashboard("terminal")
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\nDashboard encerrado.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nexus Autonomous Dashboard")
    parser.add_argument("--live", action="store_true", help="Modo live com refresh automático")
    parser.add_argument("--intervalo", type=int, default=5, help="Intervalo de refresh em segundos")
    parser.add_argument("--modo", choices=["terminal", "texto", "json"], default="terminal")
    args = parser.parse_args()

    if args.live:
        dashboard_live(args.intervalo)
    elif args.modo == "json":
        dados = coletar_dados_dashboard()
        exportar_json(dados)
        print(json.dumps(dados, ensure_ascii=False, indent=2))
    else:
        atualizar_dashboard(args.modo)
