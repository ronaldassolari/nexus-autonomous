"""
Base Agent — Classe mãe de todos os agentes do Nexus Autonomous.
Cada agente herda desta classe e implementa o método executar().
"""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime

# Caminhos raiz do ecossistema
NEXUS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMUNICACAO_DIR = os.path.join(NEXUS_ROOT, "comunicacao")
INTELIGENCIA_DIR = os.path.join(NEXUS_ROOT, "inteligencia")
LOG_FILE = os.path.join(NEXUS_ROOT, "log_execucao.md")


class BaseAgente(ABC):
    """Classe base para todos os agentes do ecossistema Nexus Autonomous."""

    def __init__(self, nome: str, squad: str, papel: str):
        self.nome = nome
        self.squad = squad
        self.papel = papel
        self.status = "inicializado"
        self._garantir_pastas()

    def _garantir_pastas(self):
        """Cria pastas de comunicação do agente se não existirem."""
        self.pasta_comunicacao = os.path.join(COMUNICACAO_DIR, self.nome.lower().replace(" ", "_"))
        os.makedirs(self.pasta_comunicacao, exist_ok=True)

    def registrar_log(self, acao: str, resultado: str = ""):
        """Registra ação no log_execucao.md com timestamp."""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        linha = f"\n[{agora}] {self.nome.upper()}: {acao}"
        if resultado:
            linha += f" → {resultado}"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linha + "\n")

    def enviar_mensagem(self, destinatario: str, assunto: str, conteudo: str):
        """Envia mensagem para outro agente via arquivo .md em /comunicacao/."""
        pasta_dest = os.path.join(COMUNICACAO_DIR, destinatario.lower().replace(" ", "_"))
        os.makedirs(pasta_dest, exist_ok=True)
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(pasta_dest, f"de_{self.nome.lower().replace(' ', '_')}_{agora}.md")
        conteudo_msg = (
            f"# Mensagem de {self.nome}\n"
            f"**Para:** {destinatario}\n"
            f"**Assunto:** {assunto}\n"
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"{conteudo}\n"
        )
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo_msg)
        self.registrar_log(f"Mensagem enviada para {destinatario}", assunto)

    def ler_mensagens(self) -> list[dict]:
        """Lê todas as mensagens pendentes na pasta de comunicação do agente."""
        mensagens = []
        if not os.path.exists(self.pasta_comunicacao):
            return mensagens
        for arquivo in sorted(os.listdir(self.pasta_comunicacao)):
            if arquivo.endswith(".md"):
                caminho = os.path.join(self.pasta_comunicacao, arquivo)
                with open(caminho, "r", encoding="utf-8") as f:
                    mensagens.append({
                        "arquivo": arquivo,
                        "conteudo": f.read(),
                        "caminho": caminho,
                    })
        return mensagens

    def publicar_resultado(self, titulo: str, dados: dict | str):
        """Publica resultado do trabalho na pasta de comunicação do agente."""
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.pasta_comunicacao, f"resultado_{agora}.md")
        if isinstance(dados, dict):
            corpo = json.dumps(dados, ensure_ascii=False, indent=2)
        else:
            corpo = str(dados)
        conteudo = f"# {titulo}\n**Agente:** {self.nome}\n**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{corpo}\n"
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        self.registrar_log(f"Resultado publicado: {titulo}")

    def atualizar_status(self, novo_status: str):
        """Atualiza o status do agente e registra no log."""
        self.status = novo_status
        status_file = os.path.join(self.pasta_comunicacao, "status.md")
        with open(status_file, "w", encoding="utf-8") as f:
            f.write(f"# Status: {self.nome}\n**Status:** {novo_status}\n**Atualizado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        self.registrar_log(f"Status atualizado para: {novo_status}")

    @abstractmethod
    def executar(self):
        """Loop principal do agente. Cada agente implementa sua lógica aqui."""
        ...

    def __repr__(self):
        return f"<{self.nome} [{self.squad}] status={self.status}>"
