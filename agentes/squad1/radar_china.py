"""
RADAR CHINA — Squad 1: Inteligência & Validação
Busca hypes e tendências emergentes em plataformas chinesas:
Douyin (TikTok CN), WeChat, Bilibili, Xiaohongshu (RED).
"""

import os
import sys
import json
from datetime import datetime
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, INTELIGENCIA_DIR


class RadarChina(BaseAgente):
    """Agente especializado em detectar tendências virais do mercado chinês."""

    PLATAFORMAS = {
        "douyin": {
            "nome": "Douyin (TikTok CN)",
            "descricao": "Vídeos curtos — maior fonte de hypes virais",
            "categorias": ["tech", "ecommerce", "lifestyle", "AI", "gadgets"],
        },
        "bilibili": {
            "nome": "Bilibili",
            "descricao": "Vídeos longos e comunidade tech/geek",
            "categorias": ["AI", "programacao", "hardware", "reviews"],
        },
        "wechat": {
            "nome": "WeChat / Weixin",
            "descricao": "Mini-programs e artigos — ecossistema fechado",
            "categorias": ["mini_programs", "fintech", "saude", "educacao"],
        },
        "xiaohongshu": {
            "nome": "Xiaohongshu (RED)",
            "descricao": "Reviews e lifestyle — forte em consumer trends",
            "categorias": ["beleza", "moda", "tech_consumer", "food"],
        },
    }

    KEYWORDS_RASTREAMENTO = [
        "AI agent", "人工智能", "赚钱", "副业", "SaaS", "电商",
        "自动化", "ChatGPT", "独立开发", "出海", "跨境电商",
        "短视频", "直播带货", "数字人", "AIGC", "大模型",
    ]

    def __init__(self):
        super().__init__(
            nome="Radar China",
            squad="Squad 1 — Inteligência & Validação",
            papel="Busca hypes em Douyin/WeChat/Bilibili/Xiaohongshu",
        )
        self.pasta_tendencias = os.path.join(INTELIGENCIA_DIR, "radar_china")
        os.makedirs(self.pasta_tendencias, exist_ok=True)
        self.tendencias_encontradas = []

    def buscar_tendencias(self, plataforma: str, keywords: list[str] | None = None) -> list[dict]:
        """
        Busca tendências em uma plataforma específica.
        Retorna lista de tendências encontradas.

        NOTA: Na Fase 1, usa fontes públicas acessíveis (RSS, APIs abertas, scraping leve).
        Na Fase 2+, integrar APIs oficiais e proxies para acesso direto.
        """
        if plataforma not in self.PLATAFORMAS:
            self.registrar_log(f"Plataforma desconhecida: {plataforma}", "ERRO")
            return []

        kws = keywords or self.KEYWORDS_RASTREAMENTO
        info_plat = self.PLATAFORMAS[plataforma]
        self.registrar_log(f"Iniciando varredura em {info_plat['nome']}", f"{len(kws)} keywords")

        resultados = []
        for kw in kws:
            resultado = {
                "keyword": kw,
                "plataforma": plataforma,
                "timestamp": datetime.now().isoformat(),
                "fonte": info_plat["nome"],
                "status": "pendente_coleta",
                "urls_busca": self._gerar_urls_busca(plataforma, kw),
            }
            resultados.append(resultado)

        self.registrar_log(
            f"Varredura concluída em {info_plat['nome']}",
            f"{len(resultados)} keywords mapeadas",
        )
        return resultados

    def _gerar_urls_busca(self, plataforma: str, keyword: str) -> dict:
        """Gera URLs de busca auxiliares para coleta manual ou automatizada."""
        kw_encoded = quote_plus(keyword)
        urls = {
            "google_site_search": f"https://www.google.com/search?q=site:{plataforma}.com+{kw_encoded}",
        }
        if plataforma == "bilibili":
            urls["bilibili_search"] = f"https://search.bilibili.com/all?keyword={kw_encoded}"
        elif plataforma == "xiaohongshu":
            urls["google_red"] = f"https://www.google.com/search?q=site:xiaohongshu.com+{kw_encoded}"
        return urls

    def analisar_tendencia(self, tendencia: dict) -> dict:
        """
        Analisa uma tendência e gera score de potencial.
        Critérios: viralidade, monetizabilidade, viabilidade técnica, concorrência.
        """
        score = {
            "keyword": tendencia["keyword"],
            "plataforma": tendencia["plataforma"],
            "viralidade": 0,         # 0-10: quão viral está na China
            "monetizacao": 0,        # 0-10: potencial de gerar receita
            "viabilidade_tecnica": 0, # 0-10: podemos construir isso?
            "concorrencia_br": 0,    # 0-10 invertido: 10 = sem concorrência no BR
            "score_total": 0,
            "status": "aguardando_dados",
            "recomendacao": "",
        }
        # Score será calculado quando dados reais chegarem (Fase 2+)
        # Por agora, estrutura pronta para receber inputs do Validador de Mercado
        return score

    def gerar_relatorio(self, tendencias: list[dict]) -> str:
        """Gera relatório consolidado das tendências encontradas."""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        relatorio = (
            f"# Relatório Radar China\n"
            f"**Data:** {agora}\n"
            f"**Tendências mapeadas:** {len(tendencias)}\n\n"
        )

        por_plataforma = {}
        for t in tendencias:
            plat = t["plataforma"]
            por_plataforma.setdefault(plat, []).append(t)

        for plat, items in por_plataforma.items():
            nome_plat = self.PLATAFORMAS[plat]["nome"]
            relatorio += f"## {nome_plat}\n"
            for item in items:
                relatorio += f"- **{item['keyword']}** — status: {item['status']}\n"
            relatorio += "\n"

        relatorio += (
            "## Próximos Passos\n"
            "1. Coletar dados reais de cada keyword\n"
            "2. Enviar para Validador de Mercado calcular scores\n"
            "3. Top 5 tendências → CEO Agente para decisão\n"
        )
        return relatorio

    def salvar_tendencias(self, tendencias: list[dict]):
        """Salva tendências no diretório de inteligência."""
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_json = os.path.join(self.pasta_tendencias, f"tendencias_{agora}.json")
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(tendencias, f, ensure_ascii=False, indent=2)
        self.registrar_log("Tendências salvas", arquivo_json)

    def executar(self):
        """Loop principal do Radar China."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Radar China iniciado", "Varredura completa em todas as plataformas")

        todas_tendencias = []
        for plataforma in self.PLATAFORMAS:
            resultados = self.buscar_tendencias(plataforma)
            todas_tendencias.extend(resultados)

        # Salvar dados brutos
        self.salvar_tendencias(todas_tendencias)

        # Gerar e publicar relatório
        relatorio = self.gerar_relatorio(todas_tendencias)
        self.publicar_resultado("Varredura Radar China", relatorio)

        # Notificar Validador de Mercado
        self.enviar_mensagem(
            destinatario="validador_mercado",
            assunto="Novas tendências para validação",
            conteudo=(
                f"Radar China completou varredura.\n"
                f"**{len(todas_tendencias)} tendências** mapeadas em {len(self.PLATAFORMAS)} plataformas.\n"
                f"Dados salvos em: {self.pasta_tendencias}\n\n"
                f"Ação necessária: validar demanda no mercado brasileiro."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Radar China finalizado", f"{len(todas_tendencias)} tendências totais")
        return todas_tendencias


# --- Execução direta ---
if __name__ == "__main__":
    agente = RadarChina()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} tendências mapeadas.")
