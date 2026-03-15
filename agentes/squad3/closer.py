"""
CLOSER — Squad 3: Marketing & Vendas
Gera scripts de vendas, funis de WhatsApp e gerencia pipeline de conversão.
Especializado em abordagem, follow-up, tratamento de objeções e fechamento.
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


class Closer(BaseAgente):
    """Agente especializado em fechamento de vendas e funis de conversão."""

    ETAPAS_FUNIL = ["abordagem", "qualificacao", "followup", "objecao", "fechamento", "pos_venda"]

    TEMPLATES_WHATSAPP = {
        "abordagem": {
            "etapa": "Abordagem Inicial",
            "mensagens": [
                {
                    "tipo": "primeira_mensagem",
                    "texto": (
                        "Olá {nome}! 👋\n\n"
                        "Vi que você se interessou por {produto}.\n\n"
                        "Posso te explicar rapidamente como funciona e como pode te ajudar com {dor_principal}?\n\n"
                        "Leva menos de 2 minutos 😊"
                    ),
                },
                {
                    "tipo": "sem_resposta_24h",
                    "texto": (
                        "Oi {nome}, tudo bem?\n\n"
                        "Sei que o dia a dia é corrido. Só queria garantir que você "
                        "viu minha mensagem sobre {produto}.\n\n"
                        "Se preferir, posso enviar um resumo rápido por aqui mesmo. "
                        "O que acha?"
                    ),
                },
            ],
        },
        "qualificacao": {
            "etapa": "Qualificação",
            "mensagens": [
                {
                    "tipo": "perguntas_qualificacao",
                    "texto": (
                        "Ótimo, {nome}! Para eu te indicar a melhor opção:\n\n"
                        "1️⃣ Qual é seu maior desafio com {area}?\n"
                        "2️⃣ Você já tentou alguma solução antes?\n"
                        "3️⃣ Qual resultado você espera nos próximos 30 dias?\n\n"
                        "Pode responder no seu tempo 🙏"
                    ),
                },
            ],
        },
        "followup": {
            "etapa": "Follow-up",
            "mensagens": [
                {
                    "tipo": "followup_pos_qualificacao",
                    "texto": (
                        "Oi {nome}! 😊\n\n"
                        "Com base no que você me contou, {produto} é ideal para o seu caso.\n\n"
                        "Vou te mostrar como {beneficio_1} e {beneficio_2} "
                        "funcionam na prática:\n\n"
                        "👉 {link_demonstracao}\n\n"
                        "Depois me diz o que achou!"
                    ),
                },
                {
                    "tipo": "followup_7_dias",
                    "texto": (
                        "Oi {nome}, tudo bem?\n\n"
                        "Faz uma semana que conversamos sobre {produto}.\n\n"
                        "Queria te avisar que temos uma condição especial "
                        "essa semana: {oferta_especial}\n\n"
                        "Quer saber mais?"
                    ),
                },
            ],
        },
        "objecao": {
            "etapa": "Tratamento de Objeções",
            "mensagens": [
                {
                    "tipo": "objecao_preco",
                    "texto": (
                        "Entendo perfeitamente, {nome}.\n\n"
                        "Quando olhamos só o valor, pode parecer investimento alto. "
                        "Mas pensa comigo:\n\n"
                        "💰 Se {produto} te ajudar a {beneficio_mensuravel}, "
                        "o retorno já cobre o investimento no primeiro mês.\n\n"
                        "Além disso, temos {facilidade_pagamento}.\n\n"
                        "Faz sentido para você?"
                    ),
                },
                {
                    "tipo": "objecao_tempo",
                    "texto": (
                        "Entendo, {nome}. O tempo é nosso recurso mais valioso.\n\n"
                        "Por isso {produto} foi feito para ser {diferencial_tempo}.\n\n"
                        "A maioria dos nossos clientes investe apenas {tempo_necessario} "
                        "por dia e já vê resultados em {prazo_resultado}.\n\n"
                        "Que tal testar por {trial_dias} dias sem compromisso?"
                    ),
                },
                {
                    "tipo": "objecao_desconfianca",
                    "texto": (
                        "Faz total sentido querer ter certeza, {nome}.\n\n"
                        "Por isso oferecemos:\n"
                        "✅ Garantia de {garantia_dias} dias — devolução total\n"
                        "✅ {numero_clientes} clientes satisfeitos\n"
                        "✅ Suporte direto comigo se precisar\n\n"
                        "Posso te enviar alguns depoimentos de clientes?"
                    ),
                },
            ],
        },
        "fechamento": {
            "etapa": "Fechamento",
            "mensagens": [
                {
                    "tipo": "fechamento_direto",
                    "texto": (
                        "Perfeito, {nome}! 🎯\n\n"
                        "Então para garantir sua vaga com {oferta}:\n\n"
                        "👉 {link_pagamento}\n\n"
                        "Assim que confirmar, você recebe acesso imediato + "
                        "bônus exclusivo de {bonus}.\n\n"
                        "Qualquer dúvida, estou aqui!"
                    ),
                },
                {
                    "tipo": "fechamento_urgencia",
                    "texto": (
                        "{nome}, só passando para avisar:\n\n"
                        "A oferta de {oferta} encerra hoje às {horario_limite}.\n\n"
                        "Depois disso, o valor volta para R$ {preco_cheio}.\n\n"
                        "👉 {link_pagamento}\n\n"
                        "Não quero que você perca essa oportunidade! 🔥"
                    ),
                },
            ],
        },
        "pos_venda": {
            "etapa": "Pós-Venda",
            "mensagens": [
                {
                    "tipo": "boas_vindas_cliente",
                    "texto": (
                        "Parabéns, {nome}! 🎉\n\n"
                        "Sua compra de {produto} foi confirmada!\n\n"
                        "Seus acessos:\n"
                        "📧 Email: verifique sua caixa de entrada\n"
                        "🔗 Plataforma: {link_acesso}\n\n"
                        "Dica: comece por {primeiro_passo}.\n\n"
                        "Estou aqui para qualquer dúvida. Bora! 🚀"
                    ),
                },
            ],
        },
    }

    PIPELINE_STAGES = {
        "lead_frio": {"ordem": 1, "desc": "Lead capturado, sem interação"},
        "lead_morno": {"ordem": 2, "desc": "Respondeu primeira mensagem"},
        "qualificado": {"ordem": 3, "desc": "Respondeu qualificação, perfil confirmado"},
        "em_negociacao": {"ordem": 4, "desc": "Recebeu proposta, em análise"},
        "fechado_ganho": {"ordem": 5, "desc": "Compra confirmada"},
        "fechado_perdido": {"ordem": 6, "desc": "Desistiu ou não qualificado"},
    }

    def __init__(self):
        super().__init__(
            nome="Closer",
            squad="Squad 3 — Marketing & Vendas",
            papel="Gera scripts de vendas e funis de WhatsApp para conversão",
        )
        self.pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        self.pasta_vendas = os.path.join(self.pasta_projetos, "vendas")
        os.makedirs(self.pasta_vendas, exist_ok=True)

    def gerar_script_vendas(self, projeto: dict, etapa: str) -> dict:
        """
        Gera script de vendas para uma etapa específica do funil.
        Etapas: abordagem, qualificacao, followup, objecao, fechamento, pos_venda
        """
        template = self.TEMPLATES_WHATSAPP.get(etapa)
        if not template:
            self.registrar_log(f"Etapa não suportada: {etapa}", "ERRO")
            return {"erro": f"Etapa não suportada: {etapa}"}

        nome_projeto = projeto.get("nome", "Produto")
        beneficio = projeto.get("beneficio_principal", "resultados melhores")
        preco = projeto.get("preco", 97.0)

        # Preencher variáveis do template
        variaveis = {
            "nome": "{nome}",  # Mantém dinâmico para personalização
            "produto": nome_projeto,
            "dor_principal": projeto.get("dor_principal", "processos manuais"),
            "area": projeto.get("area", "sua área"),
            "beneficio_1": beneficio,
            "beneficio_2": projeto.get("beneficio_secundario", "economia de tempo"),
            "beneficio_mensuravel": projeto.get("beneficio_mensuravel", f"economizar 10h por semana"),
            "link_demonstracao": f"https://demo.{nome_projeto.lower().replace(' ', '')}.com",
            "link_pagamento": f"https://pay.{nome_projeto.lower().replace(' ', '')}.com",
            "link_acesso": f"https://app.{nome_projeto.lower().replace(' ', '')}.com",
            "oferta": projeto.get("oferta", f"R$ {preco:.2f}"),
            "oferta_especial": projeto.get("oferta_especial", "30% de desconto"),
            "facilidade_pagamento": projeto.get("facilidade", "parcelamento em até 12x"),
            "diferencial_tempo": projeto.get("diferencial_tempo", "simples e direto"),
            "tempo_necessario": projeto.get("tempo_necessario", "15 minutos"),
            "prazo_resultado": projeto.get("prazo_resultado", "7 dias"),
            "trial_dias": str(projeto.get("trial_dias", 7)),
            "garantia_dias": str(projeto.get("garantia_dias", 30)),
            "numero_clientes": str(projeto.get("numero_clientes", "500+")),
            "preco_cheio": f"{preco * 1.5:.2f}",
            "horario_limite": "23:59",
            "bonus": projeto.get("bonus", "aula exclusiva"),
            "primeiro_passo": projeto.get("primeiro_passo", "o módulo 1"),
        }

        mensagens_preenchidas = []
        for msg in template["mensagens"]:
            texto = msg["texto"]
            for chave, valor in variaveis.items():
                texto = texto.replace(f"{{{chave}}}", valor)
            mensagens_preenchidas.append({
                "tipo": msg["tipo"],
                "texto": texto,
            })

        script = {
            "projeto": nome_projeto,
            "etapa": etapa,
            "nome_etapa": template["etapa"],
            "mensagens": mensagens_preenchidas,
            "pipeline_stage": self._etapa_para_pipeline(etapa),
            "gerado_em": datetime.now().isoformat(),
        }

        self.registrar_log(f"Script gerado: {template['etapa']} para {nome_projeto}")
        return script

    def _etapa_para_pipeline(self, etapa: str) -> str:
        """Mapeia etapa do funil para estágio do pipeline."""
        mapa = {
            "abordagem": "lead_frio",
            "qualificacao": "lead_morno",
            "followup": "qualificado",
            "objecao": "em_negociacao",
            "fechamento": "em_negociacao",
            "pos_venda": "fechado_ganho",
        }
        return mapa.get(etapa, "lead_frio")

    def gerar_funil_whatsapp(self, projeto: dict) -> dict:
        """Gera funil completo de WhatsApp com scripts para todas as etapas."""
        nome_projeto = projeto.get("nome", "Produto")
        funil = {
            "projeto": nome_projeto,
            "tipo": "funil_whatsapp_completo",
            "etapas": {},
            "pipeline": self.PIPELINE_STAGES,
            "gerado_em": datetime.now().isoformat(),
        }

        for etapa in self.ETAPAS_FUNIL:
            script = self.gerar_script_vendas(projeto, etapa)
            if "erro" not in script:
                funil["etapas"][etapa] = script

        funil["total_mensagens"] = sum(
            len(e.get("mensagens", [])) for e in funil["etapas"].values()
        )

        self.registrar_log(
            f"Funil WhatsApp completo gerado para {nome_projeto}",
            f"{funil['total_mensagens']} mensagens em {len(funil['etapas'])} etapas",
        )
        return funil

    def _salvar_funil(self, funil: dict):
        """Salva funil de vendas como JSON."""
        projeto = funil.get("projeto", "produto").lower().replace(" ", "_")
        caminho = os.path.join(self.pasta_vendas, f"funil_{projeto}.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(funil, f, ensure_ascii=False, indent=2)
        self.registrar_log(f"Funil salvo: {caminho}")
        return caminho

    def executar(self):
        """Loop principal do Closer."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Closer iniciado", "Gerando scripts de vendas e funis WhatsApp")

        funis_criados = []

        for arquivo in os.listdir(self.pasta_projetos):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(self.pasta_projetos, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                projeto = json.load(f)

            # Gerar funil completo
            funil = self.gerar_funil_whatsapp(projeto)
            self._salvar_funil(funil)
            funis_criados.append(funil)

        # Publicar resultado consolidado
        total_mensagens = sum(f.get("total_mensagens", 0) for f in funis_criados)
        resumo = {
            "total_funis": len(funis_criados),
            "total_mensagens": total_mensagens,
            "etapas_cobertas": self.ETAPAS_FUNIL,
            "pipeline_stages": list(self.PIPELINE_STAGES.keys()),
            "gerado_em": datetime.now().isoformat(),
        }
        self.publicar_resultado("Funis de vendas WhatsApp criados", resumo)

        # Notificar CEO Agente sobre conclusão do Squad 3
        self.enviar_mensagem(
            destinatario="ceo_agente",
            assunto="Squad 3 — Marketing & Vendas concluído",
            conteudo=(
                f"Closer finalizou geração de funis de vendas.\n"
                f"**{len(funis_criados)} funis** criados com **{total_mensagens} mensagens** totais.\n\n"
                f"Etapas: {', '.join(self.ETAPAS_FUNIL)}\n"
                f"Scripts salvos em: {self.pasta_vendas}\n\n"
                f"Squad 3 (Marketing & Vendas) operacional:\n"
                f"- Copywriter: copy para landing pages, emails e ads\n"
                f"- Gestor Tráfego: campanhas Facebook/Google/TikTok\n"
                f"- Especialista Marketplace: listings Hotmart/Kiwify\n"
                f"- Closer: funis WhatsApp completos"
            ),
        )

        self.atualizar_status("concluido")
        self.registrar_log("Closer finalizado", f"{len(funis_criados)} funis criados")
        return funis_criados


# --- Execução direta ---
if __name__ == "__main__":
    agente = Closer()
    print(f"Iniciando {agente}")
    resultados = agente.executar()
    print(f"Concluído: {len(resultados)} funis de vendas criados.")
