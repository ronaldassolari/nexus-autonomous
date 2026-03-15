"""
COPYWRITER — Squad 3: Marketing & Vendas
Gera copy para landing pages, email marketing e anúncios.
Produz textos persuasivos para diferentes canais e formatos.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


class Copywriter(BaseAgente):
    """Agente especializado em produzir textos de marketing e vendas."""

    TEMPLATES_LANDING_PAGE = {
        "hero": {
            "titulo": "Transforme {problema} em {solucao} — sem {objecao}",
            "subtitulo": "Mais de {numero} pessoas já usam {produto} para {beneficio_principal}",
            "cta": "Comece Agora — Grátis por {trial_dias} Dias",
        },
        "features": {
            "titulo_secao": "Tudo que você precisa em um só lugar",
            "formato": [
                {"icone": "🚀", "titulo": "{feature_1}", "desc": "{desc_feature_1}"},
                {"icone": "🔒", "titulo": "{feature_2}", "desc": "{desc_feature_2}"},
                {"icone": "⚡", "titulo": "{feature_3}", "desc": "{desc_feature_3}"},
            ],
        },
        "pricing": {
            "titulo_secao": "Escolha o plano ideal para você",
            "planos": [
                {"nome": "Starter", "preco": "R$ 0", "features": ["Feature básica 1", "Feature básica 2"]},
                {"nome": "Pro", "preco": "R$ {preco_pro}/mês", "features": ["Tudo do Starter", "Feature avançada 1"]},
                {"nome": "Business", "preco": "R$ {preco_business}/mês", "features": ["Tudo do Pro", "Suporte prioritário"]},
            ],
        },
        "cta_final": {
            "titulo": "Pronto para {acao_principal}?",
            "subtitulo": "Junte-se a {numero} profissionais que já transformaram seus resultados",
            "botao": "Começar Agora",
        },
    }

    TEMPLATES_EMAIL = {
        "boas_vindas": {
            "assunto": "Bem-vindo ao {produto} — seu primeiro passo para {beneficio}",
            "corpo": (
                "Olá {nome},\n\n"
                "Que bom ter você com a gente!\n\n"
                "Você acabou de dar o primeiro passo para {beneficio_principal}.\n\n"
                "Aqui está o que você pode fazer agora:\n"
                "1. {acao_1}\n"
                "2. {acao_2}\n"
                "3. {acao_3}\n\n"
                "Se tiver qualquer dúvida, responda este email.\n\n"
                "Abraço,\nEquipe {produto}"
            ),
        },
        "lancamento": {
            "assunto": "🔥 {produto} está no ar — oferta especial por {prazo}",
            "corpo": (
                "Olá {nome},\n\n"
                "Depois de meses de desenvolvimento, {produto} está oficialmente disponível.\n\n"
                "**O que é:** {descricao_curta}\n"
                "**Para quem:** {publico_alvo}\n"
                "**Oferta de lançamento:** {oferta}\n\n"
                "👉 {link_cta}\n\n"
                "Essa oferta expira em {prazo}.\n\n"
                "Abraço,\nEquipe {produto}"
            ),
        },
        "carrinho_abandonado": {
            "assunto": "Você esqueceu algo... {produto} ainda está esperando por você",
            "corpo": (
                "Olá {nome},\n\n"
                "Percebemos que você começou o cadastro em {produto} mas não finalizou.\n\n"
                "Sabemos que decisões levam tempo — por isso preparamos um incentivo:\n"
                "**{desconto}** usando o cupom **{cupom}**.\n\n"
                "👉 {link_cta}\n\n"
                "Válido por {prazo}.\n\n"
                "Abraço,\nEquipe {produto}"
            ),
        },
    }

    TEMPLATES_ADS = {
        "facebook": {
            "formato": "imagem_ou_video",
            "titulo": "{beneficio_principal} em {tempo}",
            "texto_primario": "Cansado de {dor}? {produto} resolve isso para você.\n\n✅ {beneficio_1}\n✅ {beneficio_2}\n✅ {beneficio_3}\n\n👉 {cta}",
            "descricao_link": "{produto} — {proposta_valor_curta}",
        },
        "google": {
            "formato": "search_ad",
            "titulo_1": "{produto} — {beneficio_principal}",
            "titulo_2": "{oferta} | Comece Hoje",
            "descricao": "{produto} ajuda {publico_alvo} a {beneficio}. {prova_social}. Teste grátis.",
        },
        "tiktok": {
            "formato": "video_curto",
            "hook": "POV: você descobriu {produto} e {resultado_transformador}",
            "roteiro": "Hook (0-3s): {hook}\nProblema (3-8s): {dor_do_publico}\nSolução (8-15s): {demonstracao_produto}\nCTA (15-18s): {cta}",
        },
    }

    def __init__(self):
        super().__init__(
            nome="Copywriter",
            squad="Squad 3 — Marketing & Vendas",
            papel="Gera copy para landing pages, emails e anúncios",
        )
        self.pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        os.makedirs(self.pasta_projetos, exist_ok=True)

    def gerar_copy(self, projeto: dict, tipo: str) -> dict:
        """
        Gera copy baseado no tipo solicitado.
        Tipos: landing_page, email_boas_vindas, email_lancamento, ad_facebook, ad_google, ad_tiktok
        """
        nome_projeto = projeto.get("nome", "Produto")
        descricao = projeto.get("descricao", "")
        publico = projeto.get("publico_alvo", "profissionais")
        beneficio = projeto.get("beneficio_principal", "resultados melhores")

        if tipo == "landing_page":
            return self.gerar_landing_page(projeto)

        if tipo.startswith("email_"):
            subtipo = tipo.replace("email_", "")
            template = self.TEMPLATES_EMAIL.get(subtipo, self.TEMPLATES_EMAIL["lancamento"])
            return {
                "tipo": f"email_{subtipo}",
                "projeto": nome_projeto,
                "assunto": template["assunto"].format(
                    produto=nome_projeto, beneficio=beneficio, prazo="48h", nome="{nome}"
                ),
                "corpo": template["corpo"].format(
                    produto=nome_projeto, nome="{nome}", beneficio_principal=beneficio,
                    publico_alvo=publico, descricao_curta=descricao,
                    acao_1="Acesse o painel", acao_2="Configure seu perfil",
                    acao_3="Explore as funcionalidades", oferta="30% OFF",
                    link_cta=f"https://link.do/{nome_projeto.lower().replace(' ', '-')}",
                    prazo="48h", desconto="20% OFF", cupom="VOLTA20",
                ),
                "gerado_em": datetime.now().isoformat(),
            }

        if tipo.startswith("ad_"):
            canal = tipo.replace("ad_", "")
            template = self.TEMPLATES_ADS.get(canal)
            if not template:
                return {"erro": f"Canal de ads não suportado: {canal}"}
            return {
                "tipo": f"ad_{canal}",
                "projeto": nome_projeto,
                "template": template,
                "variaveis_preenchidas": {
                    "produto": nome_projeto,
                    "beneficio_principal": beneficio,
                    "publico_alvo": publico,
                    "dor": projeto.get("dor_principal", "perder tempo com tarefas manuais"),
                },
                "gerado_em": datetime.now().isoformat(),
            }

        return {"erro": f"Tipo de copy não suportado: {tipo}"}

    def gerar_landing_page(self, projeto: dict) -> dict:
        """Gera estrutura completa de landing page para um projeto."""
        nome = projeto.get("nome", "Produto")
        beneficio = projeto.get("beneficio_principal", "resultados incríveis")
        problema = projeto.get("dor_principal", "processos manuais")

        pagina = {
            "projeto": nome,
            "tipo": "landing_page",
            "secoes": {
                "hero": {
                    "titulo": f"Transforme {problema} em {beneficio} — sem complicação",
                    "subtitulo": f"Descubra como {nome} está ajudando profissionais a alcançar {beneficio}",
                    "cta": "Comece Agora — Grátis por 7 Dias",
                },
                "features": {
                    "titulo": "Tudo que você precisa em um só lugar",
                    "items": projeto.get("features", [
                        {"titulo": "Automação inteligente", "desc": "Economize horas por semana"},
                        {"titulo": "Dashboard completo", "desc": "Tudo visível em tempo real"},
                        {"titulo": "Suporte dedicado", "desc": "Equipe pronta para ajudar"},
                    ]),
                },
                "pricing": self.TEMPLATES_LANDING_PAGE["pricing"],
                "cta_final": {
                    "titulo": f"Pronto para transformar seus resultados com {nome}?",
                    "subtitulo": "Junte-se a milhares de profissionais satisfeitos",
                    "botao": "Começar Agora",
                },
            },
            "gerado_em": datetime.now().isoformat(),
        }

        self.registrar_log(f"Landing page gerada para {nome}")
        return pagina

    def executar(self):
        """Loop principal do Copywriter."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Copywriter iniciado", "Gerando copy para projetos ativos")

        # Buscar projetos ativos
        copies_geradas = []
        for arquivo in os.listdir(self.pasta_projetos):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(self.pasta_projetos, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                projeto = json.load(f)

            # Gerar copy para cada canal
            for tipo in ["landing_page", "email_lancamento", "ad_facebook", "ad_google", "ad_tiktok"]:
                copy = self.gerar_copy(projeto, tipo)
                copies_geradas.append(copy)

        # Publicar resultado consolidado
        resumo = {
            "total_copies": len(copies_geradas),
            "tipos": list({c.get("tipo", "desconhecido") for c in copies_geradas}),
            "gerado_em": datetime.now().isoformat(),
        }
        self.publicar_resultado("Copy gerada para projetos ativos", resumo)

        # Notificar Gestor de Tráfego
        self.enviar_mensagem(
            destinatario="gestor_trafego",
            assunto="Copy pronta para campanhas",
            conteudo=(
                f"Copywriter finalizou geração de copies.\n"
                f"**{len(copies_geradas)} peças** criadas para os projetos ativos.\n\n"
                f"Tipos: {', '.join(resumo['tipos'])}\n\n"
                f"Ação necessária: configurar campanhas de tráfego pago."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Copywriter finalizado", f"{len(copies_geradas)} copies geradas")
        return copies_geradas


# --- Execução direta ---
if __name__ == "__main__":
    agente = Copywriter()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} copies geradas.")
