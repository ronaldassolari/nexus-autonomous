"""
CFO — Squad 4: Operacoes Financeiras (MODO SUGESTAO)
Gerencia fluxo de caixa, alocacao de orcamento entre squads e
gera relatorios financeiros mensais. Nao executa transacoes reais.
"""

import os
import sys
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, INTELIGENCIA_DIR


class CFO(BaseAgente):
    """Agente CFO — controle financeiro e orcamentario do ecossistema."""

    MODO = "SUGESTAO"

    SQUADS = [
        "Squad 1 — Inteligencia & Validacao",
        "Squad 2 — Fabrica de Software",
        "Squad 3 — Marketing & Vendas",
        "Squad 4 — Operacoes Financeiras",
        "Squad 5 — Automacao & Aprendizado",
    ]

    CATEGORIAS_RECEITA = [
        "vendas_produtos", "assinaturas_saas", "servicos_consultoria",
        "receita_marketplace", "receita_afiliados",
    ]

    CATEGORIAS_DESPESA = [
        "infraestrutura_cloud", "apis_pagas", "marketing_ads",
        "ferramentas_saas", "outros",
    ]

    def __init__(self):
        super().__init__(
            nome="CFO",
            squad="Squad 4 — Operacoes Financeiras",
            papel="Gestao de fluxo de caixa, orcamento e relatorios financeiros",
        )
        self.pasta_financeiro = os.path.join(NEXUS_ROOT, "financeiro")
        os.makedirs(self.pasta_financeiro, exist_ok=True)
        self.fluxo_caixa = {"receitas": [], "despesas": [], "saldo": 0.0}

    def _verificar_modo(self) -> bool:
        """Garante que o agente esta em modo SUGESTAO."""
        if self.MODO != "SUGESTAO":
            self.registrar_log("BLOQUEIO: tentativa de operar fora do modo SUGESTAO", "NEGADO")
            return False
        return True

    def registrar_receita(self, descricao: str, valor: float, categoria: str) -> dict:
        """Registra uma receita no fluxo de caixa."""
        if not self._verificar_modo():
            return {}
        entrada = {
            "tipo": "receita",
            "descricao": descricao,
            "valor": round(valor, 2),
            "categoria": categoria if categoria in self.CATEGORIAS_RECEITA else "outros",
            "data": datetime.now().isoformat(),
        }
        self.fluxo_caixa["receitas"].append(entrada)
        self.fluxo_caixa["saldo"] = round(self.fluxo_caixa["saldo"] + valor, 2)
        self.registrar_log(f"Receita registrada: {descricao}", f"R${valor:.2f}")
        return entrada

    def registrar_despesa(self, descricao: str, valor: float, categoria: str) -> dict:
        """Registra uma despesa no fluxo de caixa."""
        if not self._verificar_modo():
            return {}
        entrada = {
            "tipo": "despesa",
            "descricao": descricao,
            "valor": round(valor, 2),
            "categoria": categoria if categoria in self.CATEGORIAS_DESPESA else "outros",
            "data": datetime.now().isoformat(),
        }
        self.fluxo_caixa["despesas"].append(entrada)
        self.fluxo_caixa["saldo"] = round(self.fluxo_caixa["saldo"] - valor, 2)
        self.registrar_log(f"Despesa registrada: {descricao}", f"R${valor:.2f}")
        return entrada

    def alocar_orcamento(self, total: float, squads: dict[str, float] | None = None) -> dict:
        """
        Aloca orcamento entre squads. Se nao fornecer pesos, usa distribuicao padrao.
        Retorna dict com alocacao por squad.
        """
        if not self._verificar_modo():
            return {}

        pesos_padrao = {
            "Squad 1 — Inteligencia & Validacao": 0.10,
            "Squad 2 — Fabrica de Software": 0.35,
            "Squad 3 — Marketing & Vendas": 0.30,
            "Squad 4 — Operacoes Financeiras": 0.10,
            "Squad 5 — Automacao & Aprendizado": 0.15,
        }

        pesos = squads if squads else pesos_padrao
        soma_pesos = sum(pesos.values())

        alocacao = {}
        for squad, peso in pesos.items():
            percentual = peso / soma_pesos
            valor_alocado = round(total * percentual, 2)
            alocacao[squad] = {
                "valor": valor_alocado,
                "percentual": round(percentual * 100, 1),
            }

        resultado = {
            "total_orcamento": round(total, 2),
            "data_alocacao": datetime.now().isoformat(),
            "alocacoes": alocacao,
            "modo": self.MODO,
        }

        self.registrar_log("Orcamento alocado", f"R${total:.2f} entre {len(alocacao)} squads")
        return resultado

    def gerar_relatorio_financeiro(self, periodo: str = "mensal") -> dict:
        """
        Gera relatorio financeiro consolidado.
        periodo: 'mensal', 'semanal' ou 'diario'.
        """
        if not self._verificar_modo():
            return {}

        agora = datetime.now()
        if periodo == "mensal":
            inicio = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif periodo == "semanal":
            inicio = agora - timedelta(days=agora.weekday())
            inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)

        receitas_periodo = [
            r for r in self.fluxo_caixa["receitas"]
            if datetime.fromisoformat(r["data"]) >= inicio
        ]
        despesas_periodo = [
            d for d in self.fluxo_caixa["despesas"]
            if datetime.fromisoformat(d["data"]) >= inicio
        ]

        total_receitas = sum(r["valor"] for r in receitas_periodo)
        total_despesas = sum(d["valor"] for d in despesas_periodo)

        receitas_por_cat = {}
        for r in receitas_periodo:
            cat = r["categoria"]
            receitas_por_cat[cat] = round(receitas_por_cat.get(cat, 0) + r["valor"], 2)

        despesas_por_cat = {}
        for d in despesas_periodo:
            cat = d["categoria"]
            despesas_por_cat[cat] = round(despesas_por_cat.get(cat, 0) + d["valor"], 2)

        relatorio = {
            "periodo": periodo,
            "data_inicio": inicio.isoformat(),
            "data_fim": agora.isoformat(),
            "resumo": {
                "total_receitas": round(total_receitas, 2),
                "total_despesas": round(total_despesas, 2),
                "resultado_liquido": round(total_receitas - total_despesas, 2),
                "saldo_atual": self.fluxo_caixa["saldo"],
            },
            "receitas_por_categoria": receitas_por_cat,
            "despesas_por_categoria": despesas_por_cat,
            "num_transacoes": len(receitas_periodo) + len(despesas_periodo),
            "modo": self.MODO,
            "aviso": "Relatorio gerado em modo SUGESTAO — dados simulados",
        }

        arquivo = os.path.join(
            self.pasta_financeiro,
            f"relatorio_{periodo}_{agora.strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

        self.registrar_log(f"Relatorio financeiro {periodo} gerado", arquivo)
        return relatorio

    def _gerar_relatorio_md(self, relatorio: dict) -> str:
        """Converte relatorio dict em formato Markdown."""
        resumo = relatorio["resumo"]
        md = (
            f"# Relatorio Financeiro — {relatorio['periodo'].capitalize()}\n"
            f"**Periodo:** {relatorio['data_inicio'][:10]} a {relatorio['data_fim'][:10]}\n"
            f"**Modo:** {self.MODO}\n\n"
            f"## Resumo\n"
            f"| Metrica | Valor |\n|---|---|\n"
            f"| Receitas | R$ {resumo['total_receitas']:.2f} |\n"
            f"| Despesas | R$ {resumo['total_despesas']:.2f} |\n"
            f"| Resultado Liquido | R$ {resumo['resultado_liquido']:.2f} |\n"
            f"| Saldo Atual | R$ {resumo['saldo_atual']:.2f} |\n\n"
        )
        if relatorio["receitas_por_categoria"]:
            md += "## Receitas por Categoria\n"
            for cat, val in relatorio["receitas_por_categoria"].items():
                md += f"- **{cat}:** R$ {val:.2f}\n"
            md += "\n"
        if relatorio["despesas_por_categoria"]:
            md += "## Despesas por Categoria\n"
            for cat, val in relatorio["despesas_por_categoria"].items():
                md += f"- **{cat}:** R$ {val:.2f}\n"
            md += "\n"
        return md

    def executar(self):
        """Loop principal do CFO."""
        self.atualizar_status("em_execucao")
        self.registrar_log("CFO iniciado", "Gerando relatorio financeiro e alocacao de orcamento")

        if not self._verificar_modo():
            self.atualizar_status("bloqueado")
            return

        # Registrar movimentacoes de exemplo para demonstracao
        self.registrar_receita("Assinatura SaaS Piloto", 500.00, "assinaturas_saas")
        self.registrar_despesa("API OpenAI", 120.00, "apis_pagas")
        self.registrar_despesa("Servidor Cloud", 80.00, "infraestrutura_cloud")

        # Gerar relatorio mensal
        relatorio = self.gerar_relatorio_financeiro("mensal")
        relatorio_md = self._gerar_relatorio_md(relatorio)
        self.publicar_resultado("Relatorio Financeiro Mensal", relatorio_md)

        # Alocar orcamento
        alocacao = self.alocar_orcamento(total=5000.00)
        self.publicar_resultado("Alocacao de Orcamento", alocacao)

        # Notificar CEO
        self.enviar_mensagem(
            destinatario="ceo_agente",
            assunto="Relatorio Financeiro Disponivel",
            conteudo=(
                f"CFO completou analise financeira.\n"
                f"**Receitas:** R$ {relatorio['resumo']['total_receitas']:.2f}\n"
                f"**Despesas:** R$ {relatorio['resumo']['total_despesas']:.2f}\n"
                f"**Resultado:** R$ {relatorio['resumo']['resultado_liquido']:.2f}\n\n"
                f"Relatorio completo salvo em: {self.pasta_financeiro}\n"
                f"**Modo:** {self.MODO} — nenhuma transacao real executada."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("CFO finalizado", "Relatorio e orcamento publicados")
        return relatorio


if __name__ == "__main__":
    agente = CFO()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    if resultado:
        print(f"Concluido: saldo R$ {resultado['resumo']['saldo_atual']:.2f}")
    else:
        print("Execucao bloqueada — verificar modo de operacao.")
