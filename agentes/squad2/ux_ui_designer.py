"""
UX/UI DESIGNER — Squad 2: Fábrica de Software
Gera wireframes, design systems e especificações de UI para projetos.
Produz artefatos estruturados que alimentam o Dev Rápido e Dev Premium.
"""

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Design System Templates
# ---------------------------------------------------------------------------

DESIGN_SYSTEMS = {
    "material": {
        "nome": "Material Design 3",
        "framework_css": "MaterialUI / Tailwind",
        "cores": {
            "primary": "#6750A4",
            "secondary": "#958DA5",
            "surface": "#FFFBFE",
            "error": "#B3261E",
            "background": "#FFFBFE",
        },
        "tipografia": {
            "font_family": "Roboto, sans-serif",
            "display_large": "57px/64px",
            "headline_medium": "28px/36px",
            "body_large": "16px/24px",
            "label_medium": "12px/16px",
        },
        "espacamento_base": 8,
        "border_radius": 12,
    },
    "shadcn": {
        "nome": "Shadcn/UI",
        "framework_css": "Tailwind CSS + Radix",
        "cores": {
            "background": "hsl(0, 0%, 100%)",
            "foreground": "hsl(222.2, 84%, 4.9%)",
            "primary": "hsl(222.2, 47.4%, 11.2%)",
            "secondary": "hsl(210, 40%, 96.1%)",
            "muted": "hsl(210, 40%, 96.1%)",
            "accent": "hsl(210, 40%, 96.1%)",
            "destructive": "hsl(0, 84.2%, 60.2%)",
        },
        "tipografia": {
            "font_family": "Inter, sans-serif",
            "heading": "font-bold tracking-tight",
            "body": "text-sm leading-relaxed",
        },
        "espacamento_base": 4,
        "border_radius": 8,
    },
    "minimal": {
        "nome": "Minimal Clean",
        "framework_css": "Tailwind CSS",
        "cores": {
            "primary": "#000000",
            "secondary": "#666666",
            "background": "#FFFFFF",
            "accent": "#0066FF",
            "error": "#FF3333",
        },
        "tipografia": {
            "font_family": "Inter, system-ui, sans-serif",
            "heading": "32px bold",
            "body": "16px regular",
            "caption": "12px medium",
        },
        "espacamento_base": 4,
        "border_radius": 6,
    },
}

# Templates de wireframe por tipo de produto
WIREFRAME_TEMPLATES = {
    "saas_b2b": {
        "paginas": [
            {"nome": "Landing Page", "secoes": ["hero", "features", "pricing", "testimonials", "cta", "footer"]},
            {"nome": "Dashboard", "secoes": ["sidebar", "header", "kpi_cards", "charts", "table", "actions"]},
            {"nome": "Login/Signup", "secoes": ["form", "social_auth", "forgot_password"]},
            {"nome": "Settings", "secoes": ["profile", "billing", "integrations", "api_keys"]},
        ],
        "componentes_chave": ["data_table", "modal", "toast", "dropdown", "tabs", "breadcrumb"],
    },
    "marketplace": {
        "paginas": [
            {"nome": "Home", "secoes": ["search_bar", "categorias", "destaques", "recentes", "footer"]},
            {"nome": "Listagem", "secoes": ["filtros", "grid_cards", "pagination", "sorting"]},
            {"nome": "Detalhe Produto", "secoes": ["galeria", "info", "preco", "avaliacoes", "relacionados"]},
            {"nome": "Checkout", "secoes": ["resumo", "endereco", "pagamento", "confirmacao"]},
            {"nome": "Perfil Vendedor", "secoes": ["avatar", "bio", "produtos", "avaliacoes"]},
        ],
        "componentes_chave": ["card_produto", "rating", "carousel", "filtro_lateral", "badge"],
    },
    "chatbot_whatsapp": {
        "paginas": [
            {"nome": "Landing Page", "secoes": ["hero_demo", "como_funciona", "planos", "faq", "cta"]},
            {"nome": "Painel Admin", "secoes": ["conversas", "metricas", "fluxos", "configuracoes"]},
            {"nome": "Editor de Fluxo", "secoes": ["canvas", "nodes", "properties", "preview"]},
            {"nome": "Analytics", "secoes": ["overview", "conversas_dia", "satisfacao", "funil"]},
        ],
        "componentes_chave": ["chat_bubble", "flow_node", "metric_card", "timeline"],
    },
    "ebook_ia": {
        "paginas": [
            {"nome": "Landing Page", "secoes": ["hero", "preview_conteudo", "autor_ia", "depoimentos", "comprar"]},
            {"nome": "Reader", "secoes": ["nav_capitulos", "conteudo", "progresso", "notas"]},
            {"nome": "Gerador", "secoes": ["input_tema", "opcoes", "preview", "download"]},
        ],
        "componentes_chave": ["chapter_nav", "progress_bar", "text_reader", "download_btn"],
    },
}


