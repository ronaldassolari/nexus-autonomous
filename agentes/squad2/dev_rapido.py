"""
DEV RÁPIDO — Squad 2: Fábrica de Software
Construtor de MVPs em 24-48h. Gera scaffolding de projetos com FastAPI/Django,
estrutura de pastas, boilerplate e endpoints básicos.
"""

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Templates de Scaffolding por stack
# ---------------------------------------------------------------------------

STACK_TEMPLATES = {
    "fastapi": {
        "nome": "FastAPI + PostgreSQL",
        "descricao": "API REST rápida, async, ideal para SaaS e chatbots",
        "estrutura": {
            "app/": {
                "__init__.py": "",
                "main.py": "fastapi_main",
                "config.py": "config",
                "models/": {"__init__.py": "", "user.py": "model_user"},
                "routes/": {"__init__.py": "", "health.py": "route_health", "auth.py": "route_auth"},
                "services/": {"__init__.py": ""},
                "middleware/": {"__init__.py": ""},
            },
            "tests/": {"__init__.py": "", "test_health.py": "test_health"},
            "alembic/": {"env.py": "alembic_env"},
            "requirements.txt": "requirements_fastapi",
            ".env.example": "env_example",
            "Dockerfile": "dockerfile",
            "docker-compose.yml": "docker_compose",
            "README.md": "readme",
        },
    },
    "django": {
        "nome": "Django + DRF",
        "descricao": "Full-stack com admin, auth e ORM completo, ideal para marketplaces",
        "estrutura": {
            "manage.py": "django_manage",
            "config/": {
                "__init__.py": "",
                "settings.py": "django_settings",
                "urls.py": "django_urls",
                "wsgi.py": "django_wsgi",
            },
            "core/": {
                "__init__.py": "",
                "models.py": "django_models",
                "views.py": "django_views",
                "serializers.py": "django_serializers",
                "urls.py": "django_app_urls",
                "admin.py": "django_admin",
            },
            "requirements.txt": "requirements_django",
            ".env.example": "env_example",
            "Dockerfile": "dockerfile",
        },
    },
}

