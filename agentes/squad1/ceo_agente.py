"""
CEO AGENTE — Squad 1: Inteligência & Validação
Decisor central: recebe tendências validadas, prioriza projetos,
define escopo e aciona os squads corretos.
Padrão: task-driven loop com scoring rule-based e roteamento inteligente.
"""

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, INTELIGENCIA_DIR, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Enums e Tipos
# ---------------------------------------------------------------------------

class Prioridade(str, Enum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class StatusProjeto(str, Enum):
    IDEIA = "ideia"
    VALIDADO = "validado"
    ESCOPO_DEFINIDO = "escopo_definido"
    EM_DESENVOLVIMENTO = "em_desenvolvimento"
    MVP_PRONTO = "mvp_pronto"
    EM_LANCAMENTO = "em_lancamento"
    ATIVO = "ativo"
    PAUSADO = "pausado"


# ---------------------------------------------------------------------------
# Estruturas de Dados
# ---------------------------------------------------------------------------

@dataclass
class Projeto:
    """Representa um projeto no pipeline do Nexus."""
    nome: str
    descricao: str
    keyword_origem: str = ""
    score_validacao: float = 0.0
    prioridade: str = Prioridade.MEDIA
    status: str = StatusProjeto.IDEIA
    squad_responsavel: str = ""
    tarefas: list = field(default_factory=list)
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    data_atualizacao: str = ""
    decisoes: list = field(default_factory=list)
    requer_aprovacao_ronald: bool = False
    motivo_aprovacao: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Tarefa:
    """Tarefa atribuída a um agente específico."""
    titulo: str
    descricao: str
    agente_destino: str
    squad: str
    prioridade: str = Prioridade.MEDIA
    status: str = "pendente"
    projeto: str = ""
    prazo: str = ""
    dependencias: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Roteamento de Squads
# ---------------------------------------------------------------------------

MAPA_SQUADS = {
    "squad1": {
        "nome": "Inteligência & Validação",
        "agentes": ["radar_china", "validador_mercado", "ceo_agente"],
        "capacidades": ["pesquisa", "validacao", "decisao"],
    },
    "squad2": {
        "nome": "Fábrica de Software",
        "agentes": [
            "ux_ui_designer", "arquiteto_dados", "dev_rapido",
            "qa_seguranca", "devops",
        ],
        "capacidades": ["design", "arquitetura", "desenvolvimento", "testes", "deploy"],
    },
    "squad3": {
        "nome": "Marketing & Vendas",
        "agentes": ["copywriter", "gestor_trafego", "especialista_marketplace", "closer"],
        "capacidades": ["copy", "trafego", "marketplace", "vendas"],
    },
    "squad4": {
        "nome": "Operações Financeiras",
        "agentes": [
            "cfo", "especialista_cripto", "especialista_daytrade",
            "especialista_acoes", "especialista_opcoes",
        ],
        "capacidades": ["financeiro", "cripto", "trade", "investimentos"],
        "modo": "SUGESTAO",  # até Ronald autorizar AUTONOMO
    },
    "squad5": {
        "nome": "Automação & Aprendizado",
        "agentes": ["agente_n8n", "agente_estudante"],
        "capacidades": ["automacao", "webhooks", "aprendizado", "rag"],
    },
}


# ---------------------------------------------------------------------------
# Motor de Decisão
# ---------------------------------------------------------------------------

class MotorDecisao:
    """Engine rule-based para priorização e roteamento — sem LLM, determinístico."""

    # Thresholds de score para decisão automática
    THRESHOLD_APROVACAO_AUTO = 7.0   # Score >= 7: aprovado automaticamente
    THRESHOLD_MONITORAR = 4.0        # Score 4-7: monitorar
    THRESHOLD_DESCARTAR = 4.0        # Score < 4: descartar

    # Guardrails: quando escalar para Ronald
    GUARDRAILS = {
        "gasto_maximo_mensal": 500,       # R$
        "deletar_dados": True,            # Sempre escalar
        "squad4_autonomo": True,          # Sempre escalar
        "lancamento_produto": True,       # Sempre escalar
    }

    @staticmethod
    def decidir_sobre_tendencia(keyword: str, score: float) -> dict:
        """Decide o que fazer com uma tendência validada."""
        if score >= MotorDecisao.THRESHOLD_APROVACAO_AUTO:
            return {
                "decisao": "APROVAR",
                "acao": "criar_projeto",
                "motivo": f"Score {score} >= threshold {MotorDecisao.THRESHOLD_APROVACAO_AUTO}",
                "requer_ronald": False,
            }
        elif score >= MotorDecisao.THRESHOLD_MONITORAR:
            return {
                "decisao": "MONITORAR",
                "acao": "adicionar_watchlist",
                "motivo": f"Score {score} entre {MotorDecisao.THRESHOLD_MONITORAR}-{MotorDecisao.THRESHOLD_APROVACAO_AUTO}",
                "requer_ronald": False,
            }
        else:
            return {
                "decisao": "DESCARTAR",
                "acao": "arquivar",
                "motivo": f"Score {score} < threshold {MotorDecisao.THRESHOLD_DESCARTAR}",
                "requer_ronald": False,
            }

    @staticmethod
    def rotear_para_squad(tipo_tarefa: str) -> str:
        """Roteia tarefa para o squad correto baseado no tipo."""
        mapa_tipo = {
            "pesquisa": "squad1",
            "validacao": "squad1",
            "design": "squad2",
            "desenvolvimento": "squad2",
            "mvp": "squad2",
            "testes": "squad2",
            "deploy": "squad2",
            "marketing": "squad3",
            "vendas": "squad3",
            "financeiro": "squad4",
            "automacao": "squad5",
        }
        return mapa_tipo.get(tipo_tarefa, "squad2")

    @staticmethod
    def rotear_para_agente(tipo_tarefa: str) -> str:
        """Roteia tarefa para o agente específico."""
        mapa_agente = {
            "pesquisa_china": "radar_china",
            "validacao": "validador_mercado",
            "design_ui": "ux_ui_designer",
            "arquitetura_db": "arquiteto_dados",
            "mvp_rapido": "dev_rapido",
            "refatoracao": "dev_premium",
            "testes": "qa_seguranca",
            "deploy": "devops",
            "copy": "copywriter",
            "trafego": "gestor_trafego",
            "marketplace": "especialista_marketplace",
            "vendas": "closer",
            "webhooks": "agente_n8n",
            "aprendizado": "agente_estudante",
        }
        return mapa_agente.get(tipo_tarefa, "dev_rapido")

    @staticmethod
    def verificar_guardrail(acao: str, valor: float = 0) -> dict:
        """Verifica se ação requer aprovação do Ronald."""
        if acao == "gasto" and valor > MotorDecisao.GUARDRAILS["gasto_maximo_mensal"]:
            return {"bloqueado": True, "motivo": f"Gasto R${valor} > limite R$500/mês"}
        if acao in ("deletar_dados", "squad4_autonomo", "lancamento_produto"):
            return {"bloqueado": True, "motivo": f"Ação '{acao}' requer aprovação do Ronald"}
        return {"bloqueado": False}


# ---------------------------------------------------------------------------
# Agente CEO
# ---------------------------------------------------------------------------

class CEOAgente(BaseAgente):
    """CEO Agente — decisor central do ecossistema Nexus Autonomous."""

    def __init__(self):
        super().__init__(
            nome="CEO Agente",
            squad="Squad 1 — Inteligência & Validação",
            papel="Define escopo, prioriza projetos e aciona squads",
        )
        self.motor = MotorDecisao()
        self.pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        self.pasta_decisoes = os.path.join(self.pasta_comunicacao, "decisoes")
        os.makedirs(self.pasta_projetos, exist_ok=True)
        os.makedirs(self.pasta_decisoes, exist_ok=True)
        self.projetos: list[Projeto] = []
        self.watchlist: list[dict] = []

    def ler_validacoes(self) -> list[dict]:
        """Lê os scores de validação mais recentes."""
        pasta_val = os.path.join(INTELIGENCIA_DIR, "validacoes")
        if not os.path.exists(pasta_val):
            return []
        arquivos = sorted(
            [f for f in os.listdir(pasta_val) if f.endswith(".json")],
            reverse=True,
        )
        if not arquivos:
            return []
        with open(os.path.join(pasta_val, arquivos[0]), "r", encoding="utf-8") as f:
            return json.load(f)

    def processar_validacoes(self, scores: list[dict]) -> dict:
        """Processa scores e toma decisões sobre cada tendência."""
        resultados = {"aprovados": [], "monitorar": [], "descartados": []}

        for s in scores:
            keyword = s.get("keyword", "")
            score_total = s.get("score_total", 0)
            decisao = self.motor.decidir_sobre_tendencia(keyword, score_total)

            self.registrar_log(
                f"Decisão sobre '{keyword}'",
                f"{decisao['decisao']} (score {score_total})",
            )

            if decisao["decisao"] == "APROVAR":
                projeto = self._criar_projeto(keyword, s)
                resultados["aprovados"].append(projeto.to_dict())
            elif decisao["decisao"] == "MONITORAR":
                self.watchlist.append({"keyword": keyword, "score": score_total})
                resultados["monitorar"].append(keyword)
            else:
                resultados["descartados"].append(keyword)

        return resultados

    def _criar_projeto(self, keyword: str, score_data: dict) -> Projeto:
        """Cria um projeto a partir de uma tendência aprovada."""
        projeto = Projeto(
            nome=f"Projeto {keyword}",
            descricao=f"Projeto baseado na tendência '{keyword}' detectada pelo Radar China",
            keyword_origem=keyword,
            score_validacao=score_data.get("score_total", 0),
            prioridade=Prioridade.ALTA,
            status=StatusProjeto.VALIDADO,
            squad_responsavel="squad2",
        )

        # Definir tarefas iniciais do pipeline
        projeto.tarefas = [
            Tarefa(
                titulo=f"Design UI/UX para {keyword}",
                descricao=f"Criar wireframes e design system para projeto {keyword}",
                agente_destino="ux_ui_designer",
                squad="squad2",
                prioridade=Prioridade.ALTA,
                projeto=projeto.nome,
            ).to_dict(),
            Tarefa(
                titulo=f"Arquitetura de dados para {keyword}",
                descricao=f"Definir schema e infraestrutura para projeto {keyword}",
                agente_destino="arquiteto_dados",
                squad="squad2",
                prioridade=Prioridade.ALTA,
                projeto=projeto.nome,
            ).to_dict(),
            Tarefa(
                titulo=f"MVP rápido de {keyword}",
                descricao=f"Construir MVP funcional em 24-48h para projeto {keyword}",
                agente_destino="dev_rapido",
                squad="squad2",
                prioridade=Prioridade.ALTA,
                projeto=projeto.nome,
                dependencias=["Design UI/UX", "Arquitetura de dados"],
            ).to_dict(),
        ]

        self.projetos.append(projeto)
        self._salvar_projeto(projeto)
        return projeto

    def _salvar_projeto(self, projeto: Projeto):
        """Salva projeto em arquivo JSON."""
        nome_arquivo = projeto.nome.lower().replace(" ", "_") + ".json"
        caminho = os.path.join(self.pasta_projetos, nome_arquivo)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(projeto.to_dict(), f, ensure_ascii=False, indent=2)

    def acionar_squad(self, squad_id: str, tarefas: list[dict]):
        """Envia tarefas para os agentes do squad correto."""
        if squad_id not in MAPA_SQUADS:
            self.registrar_log(f"Squad desconhecido: {squad_id}", "ERRO")
            return

        squad = MAPA_SQUADS[squad_id]

        # Verificar guardrail do Squad 4
        if squad_id == "squad4":
            check = self.motor.verificar_guardrail("squad4_autonomo")
            if check["bloqueado"]:
                self.registrar_log("Squad 4 bloqueado", check["motivo"])
                self.enviar_mensagem(
                    "ceo_agente", "ESCALAR PARA RONALD",
                    f"Squad 4 requer aprovação: {check['motivo']}",
                )
                return

        for tarefa in tarefas:
            agente_destino = tarefa.get("agente_destino", "")
            if agente_destino:
                self.enviar_mensagem(
                    destinatario=agente_destino,
                    assunto=f"TAREFA: {tarefa['titulo']}",
                    conteudo=(
                        f"**Projeto:** {tarefa.get('projeto', 'N/A')}\n"
                        f"**Prioridade:** {tarefa.get('prioridade', 'media')}\n"
                        f"**Descrição:** {tarefa['descricao']}\n"
                        f"**Dependências:** {tarefa.get('dependencias', 'Nenhuma')}\n"
                    ),
                )
        self.registrar_log(
            f"Squad {squad_id} acionado",
            f"{len(tarefas)} tarefas enviadas para {squad['nome']}",
        )

    def gerar_relatorio_decisoes(self, resultados: dict) -> str:
        """Gera relatório de decisões tomadas."""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        relatorio = (
            f"# Relatório de Decisões — CEO Agente\n"
            f"**Data:** {agora}\n\n"
        )

        relatorio += f"## Projetos Aprovados ({len(resultados['aprovados'])})\n"
        for p in resultados["aprovados"]:
            relatorio += (
                f"- **{p['nome']}** (score {p['score_validacao']}) "
                f"→ {len(p.get('tarefas', []))} tarefas criadas\n"
            )

        relatorio += f"\n## Monitorando ({len(resultados['monitorar'])})\n"
        for kw in resultados["monitorar"]:
            relatorio += f"- {kw}\n"

        relatorio += f"\n## Descartados ({len(resultados['descartados'])})\n"
        for kw in resultados["descartados"]:
            relatorio += f"- {kw}\n"

        relatorio += (
            f"\n## Próximos Passos\n"
            f"1. Squad 2 executar tarefas dos projetos aprovados\n"
            f"2. Reavaliar watchlist na próxima varredura\n"
            f"3. Aguardar MVPs para decisão de lançamento\n"
        )
        return relatorio

    def executar(self):
        """Loop principal: lê validações, decide, cria projetos, aciona squads."""
        self.atualizar_status("em_execucao")
        self.registrar_log("CEO Agente iniciado", "Processando decisões pendentes")

        # 1. Ler mensagens pendentes
        mensagens = self.ler_mensagens()
        if mensagens:
            self.registrar_log(f"{len(mensagens)} mensagens pendentes lidas")

        # 2. Ler validações do Validador de Mercado
        scores = self.ler_validacoes()
        if not scores:
            self.registrar_log("Nenhuma validação encontrada", "Aguardando Validador de Mercado")
            self.atualizar_status("aguardando_dados")
            return {}

        self.registrar_log(f"Processando {len(scores)} tendências validadas")

        # 3. Tomar decisões
        resultados = self.processar_validacoes(scores)

        # 4. Acionar Squad 2 para projetos aprovados
        for projeto_dict in resultados["aprovados"]:
            tarefas = projeto_dict.get("tarefas", [])
            if tarefas:
                self.acionar_squad("squad2", tarefas)

        # 5. Gerar e publicar relatório
        relatorio = self.gerar_relatorio_decisoes(resultados)
        self.publicar_resultado("Decisões CEO Agente", relatorio)

        # Salvar decisão
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_decisao = os.path.join(self.pasta_decisoes, f"decisao_{agora}.json")
        with open(arquivo_decisao, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        self.atualizar_status("concluido")
        self.registrar_log(
            "CEO Agente finalizado",
            f"{len(resultados['aprovados'])} aprovados, "
            f"{len(resultados['monitorar'])} monitorando, "
            f"{len(resultados['descartados'])} descartados",
        )
        return resultados


# --- Execução direta ---
if __name__ == "__main__":
    agente = CEOAgente()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Decisões: {len(resultados.get('aprovados', []))} aprovados, "
          f"{len(resultados.get('monitorar', []))} monitorando, "
          f"{len(resultados.get('descartados', []))} descartados.")
