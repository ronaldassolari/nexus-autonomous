"""
QA & SEGURANÇA — Squad 2: Fábrica de Software
Executa testes automatizados e scan de segurança OWASP Top 10.
Gera relatórios de qualidade e vulnerabilidades.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


# ---------------------------------------------------------------------------
# OWASP Top 10 — Checklist de Verificação
# ---------------------------------------------------------------------------

OWASP_TOP_10 = [
    {
        "id": "A01",
        "nome": "Broken Access Control",
        "verificacoes": [
            "Rotas protegidas exigem autenticação",
            "Autorização por role implementada",
            "CORS configurado corretamente",
            "Sem IDOR (Insecure Direct Object Reference)",
        ],
    },
    {
        "id": "A02",
        "nome": "Cryptographic Failures",
        "verificacoes": [
            "Senhas hasheadas com bcrypt/argon2",
            "HTTPS obrigatório em produção",
            "Secrets não hardcoded no código",
            "JWT com expiração configurada",
        ],
    },
    {
        "id": "A03",
        "nome": "Injection",
        "verificacoes": [
            "Queries parametrizadas (sem SQL injection)",
            "Input sanitizado contra XSS",
            "Sem eval() ou exec() com input do usuário",
            "ORM usado para queries de banco",
        ],
    },
    {
        "id": "A04",
        "nome": "Insecure Design",
        "verificacoes": [
            "Rate limiting implementado",
            "Validação de input com Pydantic/schema",
            "Error handling sem expor stack traces",
            "Logs sem dados sensíveis",
        ],
    },
    {
        "id": "A05",
        "nome": "Security Misconfiguration",
        "verificacoes": [
            "DEBUG=False em produção",
            "Headers de segurança configurados",
            "Dependências atualizadas",
            ".env não commitado no git",
        ],
    },
    {
        "id": "A06",
        "nome": "Vulnerable Components",
        "verificacoes": [
            "Sem dependências com CVE conhecidos",
            "Versões fixas no requirements.txt",
            "Dockerfile usa imagem slim/alpine",
        ],
    },
    {
        "id": "A07",
        "nome": "Auth Failures",
        "verificacoes": [
            "Brute force protegido (rate limit login)",
            "Password policy implementada",
            "Session timeout configurado",
        ],
    },
    {
        "id": "A08",
        "nome": "Data Integrity Failures",
        "verificacoes": [
            "Dados de entrada validados",
            "Serialização segura (sem pickle de input)",
            "CI/CD pipeline com verificação de integridade",
        ],
    },
    {
        "id": "A09",
        "nome": "Logging & Monitoring Failures",
        "verificacoes": [
            "Logging de autenticação (login/logout/falha)",
            "Logging de erros estruturado",
            "Sem logging de senhas ou tokens",
        ],
    },
    {
        "id": "A10",
        "nome": "SSRF",
        "verificacoes": [
            "URLs externas validadas antes de fetch",
            "Sem redirect aberto",
            "Whitelist de domínios para chamadas externas",
        ],
    },
]


@dataclass
class ResultadoTeste:
    """Resultado de um teste ou verificação."""
    categoria: str
    nome: str
    status: str  # "pass", "fail", "warn", "skip"
    detalhe: str = ""


@dataclass
class RelatorioQA:
    """Relatório completo de QA e segurança."""
    projeto: str
    testes_unitarios: dict = field(default_factory=lambda: {
        "executados": 0, "passaram": 0, "falharam": 0, "skipped": 0,
    })
    seguranca_owasp: list = field(default_factory=list)
    vulnerabilidades: list = field(default_factory=list)
    score_qualidade: float = 0.0
    score_seguranca: float = 0.0
    recomendacoes: list = field(default_factory=list)
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class QASeguranca(BaseAgente):
    """Agente QA & Segurança — testes automatizados e scan OWASP."""

    def __init__(self):
        super().__init__(
            nome="QA Seguranca",
            squad="Squad 2 — Fábrica de Software",
            papel="Testes automatizados e verificação de segurança OWASP Top 10",
        )
        self.pasta_relatorios = os.path.join(NEXUS_ROOT, "projetos_ativos", "qa_reports")
        os.makedirs(self.pasta_relatorios, exist_ok=True)

    def executar_testes_unitarios(self, pasta_mvp: str) -> dict:
        """Executa pytest no MVP se disponível."""
        resultado = {"executados": 0, "passaram": 0, "falharam": 0, "skipped": 0}
        test_dir = os.path.join(pasta_mvp, "tests")
        if not os.path.exists(test_dir):
            self.registrar_log("Sem pasta tests/", "Skipping testes unitários")
            return resultado

        try:
            proc = subprocess.run(
                ["python3", "-m", "pytest", test_dir, "-v", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=pasta_mvp,
            )
            output = proc.stdout + proc.stderr

            # Parse resultado do pytest
            for line in output.split("\n"):
                if "passed" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == "passed" and i > 0:
                            resultado["passaram"] = int(parts[i - 1])
                        if p == "failed" and i > 0:
                            resultado["falharam"] = int(parts[i - 1])

            resultado["executados"] = resultado["passaram"] + resultado["falharam"]
            self.registrar_log("Testes executados", f"{resultado['passaram']}/{resultado['executados']} passaram")

        except FileNotFoundError:
            self.registrar_log("pytest não encontrado", "Instalar com: pip install pytest")
        except subprocess.TimeoutExpired:
            self.registrar_log("Testes excederam timeout", "60s")
        except Exception as e:
            self.registrar_log("Erro nos testes", str(e))

        return resultado

    def scan_seguranca_estatico(self, pasta_mvp: str) -> list[ResultadoTeste]:
        """Scan estático de segurança: verifica padrões inseguros no código."""
        resultados = []
        padroes_inseguros = {
            "eval(": ("A03", "Uso de eval() — risco de injection"),
            "exec(": ("A03", "Uso de exec() — risco de injection"),
            "pickle.loads": ("A08", "Desserialização insegura com pickle"),
            "DEBUG = True": ("A05", "DEBUG ativo — desabilitar em produção"),
            "password =": ("A02", "Possível senha hardcoded"),
            "secret =": ("A02", "Possível secret hardcoded"),
            "SELECT *": ("A03", "Query SQL sem ORM — risco de injection"),
            "shell=True": ("A03", "subprocess com shell=True — risco de injection"),
        }

        python_files = []
        for root, _, files in os.walk(pasta_mvp):
            for f in files:
                if f.endswith(".py"):
                    python_files.append(os.path.join(root, f))

        for filepath in python_files:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()

            for padrao, (owasp_id, descricao) in padroes_inseguros.items():
                if padrao in conteudo:
                    resultados.append(ResultadoTeste(
                        categoria=owasp_id,
                        nome=descricao,
                        status="warn",
                        detalhe=f"Encontrado em: {os.path.relpath(filepath, pasta_mvp)}",
                    ))

        # Verificar .env no código
        env_file = os.path.join(pasta_mvp, ".env")
        gitignore = os.path.join(pasta_mvp, ".gitignore")
        if os.path.exists(env_file):
            gitignore_has_env = False
            if os.path.exists(gitignore):
                with open(gitignore, "r", encoding="utf-8") as f:
                    gitignore_has_env = ".env" in f.read()
            if not gitignore_has_env:
                resultados.append(ResultadoTeste(
                    categoria="A05",
                    nome=".env sem proteção no .gitignore",
                    status="fail",
                    detalhe="Adicionar .env ao .gitignore",
                ))

        self.registrar_log(f"Scan estático concluído", f"{len(resultados)} issues encontradas")
        return resultados

    def verificar_owasp(self, pasta_mvp: str) -> list[dict]:
        """Verifica checklist OWASP Top 10 contra o código do MVP."""
        resultados = []
        python_files = []
        for root, _, files in os.walk(pasta_mvp):
            for f in files:
                if f.endswith(".py"):
                    python_files.append(os.path.join(root, f))

        todo_codigo = ""
        for fp in python_files:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                todo_codigo += f.read() + "\n"

        for categoria in OWASP_TOP_10:
            cat_result = {
                "id": categoria["id"],
                "nome": categoria["nome"],
                "verificacoes": [],
            }
            for verificacao in categoria["verificacoes"]:
                status = self._verificar_item(verificacao, todo_codigo)
                cat_result["verificacoes"].append({
                    "item": verificacao,
                    "status": status,
                })
            resultados.append(cat_result)

        return resultados

    def _verificar_item(self, item: str, codigo: str) -> str:
        """Heurística para verificar um item de segurança."""
        item_lower = item.lower()
        if "parametrizada" in item_lower or "orm" in item_lower:
            if "sqlalchemy" in codigo or "from app.models" in codigo:
                return "pass"
            if "SELECT" in codigo and "%" in codigo:
                return "fail"
            return "pass"
        if "cors" in item_lower:
            return "pass" if "CORSMiddleware" in codigo else "warn"
        if "rate limit" in item_lower:
            return "pass" if "ratelimit" in codigo.lower() or "slowapi" in codigo.lower() else "warn"
        if "bcrypt" in item_lower or "hash" in item_lower:
            return "pass" if any(h in codigo for h in ["bcrypt", "argon2", "passlib", "password_hash"]) else "warn"
        if "pydantic" in item_lower or "validação" in item_lower or "schema" in item_lower:
            return "pass" if "BaseModel" in codigo or "pydantic" in codigo else "warn"
        if "debug" in item_lower and "false" in item_lower:
            return "warn"  # Precisa de verificação em runtime
        return "skip"

    def calcular_scores(self, testes: dict, scan: list, owasp: list) -> tuple[float, float]:
        """Calcula scores de qualidade e segurança (0-10)."""
        # Score qualidade
        total_testes = testes.get("executados", 0)
        if total_testes > 0:
            score_q = (testes["passaram"] / total_testes) * 10
        else:
            score_q = 5.0  # Sem testes = nota média

        # Score segurança
        total_checks = 0
        passed_checks = 0
        for cat in owasp:
            for v in cat["verificacoes"]:
                total_checks += 1
                if v["status"] == "pass":
                    passed_checks += 1
                elif v["status"] == "skip":
                    total_checks -= 1  # Não conta skipped

        penalidade = len([s for s in scan if s.status == "fail"]) * 1.0
        penalidade += len([s for s in scan if s.status == "warn"]) * 0.5

        if total_checks > 0:
            score_s = max(0, (passed_checks / total_checks) * 10 - penalidade)
        else:
            score_s = 5.0

        return round(score_q, 1), round(score_s, 1)

    def gerar_relatorio(self, rel: RelatorioQA) -> str:
        """Gera relatório markdown de QA e segurança."""
        md = (
            f"# Relatório QA & Segurança — {rel.projeto}\n"
            f"**Data:** {rel.data_criacao}\n"
            f"**Score Qualidade:** {rel.score_qualidade}/10\n"
            f"**Score Segurança:** {rel.score_seguranca}/10\n\n"
            f"## Testes Unitários\n"
            f"- Executados: {rel.testes_unitarios['executados']}\n"
            f"- Passaram: {rel.testes_unitarios['passaram']}\n"
            f"- Falharam: {rel.testes_unitarios['falharam']}\n\n"
            f"## OWASP Top 10\n"
        )
        for cat in rel.seguranca_owasp:
            status_emoji = {"pass": "OK", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}
            md += f"\n### {cat['id']} — {cat['nome']}\n"
            for v in cat["verificacoes"]:
                s = status_emoji.get(v["status"], "?")
                md += f"- [{s}] {v['item']}\n"

        if rel.vulnerabilidades:
            md += "\n## Vulnerabilidades Encontradas\n"
            for v in rel.vulnerabilidades:
                cat = v.get("categoria", v.get("categoria", "?")) if isinstance(v, dict) else v.categoria
                nome = v.get("nome", "") if isinstance(v, dict) else v.nome
                det = v.get("detalhe", "") if isinstance(v, dict) else v.detalhe
                md += f"- **[{cat}]** {nome} — {det}\n"

        if rel.recomendacoes:
            md += "\n## Recomendações\n"
            for r in rel.recomendacoes:
                md += f"- {r}\n"

        return md

    def executar(self):
        """Loop principal: testa MVPs e gera relatórios."""
        self.atualizar_status("em_execucao")
        self.registrar_log("QA & Segurança iniciado")

        pasta_mvps = os.path.join(NEXUS_ROOT, "projetos_ativos", "mvps")
        relatorios_gerados = 0

        if os.path.exists(pasta_mvps):
            for mvp_dir in os.listdir(pasta_mvps):
                pasta_mvp = os.path.join(pasta_mvps, mvp_dir)
                if not os.path.isdir(pasta_mvp):
                    continue

                self.registrar_log(f"Analisando MVP: {mvp_dir}")

                rel = RelatorioQA(projeto=mvp_dir)
                rel.testes_unitarios = self.executar_testes_unitarios(pasta_mvp)

                scan_results = self.scan_seguranca_estatico(pasta_mvp)
                rel.vulnerabilidades = [asdict(r) for r in scan_results if r.status in ("fail", "warn")]

                rel.seguranca_owasp = self.verificar_owasp(pasta_mvp)

                score_q, score_s = self.calcular_scores(
                    rel.testes_unitarios,
                    scan_results,
                    rel.seguranca_owasp,
                )
                rel.score_qualidade = score_q
                rel.score_seguranca = score_s

                # Recomendações automáticas
                if score_s < 7:
                    rel.recomendacoes.append("Segurança abaixo de 7 — revisar antes de deploy")
                if rel.testes_unitarios["executados"] == 0:
                    rel.recomendacoes.append("Adicionar testes unitários")
                for v in scan_results:
                    if v.status == "fail":
                        rel.recomendacoes.append(f"CORRIGIR: {v.nome} ({v.detalhe})")

                # Salvar relatório
                report_md = self.gerar_relatorio(rel)
                pasta_report = os.path.join(self.pasta_relatorios, mvp_dir)
                os.makedirs(pasta_report, exist_ok=True)
                with open(os.path.join(pasta_report, "qa_report.md"), "w", encoding="utf-8") as f:
                    f.write(report_md)
                with open(os.path.join(pasta_report, "qa_report.json"), "w", encoding="utf-8") as f:
                    json.dump(rel.to_dict(), f, ensure_ascii=False, indent=2)

                # Notificar DevOps se aprovado
                if score_q >= 7 and score_s >= 7:
                    self.enviar_mensagem(
                        destinatario="devops",
                        assunto=f"MVP aprovado para deploy: {mvp_dir}",
                        conteudo=(
                            f"QA aprovado para '{mvp_dir}'.\n"
                            f"**Qualidade:** {score_q}/10\n"
                            f"**Segurança:** {score_s}/10\n"
                            f"Pronto para configurar CI/CD e deploy.\n"
                        ),
                    )
                else:
                    self.enviar_mensagem(
                        destinatario="dev_rapido",
                        assunto=f"MVP precisa de correções: {mvp_dir}",
                        conteudo=(
                            f"QA reprovou '{mvp_dir}'.\n"
                            f"**Qualidade:** {score_q}/10\n"
                            f"**Segurança:** {score_s}/10\n"
                            f"Relatório completo em: qa_reports/{mvp_dir}/\n"
                        ),
                    )

                relatorios_gerados += 1

        self.atualizar_status("concluido")
        self.registrar_log("QA finalizado", f"{relatorios_gerados} relatórios gerados")
        return relatorios_gerados


# --- Execução direta ---
if __name__ == "__main__":
    agente = QASeguranca()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    print(f"Concluído: {resultado} MVPs analisados.")
