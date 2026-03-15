"""
ESPECIALISTA DAY TRADE — Squad 4: Operacoes Financeiras (MODO SUGESTAO)
Analisa mini-indice e mini-dolar, detecta setups (9.1 Larry Williams, reversao MA20)
e gera sugestoes de operacao. NUNCA executa trades automaticamente.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, INTELIGENCIA_DIR


class EspecialistaDayTrade(BaseAgente):
    """Agente especialista em day trade — deteccao de setups e gestao de risco."""

    MODO = "SUGESTAO"

    MAX_RISCO_POR_TRADE = 0.02  # 2% do capital por operacao

    ATIVOS = {
        "WIN": {"nome": "Mini Indice Bovespa", "tick": 5, "valor_tick": 1.00},
        "WDO": {"nome": "Mini Dolar", "tick": 0.5, "valor_tick": 5.00},
    }

    SETUPS_DISPONIVEIS = ["9.1_larry_williams", "reversao_ma20", "rompimento_range"]

    def __init__(self):
        super().__init__(
            nome="Especialista Day Trade",
            squad="Squad 4 — Operacoes Financeiras",
            papel="Deteccao de setups e sugestoes de operacoes day trade",
        )
        self.pasta_daytrade = os.path.join(NEXUS_ROOT, "financeiro", "daytrade")
        os.makedirs(self.pasta_daytrade, exist_ok=True)

    def _verificar_modo(self) -> bool:
        if self.MODO != "SUGESTAO":
            self.registrar_log("BLOQUEIO: tentativa de operar fora do modo SUGESTAO", "NEGADO")
            return False
        return True

    def calcular_media_movel(self, dados: list[dict], periodo: int, campo: str = "close") -> list[float]:
        """Calcula media movel simples sobre lista de candles."""
        valores = [c[campo] for c in dados if campo in c]
        if len(valores) < periodo:
            return []
        medias = []
        for i in range(periodo - 1, len(valores)):
            janela = valores[i - periodo + 1 : i + 1]
            medias.append(round(sum(janela) / periodo, 2))
        return medias

    def detectar_setup(self, ativo: str, dados: list[dict]) -> dict:
        """
        Detecta setups de day trade nos dados fornecidos.
        dados: lista de candles [{"open", "high", "low", "close", "volume"}, ...]
        Retorna dict com setups encontrados.
        """
        if not self._verificar_modo():
            return {}

        if ativo not in self.ATIVOS:
            return {"erro": f"Ativo {ativo} nao suportado. Disponiveis: {list(self.ATIVOS.keys())}"}

        if not dados or len(dados) < 21:
            return {"erro": "Dados insuficientes (minimo 21 candles)"}

        setups_encontrados = []

        # Setup 9.1 Larry Williams
        setup_91 = self._detectar_91_larry(dados)
        if setup_91:
            setups_encontrados.append(setup_91)

        # Reversao MA20
        setup_ma20 = self._detectar_reversao_ma20(dados)
        if setup_ma20:
            setups_encontrados.append(setup_ma20)

        # Rompimento de Range
        setup_range = self._detectar_rompimento_range(dados)
        if setup_range:
            setups_encontrados.append(setup_range)

        resultado = {
            "ativo": ativo,
            "info_ativo": self.ATIVOS[ativo],
            "num_candles_analisados": len(dados),
            "setups_encontrados": setups_encontrados,
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
        }

        self.registrar_log(
            f"Deteccao de setup: {ativo}",
            f"{len(setups_encontrados)} setups encontrados",
        )
        return resultado

    def _detectar_91_larry(self, dados: list[dict]) -> dict | None:
        """
        Setup 9.1 Larry Williams: media movel exponencial de 9 periodos.
        Sinal de compra quando candle faz minima abaixo da minima anterior
        mas fecha acima da minima anterior (barra de reversao).
        """
        if len(dados) < 10:
            return None

        closes = [c["close"] for c in dados]
        # Media movel simples de 9 como proxy
        ma9 = self.calcular_media_movel(dados, 9)
        if not ma9:
            return None

        ultimo = dados[-1]
        penultimo = dados[-2]

        # Condicao compra: minima atual < minima anterior e fechamento > minima anterior
        compra = ultimo["low"] < penultimo["low"] and ultimo["close"] > penultimo["low"]
        # Condicao venda: maxima atual > maxima anterior e fechamento < maxima anterior
        venda = ultimo["high"] > penultimo["high"] and ultimo["close"] < penultimo["high"]

        if compra:
            return {
                "tipo_setup": "9.1_larry_williams",
                "direcao": "COMPRA",
                "entrada_sugerida": penultimo["high"],
                "stop_loss": ultimo["low"],
                "descricao": "Barra de reversao com minima abaixo da anterior e fechamento acima",
                "ma9": ma9[-1],
            }
        elif venda:
            return {
                "tipo_setup": "9.1_larry_williams",
                "direcao": "VENDA",
                "entrada_sugerida": penultimo["low"],
                "stop_loss": ultimo["high"],
                "descricao": "Barra de reversao com maxima acima da anterior e fechamento abaixo",
                "ma9": ma9[-1],
            }
        return None

    def _detectar_reversao_ma20(self, dados: list[dict]) -> dict | None:
        """
        Reversao na MA20: preco toca a media de 20 periodos e reverte.
        """
        ma20 = self.calcular_media_movel(dados, 20)
        if not ma20 or len(ma20) < 2:
            return None

        ultimo = dados[-1]
        ma_atual = ma20[-1]

        # Preco tocou a MA20 (dentro de 0.3% da media)
        distancia_pct = abs(ultimo["low"] - ma_atual) / ma_atual
        if distancia_pct > 0.003:
            distancia_pct_high = abs(ultimo["high"] - ma_atual) / ma_atual
            if distancia_pct_high > 0.003:
                return None

        # Compra: preco veio de cima, tocou MA20, fechou acima
        if ultimo["close"] > ma_atual and ultimo["low"] <= ma_atual * 1.003:
            return {
                "tipo_setup": "reversao_ma20",
                "direcao": "COMPRA",
                "entrada_sugerida": round(ma_atual * 1.001, 2),
                "stop_loss": round(ma_atual * 0.995, 2),
                "descricao": "Toque na MA20 com reversao de alta",
                "ma20": ma_atual,
            }
        # Venda: preco veio de baixo, tocou MA20, fechou abaixo
        if ultimo["close"] < ma_atual and ultimo["high"] >= ma_atual * 0.997:
            return {
                "tipo_setup": "reversao_ma20",
                "direcao": "VENDA",
                "entrada_sugerida": round(ma_atual * 0.999, 2),
                "stop_loss": round(ma_atual * 1.005, 2),
                "descricao": "Toque na MA20 com reversao de baixa",
                "ma20": ma_atual,
            }
        return None

    def _detectar_rompimento_range(self, dados: list[dict]) -> dict | None:
        """Detecta rompimento de range dos ultimos 10 candles."""
        if len(dados) < 11:
            return None

        range_dados = dados[-11:-1]
        max_range = max(c["high"] for c in range_dados)
        min_range = min(c["low"] for c in range_dados)
        ultimo = dados[-1]

        if ultimo["close"] > max_range:
            return {
                "tipo_setup": "rompimento_range",
                "direcao": "COMPRA",
                "entrada_sugerida": round(max_range, 2),
                "stop_loss": round(min_range, 2),
                "descricao": f"Rompimento de topo do range ({min_range:.2f} - {max_range:.2f})",
                "range_max": max_range,
                "range_min": min_range,
            }
        elif ultimo["close"] < min_range:
            return {
                "tipo_setup": "rompimento_range",
                "direcao": "VENDA",
                "entrada_sugerida": round(min_range, 2),
                "stop_loss": round(max_range, 2),
                "descricao": f"Rompimento de fundo do range ({min_range:.2f} - {max_range:.2f})",
                "range_max": max_range,
                "range_min": min_range,
            }
        return None

    def calcular_risco(self, capital: float, entrada: float, stop_loss: float, ativo: str) -> dict:
        """
        Calcula gestao de risco: tamanho de posicao respeitando max 2% de risco.
        """
        if ativo not in self.ATIVOS:
            return {"erro": f"Ativo {ativo} nao suportado"}

        info = self.ATIVOS[ativo]
        risco_maximo = capital * self.MAX_RISCO_POR_TRADE
        distancia_stop = abs(entrada - stop_loss)

        if distancia_stop == 0:
            return {"erro": "Distancia do stop nao pode ser zero"}

        ticks_risco = distancia_stop / info["tick"]
        risco_por_contrato = ticks_risco * info["valor_tick"]

        if risco_por_contrato == 0:
            return {"erro": "Risco por contrato calculado como zero"}

        contratos = int(risco_maximo / risco_por_contrato)
        contratos = max(contratos, 0)

        return {
            "capital": capital,
            "risco_maximo_reais": round(risco_maximo, 2),
            "entrada": entrada,
            "stop_loss": stop_loss,
            "distancia_stop_pts": round(distancia_stop, 2),
            "risco_por_contrato": round(risco_por_contrato, 2),
            "contratos_sugeridos": contratos,
            "risco_total": round(contratos * risco_por_contrato, 2),
            "pct_capital_arriscado": round((contratos * risco_por_contrato / capital) * 100, 2) if capital > 0 else 0,
        }

    def gerar_sugestao_operacao(self, setup: dict, capital: float = 50000.0) -> dict:
        """Gera sugestao de operacao completa a partir de um setup detectado. NUNCA auto-trade."""
        if not self._verificar_modo():
            return {}

        entrada = setup.get("entrada_sugerida", 0)
        stop = setup.get("stop_loss", 0)
        direcao = setup.get("direcao", "N/A")
        distancia = abs(entrada - stop)
        alvo = entrada + (distancia * 2) if direcao == "COMPRA" else entrada - (distancia * 2)

        sugestao = {
            "setup": setup["tipo_setup"],
            "direcao": direcao,
            "entrada": entrada,
            "stop_loss": stop,
            "alvo_1": round(alvo, 2),
            "risco_retorno": "1:2",
            "gestao_risco": self.calcular_risco(capital, entrada, stop, "WIN"),
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "aviso": "SUGESTAO APENAS — nao executa trade automaticamente",
        }

        self.registrar_log(
            f"Sugestao gerada: {setup['tipo_setup']}",
            f"{direcao} entrada {entrada}",
        )
        return sugestao

    def _gerar_dados_exemplo(self, ativo: str) -> list[dict]:
        """Gera dados de candle de exemplo para demonstracao."""
        import random
        random.seed(42)
        base = 128000 if ativo == "WIN" else 5000
        dados = []
        for i in range(25):
            abertura = base + random.uniform(-200, 200)
            fechamento = abertura + random.uniform(-150, 150)
            maxima = max(abertura, fechamento) + random.uniform(0, 100)
            minima = min(abertura, fechamento) - random.uniform(0, 100)
            dados.append({
                "open": round(abertura, 2),
                "high": round(maxima, 2),
                "low": round(minima, 2),
                "close": round(fechamento, 2),
                "volume": random.randint(5000, 50000),
            })
            base = fechamento
        return dados

    def _salvar_sugestoes(self, resultado: dict):
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_daytrade, f"sugestoes_{agora}.json")
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        self.registrar_log("Sugestoes daytrade salvas", arquivo)

    def executar(self):
        """Loop principal do Especialista Day Trade."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Especialista Day Trade iniciado", "Analise de setups")

        if not self._verificar_modo():
            self.atualizar_status("bloqueado")
            return

        resultados = {}
        for ativo in self.ATIVOS:
            dados = self._gerar_dados_exemplo(ativo)
            deteccao = self.detectar_setup(ativo, dados)
            sugestoes_ativo = []

            for setup in deteccao.get("setups_encontrados", []):
                sugestao = self.gerar_sugestao_operacao(setup)
                sugestoes_ativo.append(sugestao)

            resultados[ativo] = {
                "deteccao": deteccao,
                "sugestoes": sugestoes_ativo,
            }

        self._salvar_sugestoes(resultados)
        self.publicar_resultado("Analise Day Trade", resultados)

        # Notificar CFO
        total_setups = sum(
            len(r["deteccao"].get("setups_encontrados", []))
            for r in resultados.values()
        )
        self.enviar_mensagem(
            destinatario="cfo",
            assunto="Sugestoes Day Trade Disponiveis",
            conteudo=(
                f"Especialista Day Trade completou analise.\n"
                f"**Setups detectados:** {total_setups}\n"
                f"**Ativos analisados:** {', '.join(resultados.keys())}\n\n"
                f"**Modo:** {self.MODO} — nenhum trade executado."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Especialista Day Trade finalizado", f"{total_setups} setups detectados")
        return resultados


if __name__ == "__main__":
    agente = EspecialistaDayTrade()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    if resultado:
        for ativo, info in resultado.items():
            setups = len(info["deteccao"].get("setups_encontrados", []))
            print(f"  {ativo}: {setups} setups encontrados")
    print("Concluido (modo SUGESTAO).")
