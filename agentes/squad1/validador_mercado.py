"""
VALIDADOR DE MERCADO — Squad 1: Inteligência & Validação
Valida demanda de tendências usando Google Trends (pytrends), SEMrush e fontes públicas.
Gera score multi-dimensional para cada oportunidade.
"""

import os
import sys
import json
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, INTELIGENCIA_DIR


# ---------------------------------------------------------------------------
# Scoring Engine — multi-dimensional, rubric-based
# ---------------------------------------------------------------------------

@dataclass
class ScoreValidacao:
    """Score multi-dimensional de validação de mercado."""
    keyword: str
    plataforma_origem: str = ""

    # Dimensões individuais (0-10)
    demanda: float = 0.0          # Volume de busca / interesse real
    tendencia: float = 0.0        # Crescendo, estável ou caindo
    concorrencia: float = 0.0     # 10 = sem concorrência no BR (invertido)
    monetizacao: float = 0.0      # Potencial de gerar receita
    viabilidade: float = 0.0      # Podemos construir com nosso stack

    # Pesos para score ponderado
    PESOS: dict = field(default_factory=lambda: {
        "demanda": 0.25,
        "tendencia": 0.25,
        "concorrencia": 0.20,
        "monetizacao": 0.20,
        "viabilidade": 0.10,
    })

    rationale: dict = field(default_factory=dict)
    fontes: list = field(default_factory=list)

    @property
    def score_total(self) -> float:
        """Score ponderado (0-10)."""
        return round(
            self.demanda * self.PESOS["demanda"]
            + self.tendencia * self.PESOS["tendencia"]
            + self.concorrencia * self.PESOS["concorrencia"]
            + self.monetizacao * self.PESOS["monetizacao"]
            + self.viabilidade * self.PESOS["viabilidade"],
            2,
        )

    @property
    def classificacao(self) -> str:
        s = self.score_total
        if s >= 8:
            return "EXCELENTE — prioridade máxima"
        if s >= 6:
            return "BOM — vale investigar"
        if s >= 4:
            return "MODERADO — monitorar"
        return "FRACO — descartar por agora"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score_total"] = self.score_total
        d["classificacao"] = self.classificacao
        d.pop("PESOS", None)
        return d


# ---------------------------------------------------------------------------
# Data Sources — plugáveis para trocar implementação sem mudar o agente
# ---------------------------------------------------------------------------

class FonteDados:
    """Interface base para fontes de dados de validação."""

    nome: str = "base"

    def consultar(self, keyword: str, geo: str = "BR") -> dict:
        raise NotImplementedError


class GoogleTrendsSource(FonteDados):
    """
    Fonte: Google Trends via pytrends.
    Requer: pip install pytrends
    Rate limit: sleep 60s entre requests quando throttled.
    Fallback: gera URLs de consulta manual se pytrends falhar.
    """

    nome = "google_trends"
    RATE_LIMIT_SLEEP = 2  # segundos entre requests normais

    def consultar(self, keyword: str, geo: str = "BR") -> dict:
        resultado = {
            "fonte": self.nome,
            "keyword": keyword,
            "geo": geo,
            "status": "pendente",
            "interesse_temporal": [],
            "interesse_regional": {},
            "queries_relacionadas": [],
            "url_manual": f"https://trends.google.com/trends/explore?q={keyword}&geo={geo}",
        }

        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="pt-BR", tz=180, retries=3, backoff_factor=1.0)
            pytrends.build_payload([keyword], cat=0, timeframe="today 3-m", geo=geo)

            # Interest over time
            df_tempo = pytrends.interest_over_time()
            if not df_tempo.empty and keyword in df_tempo.columns:
                resultado["interesse_temporal"] = df_tempo[keyword].tolist()
                resultado["media_interesse"] = round(df_tempo[keyword].mean(), 1)

            time.sleep(self.RATE_LIMIT_SLEEP)

            # Interest by region
            df_regiao = pytrends.interest_by_region(resolution="COUNTRY")
            if not df_regiao.empty and keyword in df_regiao.columns:
                top_regioes = df_regiao[keyword].nlargest(10)
                resultado["interesse_regional"] = top_regioes.to_dict()

            time.sleep(self.RATE_LIMIT_SLEEP)

            # Related queries
            related = pytrends.related_queries()
            if keyword in related and related[keyword]["rising"] is not None:
                resultado["queries_relacionadas"] = (
                    related[keyword]["rising"]["query"].head(10).tolist()
                )

            resultado["status"] = "coletado"

        except ImportError:
            resultado["status"] = "pytrends_nao_instalado"
            resultado["nota"] = "Instalar com: pip install pytrends"
        except Exception as e:
            resultado["status"] = "erro"
            resultado["erro"] = str(e)

        return resultado


