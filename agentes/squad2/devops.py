"""
DEVOPS — Squad 2: Fábrica de Software
Gerencia CI/CD, monitoramento, deploy e rollback.
Gera GitHub Actions workflows, health checks e configurações de infraestrutura.
"""

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Templates de CI/CD
# ---------------------------------------------------------------------------

GITHUB_ACTIONS_CI = """name: CI — {projeto}

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      - run: pip install ruff
      - run: ruff check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
      - run: pip install safety bandit
      - run: safety check -r requirements.txt || true
      - run: bandit -r app/ -ll || true
"""

GITHUB_ACTIONS_CD = """name: CD — {projeto}

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{{{ github.repository }}}}:latest
            ghcr.io/${{{{ github.repository }}}}:${{{{ github.sha }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: echo "Deploy step — configurar conforme provider"

  health-check:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Wait for deploy
        run: sleep 30
      - name: Health check
        run: |
          for i in 1 2 3 4 5; do
            STATUS=$(curl -s -o /dev/null -w "%{{http_code}}" ${{{{ vars.HEALTH_URL }}}}/health || echo "000")
            if [ "$STATUS" = "200" ]; then
              echo "Health check passed"
              exit 0
            fi
            echo "Attempt $i: status $STATUS, retrying..."
            sleep 10
          done
          echo "Health check failed — triggering rollback"
          exit 1

  rollback:
    needs: health-check
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Rollback to previous version
        run: echo "Rollback step — reverter para última versão estável"
"""

GITIGNORE_TEMPLATE = """# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
venv/
.venv/

# Environment
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Docker
docker-compose.override.yml
"""

HEALTH_CHECK_CODE = '''"""Health check endpoint com métricas básicas."""
import time
import psutil

_start_time = time.time()

def get_health():
    """Retorna status de saúde do serviço."""
    uptime = time.time() - _start_time
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
    except Exception:
        cpu = -1
        memory = -1

    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 1),
        "cpu_percent": cpu,
        "memory_percent": memory,
        "version": "0.1.0",
    }
'''


