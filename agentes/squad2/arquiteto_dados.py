"""
ARQUITETO DE DADOS — Squad 2: Fábrica de Software
Define schemas de banco de dados, ERDs, migrations e infraestrutura de dados.
Suporta SQL (PostgreSQL) e NoSQL (MongoDB) com geração automática de schemas.
"""

import os
import sys
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Templates de Schema por tipo de produto
# ---------------------------------------------------------------------------

SCHEMAS_SQL = {
    "saas_b2b": {
        "engine": "postgresql",
        "tabelas": [
            {
                "nome": "users",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "email", "tipo": "VARCHAR(255)", "unique": True, "not_null": True},
                    {"nome": "password_hash", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "name", "tipo": "VARCHAR(150)", "not_null": True},
                    {"nome": "role", "tipo": "VARCHAR(50)", "default": "'user'"},
                    {"nome": "is_active", "tipo": "BOOLEAN", "default": "TRUE"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                    {"nome": "updated_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": ["CREATE INDEX idx_users_email ON users(email)"],
            },
            {
                "nome": "organizations",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "name", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "slug", "tipo": "VARCHAR(100)", "unique": True},
                    {"nome": "plan", "tipo": "VARCHAR(50)", "default": "'free'"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": ["CREATE INDEX idx_orgs_slug ON organizations(slug)"],
            },
            {
                "nome": "subscriptions",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "org_id", "tipo": "UUID", "fk": "organizations(id)", "not_null": True},
                    {"nome": "plan", "tipo": "VARCHAR(50)", "not_null": True},
                    {"nome": "status", "tipo": "VARCHAR(30)", "default": "'active'"},
                    {"nome": "price_cents", "tipo": "INTEGER", "not_null": True},
                    {"nome": "started_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                    {"nome": "expires_at", "tipo": "TIMESTAMPTZ"},
                ],
                "indices": ["CREATE INDEX idx_subs_org ON subscriptions(org_id)"],
            },
        ],
    },
    "marketplace": {
        "engine": "postgresql",
        "tabelas": [
            {
                "nome": "users",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "email", "tipo": "VARCHAR(255)", "unique": True, "not_null": True},
                    {"nome": "password_hash", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "name", "tipo": "VARCHAR(150)", "not_null": True},
                    {"nome": "user_type", "tipo": "VARCHAR(20)", "not_null": True},
                    {"nome": "phone", "tipo": "VARCHAR(20)"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": ["CREATE INDEX idx_users_type ON users(user_type)"],
            },
            {
                "nome": "products",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "seller_id", "tipo": "UUID", "fk": "users(id)", "not_null": True},
                    {"nome": "title", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "description", "tipo": "TEXT"},
                    {"nome": "price_cents", "tipo": "INTEGER", "not_null": True},
                    {"nome": "category", "tipo": "VARCHAR(100)"},
                    {"nome": "status", "tipo": "VARCHAR(30)", "default": "'active'"},
                    {"nome": "images", "tipo": "JSONB", "default": "'[]'"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [
                    "CREATE INDEX idx_products_seller ON products(seller_id)",
                    "CREATE INDEX idx_products_category ON products(category)",
                    "CREATE INDEX idx_products_status ON products(status)",
                ],
            },
            {
                "nome": "orders",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "buyer_id", "tipo": "UUID", "fk": "users(id)", "not_null": True},
                    {"nome": "product_id", "tipo": "UUID", "fk": "products(id)", "not_null": True},
                    {"nome": "quantity", "tipo": "INTEGER", "default": "1"},
                    {"nome": "total_cents", "tipo": "INTEGER", "not_null": True},
                    {"nome": "status", "tipo": "VARCHAR(30)", "default": "'pending'"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [
                    "CREATE INDEX idx_orders_buyer ON orders(buyer_id)",
                    "CREATE INDEX idx_orders_status ON orders(status)",
                ],
            },
            {
                "nome": "reviews",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "order_id", "tipo": "UUID", "fk": "orders(id)", "not_null": True},
                    {"nome": "user_id", "tipo": "UUID", "fk": "users(id)", "not_null": True},
                    {"nome": "rating", "tipo": "SMALLINT", "not_null": True},
                    {"nome": "comment", "tipo": "TEXT"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [],
            },
        ],
    },
    "chatbot_whatsapp": {
        "engine": "postgresql",
        "tabelas": [
            {
                "nome": "tenants",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "name", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "whatsapp_number", "tipo": "VARCHAR(20)", "unique": True},
                    {"nome": "api_key", "tipo": "VARCHAR(255)", "unique": True},
                    {"nome": "plan", "tipo": "VARCHAR(50)", "default": "'starter'"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [],
            },
            {
                "nome": "conversations",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "tenant_id", "tipo": "UUID", "fk": "tenants(id)", "not_null": True},
                    {"nome": "customer_phone", "tipo": "VARCHAR(20)", "not_null": True},
                    {"nome": "status", "tipo": "VARCHAR(30)", "default": "'active'"},
                    {"nome": "started_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                    {"nome": "ended_at", "tipo": "TIMESTAMPTZ"},
                ],
                "indices": [
                    "CREATE INDEX idx_conv_tenant ON conversations(tenant_id)",
                    "CREATE INDEX idx_conv_phone ON conversations(customer_phone)",
                ],
            },
            {
                "nome": "messages",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "conversation_id", "tipo": "UUID", "fk": "conversations(id)", "not_null": True},
                    {"nome": "direction", "tipo": "VARCHAR(10)", "not_null": True},
                    {"nome": "content", "tipo": "TEXT", "not_null": True},
                    {"nome": "message_type", "tipo": "VARCHAR(20)", "default": "'text'"},
                    {"nome": "metadata", "tipo": "JSONB", "default": "'{}'"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [
                    "CREATE INDEX idx_msg_conv ON messages(conversation_id)",
                    "CREATE INDEX idx_msg_created ON messages(created_at)",
                ],
            },
            {
                "nome": "flows",
                "colunas": [
                    {"nome": "id", "tipo": "UUID", "pk": True, "default": "gen_random_uuid()"},
                    {"nome": "tenant_id", "tipo": "UUID", "fk": "tenants(id)", "not_null": True},
                    {"nome": "name", "tipo": "VARCHAR(255)", "not_null": True},
                    {"nome": "nodes", "tipo": "JSONB", "not_null": True, "default": "'[]'"},
                    {"nome": "is_active", "tipo": "BOOLEAN", "default": "TRUE"},
                    {"nome": "created_at", "tipo": "TIMESTAMPTZ", "default": "NOW()"},
                ],
                "indices": [],
            },
        ],
    },
}