# Boilerplate de código por template key
BOILERPLATE = {
    "fastapi_main": '''"""FastAPI Application — MVP gerado pelo Dev Rápido."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, auth
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"status": "ok", "project": settings.PROJECT_NAME}
''',
    "config": '''"""Configurações do projeto via variáveis de ambiente."""
import os
from dataclasses import dataclass

@dataclass
class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Nexus MVP")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/nexus_mvp")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    ALLOWED_ORIGINS: list = None

    def __post_init__(self):
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        self.ALLOWED_ORIGINS = origins.split(",")

settings = Settings()
''',
    "route_health": '''"""Health check endpoint."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nexus-mvp"}
''',
    "route_auth": '''"""Auth endpoints — placeholder para MVP."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

@router.post("/login")
async def login(data: LoginRequest):
    # TODO: implementar autenticação real
    return {"token": "placeholder-jwt-token", "email": data.email}

@router.post("/signup")
async def signup(data: SignupRequest):
    # TODO: implementar criação de usuário
    return {"message": "Usuário criado", "email": data.email}
''',
    "test_health": '''"""Testes do health check."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
''',
    "requirements_fastapi": '''fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic[email]>=2.6.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
''',
    "env_example": '''PROJECT_NAME=Nexus MVP
DATABASE_URL=postgresql://user:pass@localhost:5432/nexus_mvp
SECRET_KEY=change-me-in-production
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
''',
    "dockerfile": '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    "docker_compose": '''version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nexus_mvp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
''',
    "readme": '''# Nexus MVP
Gerado automaticamente pelo Dev Rápido — Squad 2.

## Setup
```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints
- `GET /` — Status
- `GET /health` — Health check
- `POST /auth/login` — Login
- `POST /auth/signup` — Signup
- `GET /docs` — Swagger UI
''',
    "model_user": '''"""User model placeholder."""
# TODO: implementar model com SQLAlchemy
''',
    "alembic_env": '''"""Alembic environment — placeholder."""
# TODO: configurar alembic com SQLAlchemy
''',
    "django_manage": '''#!/usr/bin/env python
"""Django management script."""
import os, sys
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
''',
    "django_settings": '''"""Django settings — placeholder para MVP."""
# TODO: configurar settings completo
''',
    "django_urls": '''"""URL configuration."""
from django.urls import path, include
urlpatterns = [path("api/", include("core.urls"))]
''',
    "django_wsgi": '''"""WSGI config."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
''',
    "django_models": '''"""Django models — placeholder."""
from django.db import models
''',
    "django_views": '''"""Django views — placeholder."""
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def health(request):
    return Response({"status": "healthy"})
''',
    "django_serializers": '''"""Django serializers — placeholder."""
from rest_framework import serializers
''',
    "django_app_urls": '''"""App URL configuration."""
from django.urls import path
from . import views
urlpatterns = [path("health/", views.health)]
''',
    "django_admin": '''"""Django admin — placeholder."""
from django.contrib import admin
''',
    "requirements_django": '''django>=5.0
djangorestframework>=3.15
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
gunicorn>=22.0.0
pytest>=8.0.0
pytest-django>=4.8.0
''',
}


@dataclass
class MVPSpec:
    """Especificação do MVP gerado."""
    projeto: str
    stack: str
    arquivos_criados: list = field(default_factory=list)
    endpoints: list = field(default_factory=list)
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class DevRapido(BaseAgente):
    """Dev Rápido — gera MVPs funcionais em 24-48h com scaffolding automatizado."""

    def __init__(self):
        super().__init__(
            nome="Dev Rapido",
            squad="Squad 2 — Fábrica de Software",
            papel="MVP em 24-48h com FastAPI/Django scaffolding",
        )
        self.pasta_mvps = os.path.join(NEXUS_ROOT, "projetos_ativos", "mvps")
        os.makedirs(self.pasta_mvps, exist_ok=True)

    def selecionar_stack(self, tipo_produto: str) -> str:
        """Seleciona stack ideal para o tipo de produto."""
        mapa = {
            "saas_b2b": "fastapi",
            "chatbot_whatsapp": "fastapi",
            "marketplace": "fastapi",
            "ebook_ia": "fastapi",
        }
        return mapa.get(tipo_produto, "fastapi")

    def gerar_mvp(self, projeto: str, tipo_produto: str) -> MVPSpec:
        """Gera scaffolding completo do MVP."""
        stack = self.selecionar_stack(tipo_produto)
        template = STACK_TEMPLATES[stack]

        pasta_mvp = os.path.join(self.pasta_mvps, projeto.lower().replace(" ", "_"))
        os.makedirs(pasta_mvp, exist_ok=True)

        spec = MVPSpec(projeto=projeto, stack=stack)
        self._criar_estrutura(pasta_mvp, template["estrutura"], spec)

        # Registrar endpoints
        if stack == "fastapi":
            spec.endpoints = [
                {"method": "GET", "path": "/", "descricao": "Status"},
                {"method": "GET", "path": "/health", "descricao": "Health check"},
                {"method": "POST", "path": "/auth/login", "descricao": "Login"},
                {"method": "POST", "path": "/auth/signup", "descricao": "Signup"},
                {"method": "GET", "path": "/docs", "descricao": "Swagger UI"},
            ]

        self.registrar_log(
            f"MVP gerado: {projeto}",
            f"Stack {stack}, {len(spec.arquivos_criados)} arquivos",
        )
        return spec

    def _criar_estrutura(self, base_path: str, estrutura: dict, spec: MVPSpec):
        """Cria recursivamente a estrutura de pastas e arquivos."""
        for nome, conteudo in estrutura.items():
            caminho = os.path.join(base_path, nome)

            if isinstance(conteudo, dict):
                # É uma pasta
                os.makedirs(caminho, exist_ok=True)
                self._criar_estrutura(caminho, conteudo, spec)
            else:
                # É um arquivo
                texto = BOILERPLATE.get(conteudo, conteudo) if conteudo else ""
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(texto)
                spec.arquivos_criados.append(caminho)

    def salvar_spec(self, spec: MVPSpec):
        """Salva especificação do MVP."""
        nome = spec.projeto.lower().replace(" ", "_")
        pasta = os.path.join(self.pasta_mvps, nome)
        with open(os.path.join(pasta, "mvp_spec.json"), "w", encoding="utf-8") as f:
            json.dump(spec.to_dict(), f, ensure_ascii=False, indent=2)

    def executar(self):
        """Loop principal: lê projetos aprovados e gera MVPs."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Dev Rápido iniciado")

        pasta_projetos = os.path.join(NEXUS_ROOT, "projetos_ativos")
        mvps_gerados = 0

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

                tipo = self._inferir_tipo(nome, projeto.get("descricao", ""))
                spec = self.gerar_mvp(nome, tipo)
                self.salvar_spec(spec)

                # Notificar QA
                self.enviar_mensagem(
                    destinatario="qa_seguranca",
                    assunto=f"MVP pronto para testes: {nome}",
                    conteudo=(
                        f"MVP de '{nome}' gerado com sucesso.\n"
                        f"**Stack:** {spec.stack}\n"
                        f"**Arquivos:** {len(spec.arquivos_criados)}\n"
                        f"**Endpoints:** {len(spec.endpoints)}\n"
                        f"Pasta: projetos_ativos/mvps/{nome.lower().replace(' ', '_')}/\n"
                        f"Ação: executar testes e scan de segurança.\n"
                    ),
                )
                mvps_gerados += 1

        self.atualizar_status("concluido")
        self.registrar_log("Dev Rápido finalizado", f"{mvps_gerados} MVPs gerados")
        return mvps_gerados

    def _inferir_tipo(self, nome: str, descricao: str) -> str:
        texto = (nome + " " + descricao).lower()
        if any(kw in texto for kw in ["whatsapp", "zap", "chat", "bot"]):
            return "chatbot_whatsapp"
        if any(kw in texto for kw in ["marketplace", "loja", "empreitaja"]):
            return "marketplace"
        if any(kw in texto for kw in ["ebook", "livro", "influencer"]):
            return "ebook_ia"
        return "saas_b2b"


# --- Execução direta ---
if __name__ == "__main__":
    agente = DevRapido()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    print(f"Concluído: {resultado} MVPs gerados.")
