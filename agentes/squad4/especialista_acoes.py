"""
ESPECIALISTA ACOES — Squad 4: Operacoes Financeiras (MODO SUGESTAO)
Analisa acoes B3/NYSE com indicadores fundamentalistas (P/L, DY, ROE).
Monta carteiras sugeridas por perfil de risco. NUNCA executa trades.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, INTELIGENCIA_DIR


class EspecialistaAcoes(BaseAgente):
    """Agente especialista em analise fundamentalista de acoes."""

    MODO = "SUGESTAO"

    PERFIS_RISCO = {
        "conservador": {
            "descricao": "Foco em dividendos e empresas solidas",
            "max_pl": 15,
            "min_dy": 5.0,
            "min_roe": 12,
            "max_alocacao_por_ativo": 0.15,
        },
        "moderado": {
            "descricao": "Equilibrio entre crescimento e valor",
            "max_pl": 25,
            "min_dy": 2.5,
            "min_roe": 10,
            "max_alocacao_por_ativo": 0.20,
        },
        "agressivo": {
            "descricao": "Foco em crescimento e valorizacao",
            "max_pl": 40,
            "min_dy": 0,
            "min_roe": 8,
            "max_alocacao_por_ativo": 0.25,
        },
    }

    # Base de dados simulada de acoes para demonstracao (Fase 1)
    BASE_ACOES = {
        "PETR4": {"nome": "Petrobras PN", "setor": "Petroleo", "preco": 38.50,
                   "pl": 5.2, "dy": 12.3, "roe": 28.5, "pvp": 1.1, "mercado": "B3"},
        "VALE3": {"nome": "Vale ON", "setor": "Mineracao", "preco": 62.00,
                   "pl": 6.8, "dy": 8.5, "roe": 22.0, "pvp": 1.5, "mercado": "B3"},
        "ITUB4": {"nome": "Itau Unibanco PN", "setor": "Bancos", "preco": 32.00,
                   "pl": 8.5, "dy": 5.2, "roe": 19.5, "pvp": 1.8, "mercado": "B3"},
        "WEGE3": {"nome": "WEG ON", "setor": "Industria", "preco": 45.00,
                   "pl": 35.0, "dy": 1.2, "roe": 30.0, "pvp": 10.5, "mercado": "B3"},
        "BBAS3": {"nome": "Banco do Brasil ON", "setor": "Bancos", "preco": 28.00,
                   "pl": 4.8, "dy": 9.0, "roe": 18.0, "pvp": 0.9, "mercado": "B3"},
        "AAPL": {"nome": "Apple Inc", "setor": "Tecnologia", "preco": 185.00,
                  "pl": 30.0, "dy": 0.5, "roe": 160.0, "pvp": 45.0, "mercado": "NYSE"},
        "MSFT": {"nome": "Microsoft Corp", "setor": "Tecnologia", "preco": 420.00,
                  "pl": 35.0, "dy": 0.7, "roe": 38.0, "pvp": 13.0, "mercado": "NYSE"},
        "GOOGL": {"nome": "Alphabet Inc", "setor": "Tecnologia", "preco": 170.00,
                   "pl": 25.0, "dy": 0, "roe": 25.0, "pvp": 6.5, "mercado": "NYSE"},
    }

    def __init__(self):
        super().__init__(
            nome="Especialista Acoes",
            squad="Squad 4 — Operacoes Financeiras",
            papel="Analise fundamentalista de acoes e montagem de carteiras sugeridas",
        )
        self.pasta_acoes = os.path.join(NEXUS_ROOT, "financeiro", "acoes")
        os.makedirs(self.pasta_acoes, exist_ok=True)

    def _verificar_modo(self) -> bool:
        if self.MODO != "SUGESTAO":
            self.registrar_log("BLOQUEIO: tentativa de operar fora do modo SUGESTAO", "NEGADO")
            return False
        return True

    def analisar_acao(self, ticker: str) -> dict:
        """
        Analisa uma acao com indicadores fundamentalistas.
        Retorna dict com analise completa.
        """
        if not self._verificar_modo():
            return {}

        ticker = ticker.upper()
        if ticker not in self.BASE_ACOES:
            return {"erro": f"Ticker {ticker} nao encontrado na base. Disponiveis: {list(self.BASE_ACOES.keys())}"}

        dados = self.BASE_ACOES[ticker]

        # Classificacao por indicador
        score = 0
        notas = []

        # P/L (menor = melhor, ate certo ponto)
        if dados["pl"] <= 10:
            score += 3
            notas.append(f"P/L atrativo ({dados['pl']})")
        elif dados["pl"] <= 20:
            score += 2
            notas.append(f"P/L razoavel ({dados['pl']})")
        elif dados["pl"] <= 35:
            score += 1
            notas.append(f"P/L elevado ({dados['pl']}) — precificado para crescimento")
        else:
            notas.append(f"P/L muito alto ({dados['pl']}) — risco de sobrevalorizacao")

        # Dividend Yield
        if dados["dy"] >= 6:
            score += 3
            notas.append(f"Dividend yield excelente ({dados['dy']}%)")
        elif dados["dy"] >= 3:
            score += 2
            notas.append(f"Dividend yield bom ({dados['dy']}%)")
        elif dados["dy"] >= 1:
            score += 1
            notas.append(f"Dividend yield baixo ({dados['dy']}%)")
        else:
            notas.append("Sem dividendos relevantes")

        # ROE
        if dados["roe"] >= 20:
            score += 3
            notas.append(f"ROE excelente ({dados['roe']}%) — alta rentabilidade")
        elif dados["roe"] >= 12:
            score += 2
            notas.append(f"ROE bom ({dados['roe']}%)")
        else:
            score += 1
            notas.append(f"ROE moderado ({dados['roe']}%)")

        # P/VP
        if dados["pvp"] <= 1.0:
            score += 2
            notas.append(f"P/VP abaixo de 1 ({dados['pvp']}) — possivel desconto")
        elif dados["pvp"] <= 2.0:
            score += 1
            notas.append(f"P/VP razoavel ({dados['pvp']})")

        max_score = 11
        pct_score = round((score / max_score) * 100, 1)

        if pct_score >= 70:
            recomendacao = "COMPRA"
        elif pct_score >= 40:
            recomendacao = "MANTER"
        else:
            recomendacao = "CAUTELA"

        analise = {
            "ticker": ticker,
            "nome": dados["nome"],
            "setor": dados["setor"],
            "mercado": dados["mercado"],
            "preco_atual": dados["preco"],
            "indicadores": {
                "pl": dados["pl"],
                "dividend_yield": dados["dy"],
                "roe": dados["roe"],
                "pvp": dados["pvp"],
            },
            "score": score,
            "score_max": max_score,
            "score_pct": pct_score,
            "recomendacao": recomendacao,
            "notas": notas,
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "aviso": "SUGESTAO APENAS — nao executa trades automaticamente",
        }

        self.registrar_log(f"Analise de acao: {ticker}", f"{recomendacao} (score {pct_score}%)")
        return analise

    def montar_carteira_sugerida(self, perfil_risco: str = "moderado") -> dict:
        """
        Monta sugestao de carteira com base no perfil de risco.
        NUNCA executa compras — apenas sugere alocacao.
        """
        if not self._verificar_modo():
            return {}

        if perfil_risco not in self.PERFIS_RISCO:
            return {"erro": f"Perfil invalido. Disponiveis: {list(self.PERFIS_RISCO.keys())}"}

        perfil = self.PERFIS_RISCO[perfil_risco]

        # Filtrar acoes que atendem os criterios do perfil
        candidatos = []
        for ticker, dados in self.BASE_ACOES.items():
            if dados["pl"] <= perfil["max_pl"] and dados["dy"] >= perfil["min_dy"] and dados["roe"] >= perfil["min_roe"]:
                analise = self.analisar_acao(ticker)
                if analise and "score_pct" in analise:
                    candidatos.append(analise)

        # Ordenar por score
        candidatos.sort(key=lambda x: x["score_pct"], reverse=True)

        # Distribuir pesos (top candidatos recebem mais peso)
        max_ativos = min(len(candidatos), 8)
        selecionados = candidatos[:max_ativos]

        if not selecionados:
            return {
                "perfil": perfil_risco,
                "mensagem": "Nenhuma acao atende os criterios do perfil com os dados atuais",
                "modo": self.MODO,
            }

        total_score = sum(a["score_pct"] for a in selecionados)
        carteira = []
        for acao in selecionados:
            peso_bruto = acao["score_pct"] / total_score if total_score > 0 else 1 / len(selecionados)
            peso = min(peso_bruto, perfil["max_alocacao_por_ativo"])
            carteira.append({
                "ticker": acao["ticker"],
                "nome": acao["nome"],
                "setor": acao["setor"],
                "peso_pct": round(peso * 100, 1),
                "recomendacao": acao["recomendacao"],
                "score": acao["score_pct"],
            })

        # Normalizar pesos para 100%
        soma_pesos = sum(a["peso_pct"] for a in carteira)
        if soma_pesos > 0:
            for a in carteira:
                a["peso_pct"] = round((a["peso_pct"] / soma_pesos) * 100, 1)

        resultado = {
            "perfil_risco": perfil_risco,
            "descricao_perfil": perfil["descricao"],
            "num_ativos": len(carteira),
            "composicao": carteira,
            "setores": list({a["setor"] for a in carteira}),
            "timestamp": datetime.now().isoformat(),
            "modo": self.MODO,
            "aviso": "SUGESTAO APENAS — nao executa compras automaticamente",
        }

        self.registrar_log(
            f"Carteira sugerida: {perfil_risco}",
            f"{len(carteira)} ativos selecionados",
        )
        return resultado

    def _salvar_analise(self, dados: dict, prefixo: str = "analise"):
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_acoes, f"{prefixo}_{agora}.json")
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        self.registrar_log(f"Analise acoes salva ({prefixo})", arquivo)

    def executar(self):
        """Loop principal do Especialista Acoes."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Especialista Acoes iniciado", "Analise fundamentalista completa")

        if not self._verificar_modo():
            self.atualizar_status("bloqueado")
            return

        # Analisar todos os ativos da base
        analises = {}
        for ticker in self.BASE_ACOES:
            analises[ticker] = self.analisar_acao(ticker)
        self._salvar_analise(analises, "analise_individual")

        # Montar carteiras para cada perfil
        carteiras = {}
        for perfil in self.PERFIS_RISCO:
            carteiras[perfil] = self.montar_carteira_sugerida(perfil)
        self._salvar_analise(carteiras, "carteiras_sugeridas")

        # Publicar resultado consolidado
        resultado = {"analises": analises, "carteiras": carteiras}
        self.publicar_resultado("Analise Fundamentalista Completa", resultado)

        # Notificar CFO
        compras = [t for t, a in analises.items() if a.get("recomendacao") == "COMPRA"]
        self.enviar_mensagem(
            destinatario="cfo",
            assunto="Analise de Acoes Disponivel",
            conteudo=(
                f"Especialista Acoes completou analise.\n"
                f"**Ativos analisados:** {len(analises)}\n"
                f"**Recomendacao COMPRA:** {', '.join(compras) if compras else 'nenhum'}\n"
                f"**Carteiras montadas:** {len(carteiras)} perfis\n\n"
                f"**Modo:** {self.MODO} — nenhuma compra executada."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Especialista Acoes finalizado", f"{len(analises)} acoes analisadas")
        return resultado


if __name__ == "__main__":
    agente = EspecialistaAcoes()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    if resultado:
        for ticker, analise in resultado.get("analises", {}).items():
            rec = analise.get("recomendacao", "N/A")
            score = analise.get("score_pct", 0)
            print(f"  {ticker}: {rec} (score {score}%)")
    print("Concluido (modo SUGESTAO).")
