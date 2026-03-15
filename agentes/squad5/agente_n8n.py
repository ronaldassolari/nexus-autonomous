"""
AGENTE N8N — Squad 5: Automação & Aprendizado
Gerencia webhooks e automações entre os agentes do Nexus Autonomous.
Conecta eventos de um agente/squad a ações em outro via arquivos em comunicacao/.

Templates: radar_to_validador, ceo_to_squad2, qa_to_devops, deploy_to_marketing
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT, COMUNICACAO_DIR

# ---------------------------------------------------------------------------
# Templates de Workflows
# ---------------------------------------------------------------------------
WORKFLOW_TEMPLATES = {
    "radar_to_validador": {
        "trigger": "tendencia_detectada", "destino": "validador_mercado",
        "payload_template": {"acao": "validar_tendencia", "origem": "radar_china", "prioridade": "alta"},
        "descricao": "Radar China detecta tendência → Validador analisa",
    },
    "ceo_to_squad2": {
        "trigger": "projeto_aprovado", "destino": "arquiteto_dados",
        "payload_template": {"acao": "iniciar_projeto", "origem": "ceo_agente", "prioridade": "alta"},
        "descricao": "CEO aprova projeto → Squad 2 inicia desenvolvimento",
    },
    "qa_to_devops": {
        "trigger": "qa_aprovado", "destino": "devops",
        "payload_template": {"acao": "iniciar_deploy", "origem": "qa_seguranca", "prioridade": "media"},
        "descricao": "QA aprovado → DevOps inicia CI/CD",
    },
    "deploy_to_marketing": {
        "trigger": "deploy_concluido", "destino": "copywriter",
        "payload_template": {"acao": "preparar_lancamento", "origem": "devops", "prioridade": "media"},
        "descricao": "Deploy concluído → Squad 3 prepara marketing",
    },
}


# ---------------------------------------------------------------------------
# Agente n8n
# ---------------------------------------------------------------------------
class AgenteN8N(BaseAgente):
    """Agente que gerencia webhooks e automações entre agentes do Nexus."""

    def __init__(self):
        super().__init__(
            nome="Agente N8N",
            squad="Squad 5 — Automação & Aprendizado",
            papel="Gerencia webhooks e automações entre sistemas Nexus",
        )
        self.pasta_webhooks = os.path.join(COMUNICACAO_DIR, "webhooks")
        os.makedirs(self.pasta_webhooks, exist_ok=True)
        self.webhooks = self._carregar_webhooks()
        self._registrar_templates()

    def _carregar_webhooks(self) -> dict:
        """Carrega webhooks registrados do disco."""
        config_path = os.path.join(self.pasta_webhooks, "webhooks_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _salvar_webhooks(self):
        """Persiste configuração de webhooks."""
        config_path = os.path.join(self.pasta_webhooks, "webhooks_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.webhooks, f, ensure_ascii=False, indent=2)

    def _registrar_templates(self):
        """Registra templates padrão se ainda não existirem."""
        alterou = False
        for nome, tmpl in WORKFLOW_TEMPLATES.items():
            if nome not in self.webhooks:
                self.webhooks[nome] = {
                    "trigger": tmpl["trigger"], "destino": tmpl["destino"],
                    "payload_template": tmpl["payload_template"],
                    "descricao": tmpl["descricao"],
                    "criado_em": datetime.now().isoformat(), "disparos": 0,
                }
                alterou = True
        if alterou:
            self._salvar_webhooks()

    def registrar_webhook(self, nome: str, trigger: str, destino: str, payload_template: dict):
        """Registra um novo webhook customizado."""
        self.webhooks[nome] = {
            "trigger": trigger, "destino": destino,
            "payload_template": payload_template,
            "descricao": f"Webhook customizado: {trigger} → {destino}",
            "criado_em": datetime.now().isoformat(), "disparos": 0,
        }
        self._salvar_webhooks()
        self.registrar_log(f"Webhook registrado: {nome}", f"{trigger} → {destino}")

    def disparar_webhook(self, nome: str, dados: dict) -> bool:
        """Dispara um webhook, criando arquivo de mensagem para o destino."""
        if nome not in self.webhooks:
            self.registrar_log(f"Webhook não encontrado: {nome}", "ERRO")
            return False

        wh = self.webhooks[nome]
        payload = dict(wh["payload_template"])
        payload.update({"dados": dados, "webhook": nome, "disparado_em": datetime.now().isoformat()})

        # Criar mensagem no destino via sistema de comunicação do BaseAgente
        conteudo = (
            f"# Webhook Disparado: {nome}\n"
            f"**Trigger:** {wh['trigger']}\n"
            f"**Destino:** {wh['destino']}\n"
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"## Payload\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
        )
        self.enviar_mensagem(wh["destino"], f"Webhook: {nome}", conteudo)

        # Salvar log do disparo
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(self.pasta_webhooks, f"disparo_{nome}_{agora}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        wh["disparos"] += 1
        self._salvar_webhooks()
        self.registrar_log(f"Webhook disparado: {nome}", f"→ {wh['destino']}")
        return True

    def listar_webhooks(self) -> list[dict]:
        """Retorna lista de webhooks registrados com estatísticas."""
        return [
            {"nome": n, "trigger": w["trigger"], "destino": w["destino"],
             "disparos": w["disparos"], "descricao": w["descricao"]}
            for n, w in self.webhooks.items()
        ]

    def verificar_gatilhos(self) -> list[str]:
        """Escaneia comunicacao/gatilhos/ por eventos que correspondam a triggers."""
        disparados = []
        trigger_map = {}
        for nome, wh in self.webhooks.items():
            trigger_map.setdefault(wh["trigger"], []).append(nome)

        pasta_gatilhos = os.path.join(COMUNICACAO_DIR, "gatilhos")
        if not os.path.exists(pasta_gatilhos):
            os.makedirs(pasta_gatilhos, exist_ok=True)
            return disparados

        for arquivo in sorted(os.listdir(pasta_gatilhos)):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(pasta_gatilhos, arquivo)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    evento = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            trigger_nome = evento.get("trigger", "")
            if trigger_nome in trigger_map:
                dados = evento.get("dados", {})
                for wh_nome in trigger_map[trigger_nome]:
                    self.disparar_webhook(wh_nome, dados)
                    disparados.append(wh_nome)

            # Mover arquivo processado
            processados = os.path.join(pasta_gatilhos, "processados")
            os.makedirs(processados, exist_ok=True)
            os.rename(caminho, os.path.join(processados, arquivo))

        return disparados

    def executar(self):
        """Loop principal: escaneia gatilhos e dispara webhooks correspondentes."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Agente N8N iniciado", "Verificando gatilhos e webhooks")

        disparados = self.verificar_gatilhos()

        # Gerar relatório
        webhooks_info = self.listar_webhooks()
        relatorio = (
            f"# Relatório Agente N8N\n"
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Webhooks registrados:** {len(webhooks_info)}\n"
            f"**Disparados nesta execução:** {len(disparados)}\n\n"
            f"## Webhooks Ativos\n"
        )
        for wh in webhooks_info:
            relatorio += f"- **{wh['nome']}**: {wh['trigger']} → {wh['destino']} ({wh['disparos']} disparos)\n"
        if disparados:
            relatorio += "\n## Disparados Agora\n"
            for nome in disparados:
                relatorio += f"- {nome}\n"

        self.publicar_resultado("Execução Agente N8N", relatorio)
        self.atualizar_status("concluido")
        self.registrar_log("Agente N8N finalizado", f"{len(disparados)} webhooks disparados")
        return disparados


# --- Execução direta ---
if __name__ == "__main__":
    agente = AgenteN8N()
    print(f"Iniciando {agente}")
    disparados = agente.executar()
    print(f"Webhooks disparados: {len(disparados)}")
    for nome in disparados:
        print(f"  - {nome}")
    print(f"Webhooks registrados: {len(agente.listar_webhooks())}")
    print("Concluído.")
