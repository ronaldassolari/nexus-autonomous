"""
ESPECIALISTA MARKETPLACE — Squad 3: Marketing & Vendas
Cria e otimiza listings para Hotmart, Kiwify e App Store.
Aplica técnicas de SEO para maximizar visibilidade nos marketplaces.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


class EspecialistaMarketplace(BaseAgente):
    """Agente especializado em criação e otimização de listings em marketplaces."""

    TEMPLATES_MARKETPLACE = {
        "hotmart": {
            "plataforma": "Hotmart",
            "campos_obrigatorios": ["titulo", "descricao", "preco", "categoria", "subcategoria"],
            "limites": {"titulo_max": 80, "descricao_max": 5000, "tags_max": 10},
            "categorias": [
                "Negócios e Carreira", "Marketing Digital", "Desenvolvimento Pessoal",
                "Finanças e Investimentos", "Tecnologia", "Saúde e Esportes",
                "Educação", "Design e Programação",
            ],
            "formatos": ["curso_online", "ebook", "mentoria", "comunidade", "template"],
            "comissao_padrao": 0.10,
        },
        "kiwify": {
            "plataforma": "Kiwify",
            "campos_obrigatorios": ["titulo", "descricao", "preco", "categoria"],
            "limites": {"titulo_max": 100, "descricao_max": 8000, "tags_max": 15},
            "categorias": [
                "Marketing Digital", "Negócios Online", "Desenvolvimento Pessoal",
                "Finanças", "Tecnologia", "Saúde", "Educação",
            ],
            "formatos": ["curso", "ebook", "mentoria", "assinatura", "software"],
            "comissao_padrao": 0.08,
        },
        "app_store": {
            "plataforma": "App Store / Google Play",
            "campos_obrigatorios": ["titulo", "subtitulo", "descricao", "preco", "categoria", "keywords"],
            "limites": {"titulo_max": 30, "subtitulo_max": 30, "descricao_max": 4000, "keywords_max": 100},
            "categorias": [
                "Produtividade", "Negócios", "Finanças", "Educação",
                "Utilitários", "Estilo de Vida", "Saúde e Fitness",
            ],
            "modelos_monetizacao": ["freemium", "assinatura", "compra_unica", "in_app_purchase"],
            "comissao_padrao": 0.15,
        },
    }

    PALAVRAS_PODER_SEO = [
        "definitivo", "completo", "passo a passo", "comprovado", "garantido",
        "exclusivo", "profissional", "avançado", "rápido", "fácil",
        "automatizado", "inteligente", "premium", "masterclass", "método",
    ]

    def __init__(self):
        super().__init__(
            nome="Especialista Marketplace",
            squad="Squad 3 — Marketing & Vendas",
            papel="Cria e otimiza listings em Hotmart, Kiwify e App Store",
        )
        self.pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        self.pasta_listings = os.path.join(self.pasta_projetos, "listings")
        os.makedirs(self.pasta_listings, exist_ok=True)

    def criar_listagem(self, projeto: dict, marketplace: str) -> dict:
        """
        Cria listing completo para um marketplace específico.
        Retorna dict com título, descrição, preço, tags e config da plataforma.
        """
        template = self.TEMPLATES_MARKETPLACE.get(marketplace)
        if not template:
            self.registrar_log(f"Marketplace não suportado: {marketplace}", "ERRO")
            return {"erro": f"Marketplace não suportado: {marketplace}"}

        nome_projeto = projeto.get("nome", "Produto")
        descricao = projeto.get("descricao", "")
        preco = projeto.get("preco", 97.0)
        publico = projeto.get("publico_alvo", "profissionais")
        beneficio = projeto.get("beneficio_principal", "resultados melhores")
        categoria = projeto.get("categoria", template["categorias"][0])
        tags = projeto.get("tags", [])

        # Gerar título otimizado por marketplace
        limite_titulo = template["limites"]["titulo_max"]
        titulo = f"{nome_projeto} — {beneficio.capitalize()}"
        if len(titulo) > limite_titulo:
            titulo = titulo[:limite_titulo - 3] + "..."

        # Gerar descrição estruturada
        desc_completa = self._gerar_descricao(projeto, marketplace)

        # Gerar tags se não fornecidas
        if not tags:
            tags = self._gerar_tags(projeto, template["limites"].get("tags_max", 10))

        listagem = {
            "marketplace": marketplace,
            "plataforma": template["plataforma"],
            "projeto": nome_projeto,
            "titulo": titulo,
            "descricao": desc_completa,
            "preco": preco,
            "categoria": categoria,
            "tags": tags,
            "formato": projeto.get("formato", template.get("formatos", ["curso_online"])[0]),
            "comissao_afiliado": projeto.get("comissao", template["comissao_padrao"]),
            "status": "rascunho",
            "criado_em": datetime.now().isoformat(),
        }

        if marketplace == "app_store":
            listagem["subtitulo"] = beneficio[:30]
            listagem["keywords"] = ", ".join(tags[:10])
            listagem["modelo_monetizacao"] = projeto.get("monetizacao", "freemium")

        self.registrar_log(
            f"Listing criado para {nome_projeto} em {template['plataforma']}",
            f"Preço: R$ {preco:.2f}",
        )
        return listagem

    def _gerar_descricao(self, projeto: dict, marketplace: str) -> str:
        """Gera descrição otimizada para o marketplace."""
        nome = projeto.get("nome", "Produto")
        beneficio = projeto.get("beneficio_principal", "resultados melhores")
        publico = projeto.get("publico_alvo", "profissionais")
        dor = projeto.get("dor_principal", "processos manuais e demorados")
        features = projeto.get("features", [])

        descricao = (
            f"🎯 {nome} — O método comprovado para {beneficio}\n\n"
            f"Você está cansado de {dor}?\n\n"
            f"{nome} foi criado especialmente para {publico} que querem "
            f"alcançar {beneficio} de forma prática e eficiente.\n\n"
        )

        if features:
            descricao += "✅ O que você vai encontrar:\n"
            for feat in features:
                if isinstance(feat, dict):
                    descricao += f"• {feat.get('titulo', feat.get('nome', ''))}\n"
                else:
                    descricao += f"• {feat}\n"
            descricao += "\n"

        descricao += (
            f"🔒 Garantia de satisfação — teste sem risco.\n\n"
            f"👉 Comece agora e transforme seus resultados com {nome}!"
        )
        return descricao

    def _gerar_tags(self, projeto: dict, max_tags: int) -> list:
        """Gera tags SEO baseadas no projeto."""
        nome = projeto.get("nome", "").lower().split()
        categoria = projeto.get("categoria", "").lower().split()
        beneficio = projeto.get("beneficio_principal", "").lower().split()
        keywords = projeto.get("keywords", [])

        tags = list(keywords)
        for palavra in nome + categoria + beneficio:
            palavra_limpa = palavra.strip("—-.,!?")
            if palavra_limpa and len(palavra_limpa) > 2 and palavra_limpa not in tags:
                tags.append(palavra_limpa)

        return tags[:max_tags]

    def otimizar_listagem(self, listagem: dict) -> dict:
        """
        Analisa uma listagem existente e sugere otimizações SEO.
        Retorna dict com sugestões de melhoria.
        """
        sugestoes = []
        titulo = listagem.get("titulo", "")
        descricao = listagem.get("descricao", "")
        tags = listagem.get("tags", [])

        # Verificar título
        if len(titulo) < 20:
            sugestoes.append({
                "campo": "titulo",
                "tipo": "melhoria",
                "msg": "Título curto demais. Adicione benefício principal ou palavra-chave.",
            })

        # Verificar palavras de poder no título
        tem_poder = any(p in titulo.lower() for p in self.PALAVRAS_PODER_SEO)
        if not tem_poder:
            sugestoes.append({
                "campo": "titulo",
                "tipo": "seo",
                "msg": f"Adicione uma palavra de poder: {', '.join(self.PALAVRAS_PODER_SEO[:5])}",
            })

        # Verificar descrição
        if len(descricao) < 200:
            sugestoes.append({
                "campo": "descricao",
                "tipo": "melhoria",
                "msg": "Descrição curta. Expanda com benefícios, prova social e CTA.",
            })

        # Verificar tags
        if len(tags) < 5:
            sugestoes.append({
                "campo": "tags",
                "tipo": "seo",
                "msg": "Poucas tags. Adicione variações de keywords e termos relacionados.",
            })

        return {
            "listing_original": listagem.get("titulo", ""),
            "marketplace": listagem.get("marketplace", ""),
            "total_sugestoes": len(sugestoes),
            "sugestoes": sugestoes,
            "score_otimizacao": max(0, 10 - len(sugestoes) * 2),
            "analisado_em": datetime.now().isoformat(),
        }

    def _salvar_listagem(self, listagem: dict):
        """Salva listing como JSON."""
        mp = listagem.get("marketplace", "geral")
        projeto = listagem.get("projeto", "produto").lower().replace(" ", "_")
        nome_arquivo = f"{projeto}_{mp}.json"
        caminho = os.path.join(self.pasta_listings, nome_arquivo)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(listagem, f, ensure_ascii=False, indent=2)
        self.registrar_log(f"Listing salvo: {caminho}")
        return caminho

    def executar(self):
        """Loop principal do Especialista Marketplace."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Especialista Marketplace iniciado", "Criando listings para projetos ativos")

        listings_criados = []

        for arquivo in os.listdir(self.pasta_projetos):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(self.pasta_projetos, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                projeto = json.load(f)

            # Criar listing em cada marketplace relevante
            marketplaces = projeto.get("marketplaces", ["hotmart", "kiwify"])
            for mp in marketplaces:
                listagem = self.criar_listagem(projeto, mp)
                if "erro" not in listagem:
                    otimizacao = self.otimizar_listagem(listagem)
                    listagem["otimizacao"] = otimizacao
                    self._salvar_listagem(listagem)
                    listings_criados.append(listagem)

        # Publicar resultado consolidado
        resumo = {
            "total_listings": len(listings_criados),
            "marketplaces": list({l["marketplace"] for l in listings_criados}),
            "gerado_em": datetime.now().isoformat(),
        }
        self.publicar_resultado("Listings criados nos marketplaces", resumo)

        # Notificar Closer
        self.enviar_mensagem(
            destinatario="closer",
            assunto="Listings prontos nos marketplaces",
            conteudo=(
                f"Especialista Marketplace finalizou criação de listings.\n"
                f"**{len(listings_criados)} listings** criados.\n"
                f"Marketplaces: {', '.join(resumo['marketplaces'])}\n\n"
                f"Listings salvos em: {self.pasta_listings}\n\n"
                f"Ação necessária: preparar scripts de vendas e funil WhatsApp."
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Especialista Marketplace finalizado", f"{len(listings_criados)} listings criados")
        return listings_criados


# --- Execução direta ---
if __name__ == "__main__":
    agente = EspecialistaMarketplace()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} listings criados.")