class SEMrushSource(FonteDados):
    """
    Fonte: SEMrush API.
    Requer: SEMRUSH_API_KEY em variável de ambiente.
    Docs: https://developer.semrush.com/api/
    """

    nome = "semrush"

    def consultar(self, keyword: str, geo: str = "br") -> dict:
        resultado = {
            "fonte": self.nome,
            "keyword": keyword,
            "geo": geo,
            "status": "pendente",
            "volume_mensal": 0,
            "cpc": 0.0,
            "concorrencia_paga": 0.0,
            "resultados_organicos": 0,
        }

        api_key = os.environ.get("SEMRUSH_API_KEY")
        if not api_key:
            resultado["status"] = "api_key_ausente"
            resultado["nota"] = "Configurar SEMRUSH_API_KEY no ambiente"
            return resultado

        try:
            import requests

            url = "https://api.semrush.com/"
            params = {
                "type": "phrase_this",
                "key": api_key,
                "phrase": keyword,
                "database": geo,
                "export_columns": "Ph,Nq,Cp,Co,Nr",
            }
            resp = requests.get(url, params=params, timeout=30)

            if resp.status_code == 200 and "ERROR" not in resp.text:
                linhas = resp.text.strip().split("\n")
                if len(linhas) >= 2:
                    campos = linhas[1].split(";")
                    resultado["volume_mensal"] = int(campos[1]) if len(campos) > 1 else 0
                    resultado["cpc"] = float(campos[2]) if len(campos) > 2 else 0.0
                    resultado["concorrencia_paga"] = float(campos[3]) if len(campos) > 3 else 0.0
                    resultado["resultados_organicos"] = int(campos[4]) if len(campos) > 4 else 0
                    resultado["status"] = "coletado"
            else:
                resultado["status"] = "erro_api"
                resultado["erro"] = resp.text[:200]

        except ImportError:
            resultado["status"] = "requests_nao_instalado"
        except Exception as e:
            resultado["status"] = "erro"
            resultado["erro"] = str(e)

        return resultado


# ---------------------------------------------------------------------------
# Agente Principal
# ---------------------------------------------------------------------------