@dataclass
class EspecificacaoUI:
    """Especificação completa de UI para um projeto."""
    projeto: str
    tipo_produto: str
    design_system: str = "shadcn"
    paginas: list = field(default_factory=list)
    componentes: list = field(default_factory=list)
    fluxo_usuario: list = field(default_factory=list)
    responsivo: dict = field(default_factory=lambda: {
        "mobile": "375px",
        "tablet": "768px",
        "desktop": "1280px",
    })
    acessibilidade: dict = field(default_factory=lambda: {
        "contraste_minimo": "4.5:1",
        "aria_labels": True,
        "keyboard_nav": True,
        "screen_reader": True,
    })
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class UXUIDesigner(BaseAgente):
    """Agente de Design UX/UI — gera especificações, wireframes e design systems."""

    def __init__(self):
        super().__init__(
            nome="UX UI Designer",
            squad="Squad 2 — Fábrica de Software",
            papel="Design system, wireframes e especificações de UI",
        )
        self.pasta_designs = os.path.join(NEXUS_ROOT, "projetos_ativos", "designs")
        os.makedirs(self.pasta_designs, exist_ok=True)

    def selecionar_design_system(self, tipo_produto: str) -> str:
        """Seleciona o design system mais adequado para o tipo de produto."""
        mapa = {
            "saas_b2b": "shadcn",
            "marketplace": "material",
            "chatbot_whatsapp": "minimal",
            "ebook_ia": "minimal",
        }
        return mapa.get(tipo_produto, "shadcn")

    def gerar_wireframe(self, projeto: str, tipo_produto: str) -> EspecificacaoUI:
        """Gera especificação de wireframe completa baseada no tipo de produto."""
        template = WIREFRAME_TEMPLATES.get(tipo_produto)
        if not template:
            self.registrar_log(f"Tipo de produto '{tipo_produto}' sem template", "Usando saas_b2b")
            template = WIREFRAME_TEMPLATES["saas_b2b"]
            tipo_produto = "saas_b2b"

        ds_nome = self.selecionar_design_system(tipo_produto)
        ds = DESIGN_SYSTEMS[ds_nome]

        spec = EspecificacaoUI(
            projeto=projeto,
            tipo_produto=tipo_produto,
            design_system=ds_nome,
            paginas=template["paginas"],
            componentes=template["componentes_chave"],
            fluxo_usuario=self._gerar_fluxo_usuario(template["paginas"]),
        )

        self.registrar_log(
            f"Wireframe gerado para '{projeto}'",
            f"{len(spec.paginas)} páginas, design system: {ds_nome}",
        )
        return spec

    def _gerar_fluxo_usuario(self, paginas: list[dict]) -> list[dict]:
        """Gera fluxo de navegação do usuário baseado nas páginas."""
        fluxo = []
        nomes = [p["nome"] for p in paginas]
        for i, nome in enumerate(nomes):
            step = {
                "step": i + 1,
                "pagina": nome,
                "acao_usuario": f"Navega para {nome}",
                "proximas": [nomes[i + 1]] if i + 1 < len(nomes) else ["Home"],
            }
            fluxo.append(step)
        return fluxo

    def gerar_design_system_doc(self, ds_nome: str) -> str:
        """Gera documentação markdown do design system."""
        ds = DESIGN_SYSTEMS.get(ds_nome, DESIGN_SYSTEMS["shadcn"])
        doc = (
            f"# Design System: {ds['nome']}\n\n"
            f"**Framework CSS:** {ds['framework_css']}\n"
            f"**Espaçamento base:** {ds['espacamento_base']}px\n"
            f"**Border radius:** {ds['border_radius']}px\n\n"
            f"## Cores\n"
        )
        for nome, valor in ds["cores"].items():
            doc += f"- **{nome}:** `{valor}`\n"
        doc += "\n## Tipografia\n"
        for nome, valor in ds["tipografia"].items():
            doc += f"- **{nome}:** `{valor}`\n"
        return doc

    def salvar_especificacao(self, spec: EspecificacaoUI):
        """Salva especificação de UI em JSON e Markdown."""
        nome_base = spec.projeto.lower().replace(" ", "_")
        pasta_projeto = os.path.join(self.pasta_designs, nome_base)
        os.makedirs(pasta_projeto, exist_ok=True)

        # JSON completo
        with open(os.path.join(pasta_projeto, "spec_ui.json"), "w", encoding="utf-8") as f:
            json.dump(spec.to_dict(), f, ensure_ascii=False, indent=2)

        # Markdown legível
        md = (
            f"# Especificação UI — {spec.projeto}\n"
            f"**Tipo:** {spec.tipo_produto}\n"
            f"**Design System:** {spec.design_system}\n"
            f"**Data:** {spec.data_criacao}\n\n"
            f"## Páginas\n"
        )
        for p in spec.paginas:
            md += f"\n### {p['nome']}\n"
            for secao in p["secoes"]:
                md += f"- [ ] {secao}\n"

        md += "\n## Componentes Reutilizáveis\n"
        for comp in spec.componentes:
            md += f"- `<{comp} />`\n"

        md += "\n## Fluxo do Usuário\n"
        for step in spec.fluxo_usuario:
            md += f"{step['step']}. **{step['pagina']}** → {', '.join(step['proximas'])}\n"

        md += f"\n## Responsividade\n"
        for device, bp in spec.responsivo.items():
            md += f"- {device}: {bp}\n"

        md += "\n" + self.gerar_design_system_doc(spec.design_system)

        with open(os.path.join(pasta_projeto, "spec_ui.md"), "w", encoding="utf-8") as f:
            f.write(md)

        self.registrar_log(f"Especificação salva em {pasta_projeto}")

    def executar(self):
        """Loop principal: lê projetos aprovados pelo CEO e gera specs de UI."""
        self.atualizar_status("em_execucao")
        self.registrar_log("UX/UI Designer iniciado")

        # 1. Ler projetos aprovados
        pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        projetos_processados = 0

        if os.path.exists(pasta_projetos):
            for arquivo in os.listdir(pasta_projetos):
                if not arquivo.endswith(".json"):
                    continue
                caminho = os.path.join(pasta_projetos, arquivo)
                with open(caminho, "r", encoding="utf-8") as f:
                    projeto = json.load(f)

                nome = projeto.get("nome", "")
                if not nome:
                    continue

                # Inferir tipo de produto pela keyword
                tipo = self._inferir_tipo_produto(nome, projeto.get("descricao", ""))
                spec = self.gerar_wireframe(nome, tipo)
                self.salvar_especificacao(spec)

                # Notificar Arquiteto de Dados
                self.enviar_mensagem(
                    destinatario="arquiteto_dados",
                    assunto=f"Spec UI pronta: {nome}",
                    conteudo=(
                        f"Wireframe e design system prontos para '{nome}'.\n"
                        f"**Tipo:** {tipo}\n"
                        f"**Páginas:** {len(spec.paginas)}\n"
                        f"**Design System:** {spec.design_system}\n"
                        f"Arquivos em: projetos_ativos/designs/{nome.lower().replace(' ', '_')}/\n"
                    ),
                )
                projetos_processados += 1

        # 2. Ler mensagens de tarefas do CEO
        mensagens = self.ler_mensagens()
        for msg in mensagens:
            if "TAREFA:" in msg.get("conteudo", ""):
                self.registrar_log("Tarefa recebida do CEO Agente", msg["arquivo"])

        self.atualizar_status("concluido")
        self.registrar_log("UX/UI Designer finalizado", f"{projetos_processados} projetos processados")
        return projetos_processados

    def _inferir_tipo_produto(self, nome: str, descricao: str) -> str:
        """Infere o tipo de produto para selecionar template adequado."""
        texto = (nome + " " + descricao).lower()
        if any(kw in texto for kw in ["whatsapp", "zap", "chat", "bot"]):
            return "chatbot_whatsapp"
        if any(kw in texto for kw in ["marketplace", "loja", "empreitaja", "preço"]):
            return "marketplace"
        if any(kw in texto for kw in ["ebook", "livro", "influencer", "conteudo"]):
            return "ebook_ia"
        return "saas_b2b"


# --- Execução direta ---
if __name__ == "__main__":
    agente = UXUIDesigner()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    print(f"Concluído: {resultado} projetos com spec UI gerada.")
