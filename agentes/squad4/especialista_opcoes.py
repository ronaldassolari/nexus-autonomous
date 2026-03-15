"""
ESPECIALISTA OPCOES — Squad 4: Operacoes Financeiras (MODO SUGESTAO)
Analisa estrategias com opcoes (covered call, spreads, butterfly, condor).
Calcula gregas via Black-Scholes. NUNCA executa trades automaticamente.
"""

import os
import sys
import json
import math
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, INTELIGENCIA_DIR


class EspecialistaOpcoes(BaseAgente):
    """Agente especialista em estrategias com opcoes e calculo de gregas."""

    MODO = "SUGESTAO"

    ESTRATEGIAS_DISPONIVEIS = [
        "covered_call", "bull_call_spread", "bear_put_spread",
        "butterfly", "iron_condor", "straddle",
    ]

    def __init__(self):
        super().__init__(
            nome="Especialista Opcoes",
            squad="Squad 4 — Operacoes Financeiras",
            papel="Analise de estrategias com opcoes e calculo de gregas",
        )
        self.pasta_opcoes = os.path.join(NEXUS_ROOT, "financeiro", "opcoes")
        os.makedirs(self.pasta_opcoes, exist_ok=True)

    def _verificar_modo(self) -> bool:
        if self.MODO != "SUGESTAO":
            self.registrar_log("BLOQUEIO: tentativa de operar fora do modo SUGESTAO", "NEGADO")
            return False
        return True

    # --- Black-Scholes ---

    def _norm_cdf(self, x: float) -> float:
        """Aproximacao da funcao cumulativa normal padrao."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _norm_pdf(self, x: float) -> float:
        """Funcao densidade de probabilidade normal padrao."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    def _d1(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0.0
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    def _d2(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        return self._d1(S, K, T, r, sigma) - sigma * math.sqrt(T) if T > 0 and sigma > 0 else 0.0

    def preco_black_scholes(self, S: float, K: float, T: float, r: float, sigma: float, tipo: str = "call") -> float:
        """
        Calcula preco teorico de opcao via Black-Scholes.
        S: preco do ativo, K: strike, T: tempo ate vencimento (anos),
        r: taxa livre de risco, sigma: volatilidade.
        """
        if T <= 0:
            if tipo == "call":
                return max(S - K, 0)
            return max(K - S, 0)

        d1 = self._d1(S, K, T, r, sigma)
        d2 = self._d2(S, K, T, r, sigma)

        if tipo == "call":
            return round(S * self._norm_cdf(d1) - K * math.exp(-r * T) * self._norm_cdf(d2), 4)
        return round(K * math.exp(-r * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1), 4)

    def calcular_gregas(self, S: float, K: float, T: float, r: float, sigma: float, tipo: str = "call") -> dict:
        """
        Calcula gregas (delta, gamma, theta, vega) via Black-Scholes.
        """
        if T <= 0 or sigma <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

        d1 = self._d1(S, K, T, r, sigma)
        d2 = self._d2(S, K, T, r, sigma)
        sqrt_T = math.sqrt(T)

        # Delta
        if tipo == "call":
            delta = self._norm_cdf(d1)
        else:
            delta = self._norm_cdf(d1) - 1

        # Gamma (igual para call e put)
        gamma = self._norm_pdf(d1) / (S * sigma * sqrt_T) if S > 0 else 0

        # Theta (por dia)
        theta_comum = -(S * self._norm_pdf(d1) * sigma) / (2 * sqrt_T)
        if tipo == "call":
            theta = theta_comum - r * K * math.exp(-r * T) * self._norm_cdf(d2)
        else:
            theta = theta_comum + r * K * math.exp(-r * T) * self._norm_cdf(-d2)
        theta_diario = theta / 365

        # Vega (por 1% de variacao na vol)
        vega = S * sqrt_T * self._norm_pdf(d1) / 100

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta_diario, 4),
            "vega": round(vega, 4),
        }

    def calcular_estrategia(self, tipo: str, ativo: str, strikes: list[float], premios: list[float],
                             S: float = 0, T: float = 0.083, r: float = 0.1075, sigma: float = 0.25) -> dict:
        """
        Calcula parametros de uma estrategia de opcoes.
        tipo: nome da estrategia
        ativo: ticker do ativo-objeto
        strikes: lista de strikes envolvidos
        premios: lista de premios correspondentes
        S: preco atual do ativo (se 0, usa primeiro strike como referencia)
        """
        if not self._verificar_modo():
            return {}

        if tipo not in self.ESTRATEGIAS_DISPONIVEIS:
            return {"erro": f"Estrategia {tipo} nao disponivel. Opcoes: {self.ESTRATEGIAS_DISPONIVEIS}"}

        S = S if S > 0 else strikes[0] * 0.98

        if tipo == "covered_call":
            return self._estrategia_covered_call(ativo, S, strikes, premios, T, r, sigma)
        elif tipo == "bull_call_spread":
            return self._estrategia_bull_call_spread(ativo, S, strikes, premios, T, r, sigma)
        elif tipo == "bear_put_spread":
            return self._estrategia_bear_put_spread(ativo, S, strikes, premios, T, r, sigma)
        elif tipo == "butterfly":
            return self._estrategia_butterfly(ativo, S, strikes, premios, T, r, sigma)
        elif tipo == "iron_condor":
            return self._estrategia_iron_condor(ativo, S, strikes, premios, T, r, sigma)
        elif tipo == "straddle":
            return self._estrategia_straddle(ativo, S, strikes, premios, T, r, sigma)
        return {"erro": "Estrategia nao implementada"}

    def _estrategia_covered_call(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 1 or len(premios) < 1:
            return {"erro": "Covered call requer 1 strike e 1 premio"}
        K = strikes[0]
        premio = premios[0]
        gregas = self.calcular_gregas(S, K, T, r, sigma, "call")
        lucro_max = (K - S) + premio
        perda_max = S - premio  # ativo vai a zero (teorico)
        breakeven = S - premio
        return {
            "estrategia": "covered_call", "ativo": ativo,
            "posicoes": [
                {"tipo": "acao", "direcao": "compra", "preco": S, "qtd": 100},
                {"tipo": "call", "direcao": "venda", "strike": K, "premio": premio, "qtd": 100},
            ],
            "lucro_maximo": round(lucro_max, 2),
            "perda_maxima_teorica": round(perda_max, 2),
            "breakeven": round(breakeven, 2),
            "gregas_call": gregas,
            "modo": self.MODO,
        }

    def _estrategia_bull_call_spread(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 2 or len(premios) < 2:
            return {"erro": "Bull call spread requer 2 strikes e 2 premios"}
        K1, K2 = sorted(strikes[:2])
        p1, p2 = premios[0], premios[1]
        custo = p1 - p2
        lucro_max = (K2 - K1) - custo
        return {
            "estrategia": "bull_call_spread", "ativo": ativo,
            "posicoes": [
                {"tipo": "call", "direcao": "compra", "strike": K1, "premio": p1},
                {"tipo": "call", "direcao": "venda", "strike": K2, "premio": p2},
            ],
            "custo_liquido": round(custo, 2),
            "lucro_maximo": round(lucro_max, 2),
            "perda_maxima": round(custo, 2),
            "breakeven": round(K1 + custo, 2),
            "modo": self.MODO,
        }

    def _estrategia_bear_put_spread(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 2 or len(premios) < 2:
            return {"erro": "Bear put spread requer 2 strikes e 2 premios"}
        K1, K2 = sorted(strikes[:2])
        p1, p2 = premios[0], premios[1]
        custo = p2 - p1
        lucro_max = (K2 - K1) - custo
        return {
            "estrategia": "bear_put_spread", "ativo": ativo,
            "posicoes": [
                {"tipo": "put", "direcao": "compra", "strike": K2, "premio": p2},
                {"tipo": "put", "direcao": "venda", "strike": K1, "premio": p1},
            ],
            "custo_liquido": round(custo, 2),
            "lucro_maximo": round(lucro_max, 2),
            "perda_maxima": round(custo, 2),
            "breakeven": round(K2 - custo, 2),
            "modo": self.MODO,
        }

    def _estrategia_butterfly(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 3 or len(premios) < 3:
            return {"erro": "Butterfly requer 3 strikes e 3 premios"}
        K1, K2, K3 = sorted(strikes[:3])
        custo = premios[0] - 2 * premios[1] + premios[2]
        lucro_max = (K2 - K1) - abs(custo)
        return {
            "estrategia": "butterfly", "ativo": ativo,
            "posicoes": [
                {"tipo": "call", "direcao": "compra", "strike": K1, "premio": premios[0]},
                {"tipo": "call", "direcao": "venda", "strike": K2, "premio": premios[1], "qtd": 2},
                {"tipo": "call", "direcao": "compra", "strike": K3, "premio": premios[2]},
            ],
            "custo_liquido": round(abs(custo), 2),
            "lucro_maximo": round(lucro_max, 2),
            "perda_maxima": round(abs(custo), 2),
            "breakeven_inferior": round(K1 + abs(custo), 2),
            "breakeven_superior": round(K3 - abs(custo), 2),
            "modo": self.MODO,
        }

    def _estrategia_iron_condor(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 4 or len(premios) < 4:
            return {"erro": "Iron condor requer 4 strikes e 4 premios"}
        K1, K2, K3, K4 = sorted(strikes[:4])
        credito = (premios[1] + premios[2]) - (premios[0] + premios[3])
        perda_max = (K2 - K1) - credito
        return {
            "estrategia": "iron_condor", "ativo": ativo,
            "posicoes": [
                {"tipo": "put", "direcao": "compra", "strike": K1, "premio": premios[0]},
                {"tipo": "put", "direcao": "venda", "strike": K2, "premio": premios[1]},
                {"tipo": "call", "direcao": "venda", "strike": K3, "premio": premios[2]},
                {"tipo": "call", "direcao": "compra", "strike": K4, "premio": premios[3]},
            ],
            "credito_liquido": round(credito, 2),
            "lucro_maximo": round(credito, 2),
            "perda_maxima": round(max(perda_max, 0), 2),
            "breakeven_inferior": round(K2 - credito, 2),
            "breakeven_superior": round(K3 + credito, 2),
            "modo": self.MODO,
        }

    def _estrategia_straddle(self, ativo, S, strikes, premios, T, r, sigma):
        if len(strikes) < 1 or len(premios) < 2:
            return {"erro": "Straddle requer 1 strike e 2 premios (call + put)"}
        K = strikes[0]
        custo = premios[0] + premios[1]
        return {
            "estrategia": "straddle", "ativo": ativo,
            "posicoes": [
                {"tipo": "call", "direcao": "compra", "strike": K, "premio": premios[0]},
                {"tipo": "put", "direcao": "compra", "strike": K, "premio": premios[1]},
            ],
            "custo_total": round(custo, 2),
            "perda_maxima": round(custo, 2),
            "lucro_maximo": "ilimitado (em teoria)",
            "breakeven_superior": round(K + custo, 2),
            "breakeven_inferior": round(K - custo, 2),
            "modo": self.MODO,
        }

    def sugerir_operacao(self, ativo: str, cenario: str = "neutro") -> dict:
        """
        Sugere estrategia de opcoes com base no cenario de mercado.
        cenario: 'alta', 'baixa', 'neutro', 'volatil'.
        NUNCA executa trades.
        """
        if not self._verificar_modo():
            return {}

        mapa_cenario = {
            "alta": {"estrategia": "bull_call_spread", "strikes": [100, 110], "premios": [5.0, 2.0]},
            "baixa": {"estrategia": "bear_put_spread", "strikes": [90, 100], "premios": [2.0, 5.0]},
            "neutro": {"estrategia": "iron_condor", "strikes": [85, 90, 110, 115], "premios": [0.5, 2.0, 2.0, 0.5]},
            "volatil": {"estrategia": "straddle", "strikes": [100], "premios": [4.0, 3.5]},
        }

        if cenario not in mapa_cenario:
            return {"erro": f"Cenario invalido. Opcoes: {list(mapa_cenario.keys())}"}

        params = mapa_cenario[cenario]
        calculo = self.calcular_estrategia(
            tipo=params["estrategia"],
            ativo=ativo,
            strikes=params["strikes"],
            premios=params["premios"],
        )

        sugestao = {
            "ativo": ativo,
            "cenario": cenario,
            "estrategia_sugerida": params["estrategia"],
            "calculo": calculo,
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "aviso": "SUGESTAO APENAS — nao executa trades automaticamente",
        }

        self.registrar_log(f"Sugestao opcoes: {ativo}", f"{params['estrategia']} ({cenario})")
        return sugestao

    def _salvar_sugestao(self, dados: dict):
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_opcoes, f"sugestao_{agora}.json")
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        self.registrar_log("Sugestao opcoes salva", arquivo)

    def executar(self):
        """Loop principal do Especialista Opcoes."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Especialista Opcoes iniciado", "Analise de estrategias")

        if not self._verificar_modo():
            self.atualizar_status("bloqueado")
            return

        # Gerar sugestoes para cada cenario com ativo de referencia
        ativos_ref = ["PETR4", "VALE3"]
        cenarios = ["alta", "baixa", "neutro", "volatil"]
        resultado = {}

        for ativo in ativos_ref:
            resultado[ativo] = {}
            for cenario in cenarios:
                sugestao = self.sugerir_operacao(ativo, cenario)
                resultado[ativo][cenario] = sugestao

        # Calcular gregas de exemplo
        gregas_exemplo = self.calcular_gregas(S=38.50, K=40.00, T=30/365, r=0.1075, sigma=0.30, tipo="call")
        resultado["gregas_exemplo"] = {
            "ativo": "PETR4", "strike": 40.00, "tipo": "call",
            "preco_bs": self.preco_black_scholes(38.50, 40.00, 30/365, 0.1075, 0.30, "call"),
            "gregas": gregas_exemplo,
        }

        self._salvar_sugestao(resultado)
        self.publicar_resultado("Analise de Opcoes Completa", resultado)

        # Notificar CFO
        self.enviar_mensagem(
            destinatario="cfo",
            assunto="Sugestoes de Opcoes Disponiveis",
            conteudo=(
                f"Especialista Opcoes completou analise.\n"
                f"**Ativos:** {', '.join(ativos_ref)}\n"
                f"**Cenarios analisados:** {', '.join(cenarios)}\n"
                f"**Estrategias avaliadas:** {len(cenarios) * len(ativos_ref)}\n\n"
                f"**Modo:** {self.MODO} — nenhum trade executado."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Especialista Opcoes finalizado", f"{len(ativos_ref)} ativos, {len(cenarios)} cenarios")
        return resultado


if __name__ == "__main__":
    agente = EspecialistaOpcoes()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    if resultado:
        for ativo in ["PETR4", "VALE3"]:
            if ativo in resultado:
                print(f"  {ativo}: {len(resultado[ativo])} cenarios analisados")
        if "gregas_exemplo" in resultado:
            g = resultado["gregas_exemplo"]
            print(f"  Gregas (PETR4 C40): delta={g['gregas']['delta']}, theta={g['gregas']['theta']}")
    print("Concluido (modo SUGESTAO).")
