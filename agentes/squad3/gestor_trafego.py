"""
GESTOR DE TRÁFEGO — Squad 3: Marketing & Vendas
Configura e gerencia campanhas de tráfego pago em múltiplos canais.
Aloca orçamento, calcula ROI estimado e salva configs de campanha.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


class GestorTrafego(BaseAgente):
    """Agente especializado em gestão de tráfego pago e campanhas digitais."""

    TEMPLATES_CAMPANHA = {
        "facebook": {
            "plataforma": "Facebook Ads",
            "objetivo": "conversoes",
            "posicionamentos": ["feed", "stories", "reels", "audience_network"],
            "formatos_criativos": ["imagem_unica", "carrossel", "video_curto"],
            "segmentacao": {
                "idade_min": 25,
                "idade_max": 55,
                "genero": "todos",
                "interesses": [],
                "lookalike": True,
            },
            "lances": {"estrategia": "menor_custo", "limite_cpa": None},
        },
        "google": {
            "plataforma": "Google Ads",
            "tipos_campanha": ["search", "display", "youtube", "performance_max"],
            "config_search": {
                "match_types": ["exact", "phrase", "broad"],
                "extensoes": ["sitelink", "callout", "snippet_estruturado"],
                "negativas": [],
            },
            "lances": {"estrategia": "maximizar_conversoes", "cpa_alvo": None},
        },
        "tiktok": {
            "plataforma": "TikTok Ads",
            "objetivo": "conversoes",
            "formatos": ["in_feed", "top_view", "spark_ads"],
            "segmentacao": {
                "idade_min": 18,
                "idade_max": 45,
                "interesses": [],
                "comportamento": ["video_watchers", "engajados"],
            },
            "lances": {"estrategia": "menor_custo", "limite_cpa": None},
        },
    }

    ALOCACAO_ORCAMENTO = {
        "saas": {"facebook": 0.30, "google": 0.50, "tiktok": 0.20},
        "infoproduto": {"facebook": 0.50, "google": 0.20, "tiktok": 0.30},
        "ecommerce": {"facebook": 0.35, "google": 0.40, "tiktok": 0.25},
        "app": {"facebook": 0.25, "google": 0.45, "tiktok": 0.30},
        "servico": {"facebook": 0.40, "google": 0.45, "tiktok": 0.15},
        "default": {"facebook": 0.35, "google": 0.40, "tiktok": 0.25},
    }

    BENCHMARKS = {
        "facebook": {"ctr_medio": 0.012, "cpc_medio": 2.50, "conv_media": 0.025},
        "google": {"ctr_medio": 0.035, "cpc_medio": 3.80, "conv_media": 0.035},
        "tiktok": {"ctr_medio": 0.018, "cpc_medio": 1.80, "conv_media": 0.015},
    }

    def __init__(self):
        super().__init__(
            nome="Gestor Trafego",
            squad="Squad 3 — Marketing & Vendas",
            papel="Configura campanhas de tráfego pago e aloca orçamento",
        )
        self.pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        self.pasta_campanhas = os.path.join(self.pasta_projetos, "campanhas")
        os.makedirs(self.pasta_campanhas, exist_ok=True)

    def _alocar_orcamento(self, orcamento_total: float, tipo_produto: str) -> dict:
        """Distribui o orçamento entre canais com base no tipo de produto."""
        proporcoes = self.ALOCACAO_ORCAMENTO.get(tipo_produto, self.ALOCACAO_ORCAMENTO["default"])
        return {canal: round(orcamento_total * prop, 2) for canal, prop in proporcoes.items()}

    def criar_campanha(self, projeto: dict, canal: str, orcamento: float) -> dict:
        """
        Cria configuração de campanha para um canal específico.
        Retorna dict com toda a config pronta para implementação.
        """
        nome_projeto = projeto.get("nome", "Produto")
        tipo_produto = projeto.get("tipo", "default")
        publico = projeto.get("publico_alvo", "profissionais 25-55 anos")

        template = self.TEMPLATES_CAMPANHA.get(canal)
        if not template:
            self.registrar_log(f"Canal não suportado: {canal}", "ERRO")
            return {"erro": f"Canal não suportado: {canal}"}

        benchmark = self.BENCHMARKS.get(canal, {})
        impressoes_estimadas = int(orcamento / benchmark.get("cpc_medio", 3.0) / benchmark.get("ctr_medio", 0.02))

        campanha = {
            "nome_campanha": f"{nome_projeto} — {canal.upper()} — {datetime.now().strftime('%Y%m')}",
            "projeto": nome_projeto,
            "canal": canal,
            "plataforma": template["plataforma"],
            "orcamento_diario": round(orcamento / 30, 2),
            "orcamento_mensal": orcamento,
            "config": template,
            "segmentacao_customizada": {
                "publico_alvo": publico,
                "keywords": projeto.get("keywords", []),
                "interesses": projeto.get("interesses", []),
            },
            "estimativas": {
                "impressoes_mes": impressoes_estimadas,
                "cliques_mes": int(impressoes_estimadas * benchmark.get("ctr_medio", 0.02)),
                "conversoes_mes": int(impressoes_estimadas * benchmark.get("ctr_medio", 0.02) * benchmark.get("conv_media", 0.02)),
                "cpc_estimado": benchmark.get("cpc_medio", 3.0),
                "ctr_estimado": benchmark.get("ctr_medio", 0.02),
            },
            "status": "rascunho",
            "criado_em": datetime.now().isoformat(),
        }

        self.registrar_log(
            f"Campanha criada: {campanha['nome_campanha']}",
            f"R$ {orcamento:.2f}/mês em {canal}",
        )
        return campanha

    def calcular_roi_estimado(
        self, impressoes: int, ctr: float, conversao: float, ticket_medio: float
    ) -> dict:
        """
        Calcula ROI estimado com base em métricas de funil.
        impressoes: número de impressões
        ctr: click-through rate (ex: 0.02 = 2%)
        conversao: taxa de conversão (ex: 0.03 = 3%)
        ticket_medio: valor médio de venda em R$
        """
        cliques = int(impressoes * ctr)
        vendas = int(cliques * conversao)
        receita = vendas * ticket_medio

        return {
            "impressoes": impressoes,
            "ctr": f"{ctr * 100:.1f}%",
            "cliques": cliques,
            "taxa_conversao": f"{conversao * 100:.1f}%",
            "vendas_estimadas": vendas,
            "ticket_medio": ticket_medio,
            "receita_estimada": round(receita, 2),
        }

    def _salvar_campanha(self, campanha: dict):
        """Salva configuração de campanha como JSON."""
        nome_arquivo = campanha["nome_campanha"].lower().replace(" ", "_").replace("—", "-")
        nome_arquivo = "".join(c for c in nome_arquivo if c.isalnum() or c in "-_")
        caminho = os.path.join(self.pasta_campanhas, f"{nome_arquivo}.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(campanha, f, ensure_ascii=False, indent=2)
        self.registrar_log(f"Campanha salva: {caminho}")
        return caminho

    def executar(self):
        """Loop principal do Gestor de Tráfego."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Gestor Tráfego iniciado", "Configurando campanhas para projetos ativos")

        campanhas_criadas = []

        for arquivo in os.listdir(self.pasta_projetos):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(self.pasta_projetos, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                projeto = json.load(f)

            nome_projeto = projeto.get("nome", arquivo)
            tipo_produto = projeto.get("tipo", "default")
            orcamento_total = projeto.get("orcamento_marketing", 3000.0)
            ticket_medio = projeto.get("ticket_medio", 97.0)

            # Alocar orçamento entre canais
            alocacao = self._alocar_orcamento(orcamento_total, tipo_produto)

            for canal, orcamento_canal in alocacao.items():
                campanha = self.criar_campanha(projeto, canal, orcamento_canal)
                if "erro" not in campanha:
                    # Calcular ROI estimado
                    est = campanha["estimativas"]
                    roi = self.calcular_roi_estimado(
                        est["impressoes_mes"],
                        est.get("ctr_estimado", 0.02),
                        self.BENCHMARKS.get(canal, {}).get("conv_media", 0.02),
                        ticket_medio,
                    )
                    campanha["roi_estimado"] = roi
                    self._salvar_campanha(campanha)
                    campanhas_criadas.append(campanha)

        # Publicar resultado consolidado
        resumo = {
            "total_campanhas": len(campanhas_criadas),
            "canais": list({c["canal"] for c in campanhas_criadas}),
            "orcamento_total": sum(c["orcamento_mensal"] for c in campanhas_criadas),
            "gerado_em": datetime.now().isoformat(),
        }
        self.publicar_resultado("Campanhas de tráfego configuradas", resumo)

        # Notificar Especialista Marketplace
        self.enviar_mensagem(
            destinatario="especialista_marketplace",
            assunto="Campanhas de tráfego configuradas",
            conteudo=(
                f"Gestor de Tráfego finalizou configuração de campanhas.\n"
                f"**{len(campanhas_criadas)} campanhas** criadas.\n"
                f"Orçamento total alocado: R$ {resumo['orcamento_total']:.2f}\n\n"
                f"Configs salvas em: {self.pasta_campanhas}\n\n"
                f"Ação necessária: configurar listings nos marketplaces."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Gestor Tráfego finalizado", f"{len(campanhas_criadas)} campanhas criadas")
        return campanhas_criadas


# --- Execução direta ---
if __name__ == "__main__":
    agente = GestorTrafego()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} campanhas criadas.")