@dataclass
class EspecificacaoDB:
    """Especificação completa de banco de dados."""
    projeto: str
    tipo_produto: str
    engine: str = "postgresql"
    tabelas: list = field(default_factory=list)
    migrations: list = field(default_factory=list)
    indices: list = field(default_factory=list)
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ArquitetoDados(BaseAgente):
    """Agente Arquiteto de Dados — define schemas, ERDs e migrations."""

    def __init__(self):
        super().__init__(
            nome="Arquiteto Dados",
            squad="Squad 2 — Fábrica de Software",
            papel="Banco de dados, schemas, ERD e infraestrutura de dados",
        )
        self.pasta_schemas = os.path.join(NEXUS_ROOT, "projetos_ativos", "schemas")
        os.makedirs(self.pasta_schemas, exist_ok=True)

    def gerar_schema(self, projeto: str, tipo_produto: str) -> EspecificacaoDB:
        """Gera schema de banco de dados baseado no tipo de produto."""
        template = SCHEMAS_SQL.get(tipo_produto)
        if not template:
            self.registrar_log(f"Tipo '{tipo_produto}' sem schema", "Usando saas_b2b")
            template = SCHEMAS_SQL["saas_b2b"]
            tipo_produto = "saas_b2b"

        spec = EspecificacaoDB(
            projeto=projeto,
            tipo_produto=tipo_produto,
            engine=template["engine"],
            tabelas=template["tabelas"],
        )

        # Gerar migrations SQL
        spec.migrations = self._gerar_migrations(template["tabelas"])

        self.registrar_log(
            f"Schema gerado para '{projeto}'",
            f"{len(spec.tabelas)} tabelas, engine: {spec.engine}",
        )
        return spec

    def _gerar_migrations(self, tabelas: list[dict]) -> list[str]:
        """Gera SQL de migration CREATE TABLE."""
        migrations = ["-- Migration gerada automaticamente pelo Arquiteto de Dados"]
        migrations.append(f"-- Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        migrations.append('CREATE EXTENSION IF NOT EXISTS "pgcrypto";\n')

        for tabela in tabelas:
            sql = f"CREATE TABLE IF NOT EXISTS {tabela['nome']} (\n"
            colunas_sql = []
            fks = []

            for col in tabela["colunas"]:
                parts = [f"  {col['nome']} {col['tipo']}"]
                if col.get("pk"):
                    parts.append("PRIMARY KEY")
                if col.get("not_null"):
                    parts.append("NOT NULL")
                if col.get("unique"):
                    parts.append("UNIQUE")
                if col.get("default"):
                    parts.append(f"DEFAULT {col['default']}")
                colunas_sql.append(" ".join(parts))

                if col.get("fk"):
                    fks.append(
                        f"  CONSTRAINT fk_{tabela['nome']}_{col['nome']} "
                        f"FOREIGN KEY ({col['nome']}) REFERENCES {col['fk']} ON DELETE CASCADE"
                    )

            todas_colunas = colunas_sql + fks
            sql += ",\n".join(todas_colunas)
            sql += "\n);\n"
            migrations.append(sql)

            # Indices
            for idx in tabela.get("indices", []):
                migrations.append(idx + ";")
            migrations.append("")

        return migrations

    def gerar_erd_texto(self, spec: EspecificacaoDB) -> str:
        """Gera representação textual do ERD (Entity Relationship Diagram)."""
        erd = f"# ERD — {spec.projeto}\n\n```\n"
        for tabela in spec.tabelas:
            erd += f"┌{'─' * 40}┐\n"
            erd += f"│ {tabela['nome'].upper():<38} │\n"
            erd += f"├{'─' * 40}┤\n"
            for col in tabela["colunas"]:
                pk = "PK" if col.get("pk") else "  "
                fk = "FK" if col.get("fk") else "  "
                nn = "NN" if col.get("not_null") else "  "
                erd += f"│ {pk} {fk} {nn} {col['nome']:<20} {col['tipo']:<10} │\n"
            erd += f"└{'─' * 40}┘\n\n"

        # Relacionamentos
        erd += "Relacionamentos:\n"
        for tabela in spec.tabelas:
            for col in tabela["colunas"]:
                if col.get("fk"):
                    ref_table = col["fk"].split("(")[0]
                    erd += f"  {tabela['nome']}.{col['nome']} ──→ {col['fk']}\n"
        erd += "```\n"
        return erd

    def salvar_schema(self, spec: EspecificacaoDB):
        """Salva schema em JSON, SQL e ERD markdown."""
        nome_base = spec.projeto.lower().replace(" ", "_")
        pasta = os.path.join(self.pasta_schemas, nome_base)
        os.makedirs(pasta, exist_ok=True)

        # JSON
        with open(os.path.join(pasta, "schema.json"), "w", encoding="utf-8") as f:
            json.dump(spec.to_dict(), f, ensure_ascii=False, indent=2)

        # SQL Migration
        with open(os.path.join(pasta, "001_initial.sql"), "w", encoding="utf-8") as f:
            f.write("\n".join(spec.migrations))

        # ERD
        erd = self.gerar_erd_texto(spec)
        with open(os.path.join(pasta, "erd.md"), "w", encoding="utf-8") as f:
            f.write(erd)

        self.registrar_log(f"Schema salvo em {pasta}")

    def executar(self):
        """Loop principal: lê projetos e gera schemas de dados."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Arquiteto de Dados iniciado")

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

                tipo = self._inferir_tipo(nome, projeto.get("descricao", ""))
                spec = self.gerar_schema(nome, tipo)
                self.salvar_schema(spec)

                # Notificar Dev Rápido
                self.enviar_mensagem(
                    destinatario="dev_rapido",
                    assunto=f"Schema DB pronto: {nome}",
                    conteudo=(
                        f"Schema de banco de dados pronto para '{nome}'.\n"
                        f"**Engine:** {spec.engine}\n"
                        f"**Tabelas:** {len(spec.tabelas)}\n"
                        f"**Arquivos em:** projetos_ativos/schemas/{nome.lower().replace(' ', '_')}/\n"
                        f"Migration SQL: 001_initial.sql\n"
                    ),
                )
                projetos_processados += 1

        self.atualizar_status("concluido")
        self.registrar_log("Arquiteto finalizado", f"{projetos_processados} schemas gerados")
        return projetos_processados

    def _inferir_tipo(self, nome: str, descricao: str) -> str:
        """Infere tipo de produto para selecionar schema adequado."""
        texto = (nome + " " + descricao).lower()
        if any(kw in texto for kw in ["whatsapp", "zap", "chat", "bot"]):
            return "chatbot_whatsapp"
        if any(kw in texto for kw in ["marketplace", "loja", "empreitaja", "preço"]):
            return "marketplace"
        return "saas_b2b"


# --- Execução direta ---
if __name__ == "__main__":
    agente = ArquitetoDados()
    print(f"Iniciando {agente}")
    resultado = agente.executar()
    print(f"Concluído: {resultado} schemas gerados.")