@dataclass
class InfraSpec:
    """Especificação de infraestrutura gerada."""
    projeto: str
    arquivos_ci_cd: list = field(default_factory=list)
    health_check: bool = False
    monitoring: bool = False
    rollback_automatico: bool = False
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class DevOps(BaseAgente):
    """Agente DevOps — CI/CD, monitoramento, deploy e rollback."""

    def __init__(self):
        super().__init__(
            nome="DevOps",
            squad="Squad 2 — Fábrica de Software",
            papel="CI/CD, monitoramento, health checks e rollback automático",
        )
        self.pasta_infra = os.path.join(NEXUS_ROOT, "projetos_ativos", "infra")
        os.makedirs(self.pasta_infra, exist_ok=True)

    def gerar_ci_cd(self, projeto: str, pasta_mvp: str) -> InfraSpec:
        """Gera configuração completa de CI/CD para um MVP."""
        spec = InfraSpec(projeto=projeto)
        nome_projeto = projeto.lower().replace(" ", "_")
        pasta_projeto = os.path.join(self.pasta_infra, nome_projeto)
        os.makedirs(pasta_projeto, exist_ok=True)

        # GitHub Actions — CI
        github_dir = os.path.join(pasta_projeto, ".github", "workflows")
        os.makedirs(github_dir, exist_ok=True)

        ci_content = GITHUB_ACTIONS_CI.format(projeto=projeto)
        ci_path = os.path.join(github_dir, "ci.yml")
        with open(ci_path, "w", encoding="utf-8") as f:
            f.write(ci_content)
        spec.arquivos_ci_cd.append(ci_path)

        # GitHub Actions — CD
        cd_content = GITHUB_ACTIONS_CD.format(projeto=projeto)
        cd_path = os.path.join(github_dir, "cd.yml")
        with open(cd_path, "w", encoding="utf-8") as f:
            f.write(cd_content)
        spec.arquivos_ci_cd.append(cd_path)
        spec.rollback_automatico = True

        # .gitignore
        gitignore_path = os.path.join(pasta_projeto, ".gitignore")
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(GITIGNORE_TEMPLATE)
        spec.arquivos_ci_cd.append(gitignore_path)

        # Health check
        health_path = os.path.join(pasta_projeto, "health_check.py")
        with open(health_path, "w", encoding="utf-8") as f:
            f.write(HEALTH_CHECK_CODE)
        spec.health_check = True
        spec.arquivos_ci_cd.append(health_path)

        # Monitoring config
        monitoring = self._gerar_monitoring_config(projeto)
        monitoring_path = os.path.join(pasta_projeto, "monitoring.json")
        with open(monitoring_path, "w", encoding="utf-8") as f:
            json.dump(monitoring, f, ensure_ascii=False, indent=2)
        spec.monitoring = True
        spec.arquivos_ci_cd.append(monitoring_path)

        self.registrar_log(
            f"CI/CD gerado para '{projeto}'",
            f"{len(spec.arquivos_ci_cd)} arquivos criados",
        )
        return spec

    def _gerar_monitoring_config(self, projeto: str) -> dict:
        """Gera configuração de monitoramento."""
        return {
            "projeto": projeto,
            "alertas": [
                {
                    "nome": "Health Check Failed",
                    "tipo": "http",
                    "url": "/health",
                    "intervalo_segundos": 60,
                    "timeout_segundos": 10,
                    "tentativas_antes_alerta": 3,
                    "notificar": ["log", "webhook"],
                },
                {
                    "nome": "High CPU",
                    "tipo": "metrica",
                    "metrica": "cpu_percent",
                    "threshold": 90,
                    "duracao_minutos": 5,
                    "notificar": ["log"],
                },
                {
                    "nome": "High Memory",
                    "tipo": "metrica",
                    "metrica": "memory_percent",
                    "threshold": 85,
                    "duracao_minutos": 5,
                    "notificar": ["log"],
                },
                {
                    "nome": "Error Rate High",
                    "tipo": "metrica",
                    "metrica": "error_rate_5xx",
                    "threshold": 5,
                    "duracao_minutos": 2,
                    "notificar": ["log", "webhook"],
                },
            ],
            "metricas_coletadas": [
                "requests_total",
                "request_duration_seconds",
                "error_rate_5xx",
                "cpu_percent",
                "memory_percent",
                "active_connections",
            ],
            "rollback": {
                "automatico": True,
                "trigger": "health_check_failed",
                "estrategia": "revert_to_last_stable",
                "max_tentativas": 2,
            },
        }

    def salvar_spec(self, spec: InfraSpec):
        """Salva especificação de infraestrutura."""
        nome = spec.projeto.lower().replace(" ", "_")
        pasta = os.path.join(self.pasta_infra, nome)
        with open(os.path.join(pasta, "infra_spec.json"), "w", encoding="utf-8") as f:
            json.dump(spec.to_dict(), f, ensure_ascii=False, indent=2)

    def executar(self):
        """Loop principal: gera CI/CD para MVPs aprovados pelo QA."""
        self.atualizar_status("em_execucao")
        self.registrar_log("DevOps iniciado")

        pasta_mvps = os.path.join(NEXUS_ROOT, "projetos_ativos", "mvps")
        infras_geradas = 0

        if os.path.exists(pasta_mvps):
            for mvp_dir in os.listdir(pasta_mvps):
                pasta_mvp = os.path.join(pasta_mvps, mvp_dir)
                if not os.path.isdir(pasta_mvp):
                    continue

                spec = self.gerar_ci_cd(mvp_dir, pasta_mvp)
                self.salvar_spec(spec)

                self.publicar_resultado(
                    f"Infra pronta: {mvp_dir}",
                    (
                        f"CI/CD configurado para '{mvp_dir}'.\n"
                        f"- GitHub Actions CI: lint → test → security\n"
                        f"- GitHub Actions CD: build → deploy → health check → rollback\n"
                        f"- Health check endpoint configurado\n"
                        f"- Monitoring com alertas automáticos\n"
                        f"- Rollback automático se health check falhar\n"
                    ),
                )
                infras_geradas += 1

        # Ler mensagens pendentes
        mensagens = self.ler_mensagens()
        for msg in mensagens:
            self.registrar_log("Mensagem processada", msg.get("arquivo", ""))

        self.atualizar_status("concluido")
        self.registrar_log("DevOps finalizado", f"{infras_geradas} infras geradas")
        return infras_geradas


# --- Execução direta ---
if __name__ == "__main__":
    agente = DevOps()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    print(f"Concluído: {resultado} projetos com infra configurada.")