class ValidadorMercado(BaseAgente):
    """Agente que valida demanda de mercado para tendências detectadas pelo Radar China."""

    def __init__(self):
        super().__init__(
            nome="Validador Mercado",
            squad="Squad 1 — Inteligência & Validação",
            papel="Valida demanda com Google Trends + SEMrush e gera scoring",
        )
        self.pasta_validacoes = os.path.join(INTELIGENCIA_DIR, "validacoes")
        os.makedirs(self.pasta_validacoes, exist_ok=True)
        self.fontes: list[FonteDados] = [GoogleTrendsSource(), SEMrushSource()]

    def coletar_dados(self, keyword: str, geo: str = "BR") -> dict:
        """Coleta dados de todas as fontes plugadas."""
        dados = {"keyword": keyword, "geo": geo, "coletas": {}}
        for fonte in self.fontes:
            self.registrar_log(f"Consultando {fonte.nome} para '{keyword}'")
            dados["coletas"][fonte.nome] = fonte.consultar(keyword, geo)
        return dados

    def calcular_score(self, keyword: str, dados_coletados: dict) -> ScoreValidacao:
        """
        Calcula score multi-dimensional baseado nos dados coletados.
        Quando dados reais estão disponíveis, usa heurísticas para pontuar.
        Quando não, marca como pendente para revisão manual.
        """
        score = ScoreValidacao(keyword=keyword)

        # --- Demanda (via Google Trends) ---
        gt = dados_coletados.get("coletas", {}).get("google_trends", {})
        if gt.get("status") == "coletado":
            media = gt.get("media_interesse", 0)
            score.demanda = min(10, round(media / 10, 1))
            score.rationale["demanda"] = f"Google Trends média: {media}/100"
            score.fontes.append("google_trends")

        # --- Tendência (crescimento no tempo) ---
        interesse = gt.get("interesse_temporal", [])
        if len(interesse) >= 4:
            primeira_metade = sum(interesse[: len(interesse) // 2])
            segunda_metade = sum(interesse[len(interesse) // 2 :])
            if primeira_metade > 0:
                crescimento = (segunda_metade - primeira_metade) / primeira_metade
                score.tendencia = min(10, max(0, round(5 + crescimento * 5, 1)))
                score.rationale["tendencia"] = f"Crescimento: {crescimento:.0%}"

        # --- Concorrência (via SEMrush — invertido) ---
        sem = dados_coletados.get("coletas", {}).get("semrush", {})
        if sem.get("status") == "coletado":
            conc = sem.get("concorrencia_paga", 0.5)
            score.concorrencia = round((1 - conc) * 10, 1)
            score.rationale["concorrencia"] = f"SEMrush concorrência paga: {conc}"
            score.fontes.append("semrush")

            # --- Monetização (baseado em CPC) ---
            cpc = sem.get("cpc", 0)
            score.monetizacao = min(10, round(cpc * 2, 1))
            score.rationale["monetizacao"] = f"CPC médio: R${cpc:.2f}"

        # --- Viabilidade (heurística: se temos keywords relacionadas, é construível) ---
        queries = gt.get("queries_relacionadas", [])
        if queries:
            score.viabilidade = min(10, 5 + len(queries) * 0.5)
            score.rationale["viabilidade"] = f"{len(queries)} queries relacionadas encontradas"

        return score

    def validar_tendencia(self, keyword: str, plataforma_origem: str = "") -> ScoreValidacao:
        """Pipeline completo: coletar → pontuar → retornar score."""
        self.registrar_log(f"Validando tendência: '{keyword}'", f"origem: {plataforma_origem}")
        dados = self.coletar_dados(keyword)
        score = self.calcular_score(keyword, dados)
        score.plataforma_origem = plataforma_origem
        return score

    def validar_lote(self, tendencias: list[dict]) -> list[ScoreValidacao]:
        """Valida um lote de tendências (ex: output do Radar China)."""
        scores = []
        for t in tendencias:
            kw = t.get("keyword", "")
            plat = t.get("plataforma", "")
            if kw:
                score = self.validar_tendencia(kw, plat)
                scores.append(score)
        return scores

    def gerar_relatorio(self, scores: list[ScoreValidacao]) -> str:
        """Gera relatório rankeado por score total."""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        scores_sorted = sorted(scores, key=lambda s: s.score_total, reverse=True)

        relatorio = (
            f"# Relatório de Validação de Mercado\n"
            f"**Data:** {agora}\n"
            f"**Keywords validadas:** {len(scores)}\n\n"
            f"## Ranking\n\n"
            f"| # | Keyword | Score | Classificação | Demanda | Tendência | Concorrência | Monetização |\n"
            f"|---|---------|-------|---------------|---------|-----------|--------------|-------------|\n"
        )
        for i, s in enumerate(scores_sorted, 1):
            relatorio += (
                f"| {i} | {s.keyword} | **{s.score_total}** | {s.classificacao} "
                f"| {s.demanda} | {s.tendencia} | {s.concorrencia} | {s.monetizacao} |\n"
            )

        # Top 5 para o CEO Agente
        top5 = scores_sorted[:5]
        relatorio += "\n## Top 5 — Recomendação para CEO Agente\n"
        for i, s in enumerate(top5, 1):
            relatorio += f"{i}. **{s.keyword}** (score {s.score_total}) — {s.classificacao}\n"
            for dim, rat in s.rationale.items():
                relatorio += f"   - {dim}: {rat}\n"

        return relatorio

    def salvar_scores(self, scores: list[ScoreValidacao]):
        """Persiste scores em JSON."""
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_validacoes, f"validacao_{agora}.json")
        dados = [s.to_dict() for s in scores]
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        self.registrar_log("Scores salvos", arquivo)

    def executar(self):
        """Loop principal: lê tendências do Radar China, valida e notifica CEO Agente."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Validador de Mercado iniciado")

        # 1. Ler tendências do Radar China
        pasta_radar = os.path.join(INTELIGENCIA_DIR, "radar_china")
        tendencias = []
        if os.path.exists(pasta_radar):
            arquivos = sorted(
                [f for f in os.listdir(pasta_radar) if f.endswith(".json")],
                reverse=True,
            )
            if arquivos:
                ultimo = os.path.join(pasta_radar, arquivos[0])
                with open(ultimo, "r", encoding="utf-8") as f:
                    tendencias = json.load(f)
                self.registrar_log(f"Lidas {len(tendencias)} tendências do Radar China", ultimo)

        if not tendencias:
            self.registrar_log("Nenhuma tendência encontrada", "Aguardando Radar China")
            self.atualizar_status("aguardando_dados")
            return []

        # 2. Validar lote
        # Deduplica keywords antes de validar
        keywords_unicas = {}
        for t in tendencias:
            kw = t.get("keyword", "")
            if kw and kw not in keywords_unicas:
                keywords_unicas[kw] = t
        tendencias_unicas = list(keywords_unicas.values())

        self.registrar_log(
            f"Validando {len(tendencias_unicas)} keywords únicas",
            f"(de {len(tendencias)} totais)",
        )
        scores = self.validar_lote(tendencias_unicas)

        # 3. Salvar e publicar
        self.salvar_scores(scores)
        relatorio = self.gerar_relatorio(scores)
        self.publicar_resultado("Validação de Mercado", relatorio)

        # 4. Notificar CEO Agente com top 5
        top5 = sorted(scores, key=lambda s: s.score_total, reverse=True)[:5]
        resumo_top5 = "\n".join(
            f"- {s.keyword}: score {s.score_total} ({s.classificacao})" for s in top5
        )
        self.enviar_mensagem(
            destinatario="ceo_agente",
            assunto="Top 5 tendências validadas — decisão necessária",
            conteudo=(
                f"Validação concluída: {len(scores)} keywords analisadas.\n\n"
                f"**Top 5:**\n{resumo_top5}\n\n"
                f"Dados completos em: {self.pasta_validacoes}\n"
                f"Ação: definir quais tendências viram projeto."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Validador finalizado", f"{len(scores)} scores gerados")
        return scores


# --- Execução direta ---
if __name__ == "__main__":
    agente = ValidadorMercado()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} keywords validadas.")
