"""
ESPECIALISTA CRIPTO — Squad 4: Operacoes Financeiras (MODO SUGESTAO)
Monitora mercado de criptomoedas via CoinGecko (API publica, sem chave).
Gera analises tecnicas e sugestoes. NUNCA executa trades automaticamente.
"""

import os
import sys
import json
import math
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, INTELIGENCIA_DIR

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    urlopen = None


class EspecialistaCripto(BaseAgente):
    """Agente especialista em analise de criptomoedas — modo sugestao."""

    MODO = "SUGESTAO"

    ATIVOS_MONITORADOS = {
        "bitcoin": {"simbolo": "BTC", "nome": "Bitcoin"},
        "ethereum": {"simbolo": "ETH", "nome": "Ethereum"},
        "solana": {"simbolo": "SOL", "nome": "Solana"},
    }

    COINGECKO_BASE = "https://api.coingecko.com/api/v3"

    def __init__(self):
        super().__init__(
            nome="Especialista Cripto",
            squad="Squad 4 — Operacoes Financeiras",
            papel="Analise de mercado cripto e geracao de sugestoes de operacao",
        )
        self.pasta_cripto = os.path.join(NEXUS_ROOT, "financeiro", "cripto")
        os.makedirs(self.pasta_cripto, exist_ok=True)

    def _verificar_modo(self) -> bool:
        if self.MODO != "SUGESTAO":
            self.registrar_log("BLOQUEIO: tentativa de operar fora do modo SUGESTAO", "NEGADO")
            return False
        return True

    def _fazer_request(self, url: str) -> dict | list | None:
        """Faz request HTTP GET e retorna JSON parseado."""
        if urlopen is None:
            self.registrar_log("urllib nao disponivel", "ERRO")
            return None
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "NexusAutonomous/1.0"})
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, json.JSONDecodeError, OSError) as e:
            self.registrar_log(f"Erro na request: {url}", str(e))
            return None

    def obter_precos(self) -> dict:
        """Obtem precos atuais via CoinGecko API."""
        ids = ",".join(self.ATIVOS_MONITORADOS.keys())
        url = f"{self.COINGECKO_BASE}/simple/price?ids={ids}&vs_currencies=usd,brl&include_24hr_change=true"
        dados = self._fazer_request(url)
        if not dados:
            self.registrar_log("Falha ao obter precos", "Usando dados offline")
            return {}
        precos = {}
        for ativo_id, info in self.ATIVOS_MONITORADOS.items():
            if ativo_id in dados:
                precos[info["simbolo"]] = {
                    "preco_usd": dados[ativo_id].get("usd", 0),
                    "preco_brl": dados[ativo_id].get("brl", 0),
                    "variacao_24h": dados[ativo_id].get("usd_24h_change", 0),
                }
        return precos

    def obter_historico(self, ativo_id: str, dias: int = 30) -> list[float]:
        """Obtem historico de precos (fechamento diario) via CoinGecko."""
        url = f"{self.COINGECKO_BASE}/coins/{ativo_id}/market_chart?vs_currency=usd&days={dias}&interval=daily"
        dados = self._fazer_request(url)
        if not dados or "prices" not in dados:
            return []
        return [p[1] for p in dados["prices"]]

    def calcular_media_movel(self, precos: list[float], periodo: int) -> list[float]:
        """Calcula media movel simples para um dado periodo."""
        if len(precos) < periodo:
            return []
        medias = []
        for i in range(periodo - 1, len(precos)):
            janela = precos[i - periodo + 1 : i + 1]
            medias.append(round(sum(janela) / periodo, 2))
        return medias

    def calcular_rsi(self, precos: list[float], periodo: int = 14) -> float | None:
        """Calcula RSI (Relative Strength Index) a partir de precos de fechamento."""
        if len(precos) < periodo + 1:
            return None
        ganhos = []
        perdas = []
        for i in range(1, len(precos)):
            diff = precos[i] - precos[i - 1]
            ganhos.append(max(diff, 0))
            perdas.append(max(-diff, 0))

        ganhos_recentes = ganhos[-(periodo):]
        perdas_recentes = perdas[-(periodo):]

        media_ganho = sum(ganhos_recentes) / periodo
        media_perda = sum(perdas_recentes) / periodo

        if media_perda == 0:
            return 100.0
        rs = media_ganho / media_perda
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def _interpretar_rsi(self, rsi: float | None) -> str:
        if rsi is None:
            return "dados insuficientes"
        if rsi >= 70:
            return "sobrecomprado — possivel correcao"
        if rsi <= 30:
            return "sobrevendido — possivel recuperacao"
        return "neutro"

    def _interpretar_medias(self, preco_atual: float, ma7: list[float], ma30: list[float]) -> str:
        if not ma7 or not ma30:
            return "dados insuficientes"
        if ma7[-1] > ma30[-1] and preco_atual > ma7[-1]:
            return "tendencia de alta — preco acima das medias"
        if ma7[-1] < ma30[-1] and preco_atual < ma7[-1]:
            return "tendencia de baixa — preco abaixo das medias"
        return "lateralizado — medias convergindo"

    def analisar_mercado(self) -> dict:
        """Analisa mercado completo: precos, RSI, medias moveis. Retorna dict consolidado."""
        if not self._verificar_modo():
            return {}

        precos_atuais = self.obter_precos()
        analise = {
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "ativos": {},
        }

        for ativo_id, info in self.ATIVOS_MONITORADOS.items():
            simbolo = info["simbolo"]
            historico = self.obter_historico(ativo_id, dias=30)
            rsi = self.calcular_rsi(historico) if historico else None
            ma7 = self.calcular_media_movel(historico, 7) if historico else []
            ma30 = self.calcular_media_movel(historico, 30) if historico else []

            preco_info = precos_atuais.get(simbolo, {})
            preco_usd = preco_info.get("preco_usd", historico[-1] if historico else 0)

            analise["ativos"][simbolo] = {
                "nome": info["nome"],
                "preco_usd": preco_usd,
                "preco_brl": preco_info.get("preco_brl", 0),
                "variacao_24h": preco_info.get("variacao_24h", 0),
                "rsi_14": rsi,
                "sinal_rsi": self._interpretar_rsi(rsi),
                "ma7_ultimo": ma7[-1] if ma7 else None,
                "ma30_ultimo": ma30[-1] if ma30 else None,
                "sinal_medias": self._interpretar_medias(preco_usd, ma7, ma30),
            }

        self.registrar_log("Analise de mercado cripto concluida", f"{len(analise['ativos'])} ativos")
        return analise

    def gerar_sugestao(self, ativo: str) -> dict:
        """
        Gera sugestao de operacao para um ativo especifico.
        NUNCA executa trades — apenas retorna sugestao.
        """
        if not self._verificar_modo():
            return {}

        ativo_upper = ativo.upper()
        ativo_id = None
        for aid, info in self.ATIVOS_MONITORADOS.items():
            if info["simbolo"] == ativo_upper:
                ativo_id = aid
                break
        if not ativo_id:
            return {"erro": f"Ativo {ativo} nao monitorado"}

        historico = self.obter_historico(ativo_id, dias=30)
        if not historico or len(historico) < 15:
            return {"erro": "Dados historicos insuficientes para analise"}

        rsi = self.calcular_rsi(historico)
        ma7 = self.calcular_media_movel(historico, 7)
        preco_atual = historico[-1]

        if rsi is not None and rsi <= 30:
            acao = "COMPRA"
            motivo = f"RSI em {rsi} indica sobrevendido"
            confianca = min(90, 50 + (30 - rsi))
        elif rsi is not None and rsi >= 70:
            acao = "VENDA"
            motivo = f"RSI em {rsi} indica sobrecomprado"
            confianca = min(90, 50 + (rsi - 70))
        else:
            acao = "AGUARDAR"
            motivo = "Indicadores em zona neutra"
            confianca = 30

        sugestao = {
            "ativo": ativo_upper,
            "acao_sugerida": acao,
            "motivo": motivo,
            "confianca_pct": round(confianca, 1),
            "preco_atual": round(preco_atual, 2),
            "rsi": rsi,
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "aviso": "SUGESTAO APENAS — nao executa trade automaticamente",
        }

        self.registrar_log(f"Sugestao gerada: {ativo_upper}", f"{acao} (confianca {confianca:.0f}%)")
        return sugestao

    def _salvar_analise(self, analise: dict):
        """Salva analise em arquivo JSON na pasta cripto."""
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_cripto, f"analise_{agora}.json")
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(analise, f, ensure_ascii=False, indent=2)
        self.registrar_log("Analise cripto salva", arquivo)
        return arquivo

    def executar(self):
        """Loop principal do Especialista Cripto."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Especialista Cripto iniciado", "Analise completa de mercado")

        if not self._verificar_modo():
            self.atualizar_status("bloqueado")
            return

        # Analisar mercado
        analise = self.analisar_mercado()
        self._salvar_analise(analise)

        # Gerar sugestoes para cada ativo
        sugestoes = {}
        for info in self.ATIVOS_MONITORADOS.values():
            sugestao = self.gerar_sugestao(info["simbolo"])
            sugestoes[info["simbolo"]] = sugestao

        # Publicar resultado consolidado
        resultado = {"analise_mercado": analise, "sugestoes": sugestoes}
        self.publicar_resultado("Analise Cripto Completa", resultado)

        # Notificar CFO
        resumo_linhas = []
        for simb, sug in sugestoes.items():
            if "acao_sugerida" in sug:
                resumo_linhas.append(f"- **{simb}:** {sug['acao_sugerida']} (confianca {sug.get('confianca_pct', 0)}%)")
        self.enviar_mensagem(
            destinatario="cfo",
            assunto="Analise Cripto Disponivel",
            conteudo=(
                f"Especialista Cripto completou analise.\n\n"
                + "\n".join(resumo_linhas) + "\n\n"
                f"**Modo:** {self.MODO} — nenhum trade executado."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Especialista Cripto finalizado", f"{len(sugestoes)} sugestoes geradas")
        return resultado


if __name__ == "__main__":
    agente = EspecialistaCripto()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    if resultado:
        for simb, sug in resultado.get("sugestoes", {}).items():
            acao = sug.get("acao_sugerida", "N/A")
            print(f"  {simb}: {acao}")
    print("Concluido (modo SUGESTAO).")
