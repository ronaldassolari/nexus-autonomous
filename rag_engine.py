"""
RAG ENGINE — Nexus Autonomous
Motor de Retrieval-Augmented Generation local.
Fase 1: índice invertido (keyword-based) + busca por similaridade simples.
Fase 2+: ChromaDB/FAISS com embeddings para busca semântica real.

Uso:
    from rag_engine import RAGEngine
    rag = RAGEngine()
    rag.ingerir_texto("trade", "Conteúdo sobre técnicas de trade...")
    resultados = rag.buscar("como operar mini-índice")
"""

import os
import sys
import json
import re
import math
import hashlib
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, field

NEXUS_ROOT = os.path.dirname(os.path.abspath(__file__))
RAG_STORE = os.path.join(NEXUS_ROOT, "inteligencia", "rag_store")


# ---------------------------------------------------------------------------
# TF-IDF simples para ranking sem dependências externas
# ---------------------------------------------------------------------------

class TFIDF:
    """Implementação leve de TF-IDF para ranking de chunks."""

    STOPWORDS_PT = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para",
        "é", "com", "não", "uma", "os", "no", "se", "na", "por",
        "mais", "as", "dos", "como", "mas", "foi", "ao", "ele",
        "das", "tem", "à", "seu", "sua", "ou", "ser", "quando",
        "muito", "há", "nos", "já", "eu", "também", "só", "pelo",
        "pela", "até", "isso", "ela", "entre", "era", "depois",
        "sem", "mesmo", "aos", "ter", "seus", "quem", "nas", "me",
        "esse", "eles", "estão", "você", "tinha", "foram", "essa",
        "num", "nem", "suas", "meu", "às", "minha", "têm", "numa",
        "the", "is", "a", "an", "and", "or", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "it", "this",
    }

    @staticmethod
    def tokenize(texto: str) -> list[str]:
        """Tokeniza texto removendo pontuação e stopwords."""
        palavras = re.findall(r"\w{3,}", texto.lower())
        return [p for p in palavras if p not in TFIDF.STOPWORDS_PT]

    @staticmethod
    def tf(termo: str, documento: list[str]) -> float:
        """Term Frequency."""
        if not documento:
            return 0.0
        return documento.count(termo) / len(documento)

    @staticmethod
    def idf(termo: str, corpus: list[list[str]]) -> float:
        """Inverse Document Frequency."""
        n_docs = len(corpus)
        if n_docs == 0:
            return 0.0
        docs_com_termo = sum(1 for doc in corpus if termo in doc)
        if docs_com_termo == 0:
            return 0.0
        return math.log(n_docs / docs_com_termo)

    @staticmethod
    def tfidf_score(query_tokens: list[str], doc_tokens: list[str], corpus: list[list[str]]) -> float:
        """Calcula score TF-IDF de um documento em relação a uma query."""
        score = 0.0
        for termo in query_tokens:
            score += TFIDF.tf(termo, doc_tokens) * TFIDF.idf(termo, corpus)
        return score


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------

@dataclass
class ChunkRAG:
    """Chunk armazenado na base RAG."""
    id: str
    texto: str
    fonte: str
    categoria: str
    tokens: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "texto": self.texto,
            "fonte": self.fonte,
            "categoria": self.categoria,
            "metadata": self.metadata,
        }


class RAGEngine:
    """
    Motor RAG local para o ecossistema Nexus Autonomous.

    Fase 1: TF-IDF keyword ranking (zero dependências externas).
    Fase 2: ChromaDB com embeddings (requer: pip install chromadb).
    """

    def __init__(self, store_path: str = RAG_STORE):
        self.store_path = store_path
        self.chunks_path = os.path.join(store_path, "rag_chunks.json")
        self.stats_path = os.path.join(store_path, "rag_stats.json")
        os.makedirs(store_path, exist_ok=True)
        self.chunks: list[ChunkRAG] = []
        self._carregar()

    def _carregar(self):
        """Carrega chunks da base persistida."""
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = [
                ChunkRAG(
                    id=c["id"],
                    texto=c["texto"],
                    fonte=c["fonte"],
                    categoria=c.get("categoria", "geral"),
                    tokens=TFIDF.tokenize(c["texto"]),
                    metadata=c.get("metadata", {}),
                )
                for c in data
            ]

    def _salvar(self):
        """Persiste chunks no disco."""
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.chunks], f, ensure_ascii=False, indent=2)
        self._salvar_stats()

    def _salvar_stats(self):
        """Salva estatísticas da base RAG."""
        categorias = Counter(c.categoria for c in self.chunks)
        fontes = Counter(c.fonte for c in self.chunks)
        stats = {
            "total_chunks": len(self.chunks),
            "total_tokens": sum(len(c.tokens) for c in self.chunks),
            "categorias": dict(categorias),
            "fontes": dict(fontes),
            "ultima_atualizacao": datetime.now().isoformat(),
        }
        with open(self.stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    def ingerir_texto(
        self,
        categoria: str,
        texto: str,
        fonte: str = "manual",
        metadata: dict = None,
        chunk_size: int = 400,
        overlap: int = 50,
    ) -> int:
        """
        Ingere texto na base RAG: chunka, tokeniza e persiste.
        Retorna número de chunks criados.
        """
        if not texto.strip():
            return 0

        palavras = texto.split()
        chunks_texto = []
        inicio = 0
        while inicio < len(palavras):
            fim = min(inicio + chunk_size, len(palavras))
            chunk = " ".join(palavras[inicio:fim])
            if chunk.strip():
                chunks_texto.append(chunk)
            inicio += chunk_size - overlap

        novos = 0
        for i, chunk_texto in enumerate(chunks_texto):
            chunk_id = hashlib.md5(f"{fonte}:{categoria}:{chunk_texto[:100]}:{i}".encode()).hexdigest()[:12]

            # Evitar duplicatas
            if any(c.id == chunk_id for c in self.chunks):
                continue

            chunk = ChunkRAG(
                id=chunk_id,
                texto=chunk_texto,
                fonte=fonte,
                categoria=categoria,
                tokens=TFIDF.tokenize(chunk_texto),
                metadata=metadata or {},
            )
            self.chunks.append(chunk)
            novos += 1

        if novos > 0:
            self._salvar()

        return novos

    def ingerir_arquivo(self, caminho: str, categoria: str, chunk_size: int = 400) -> int:
        """Ingere um arquivo na base RAG."""
        if not os.path.exists(caminho):
            return 0

        ext = os.path.splitext(caminho)[1].lower()
        if ext == ".json":
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            if isinstance(data, list):
                texto = "\n".join(
                    c.get("texto", c.get("content", str(c)))
                    if isinstance(c, dict) else str(c)
                    for c in data
                )
            else:
                texto = json.dumps(data, ensure_ascii=False)
        else:
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()

        return self.ingerir_texto(
            categoria=categoria,
            texto=texto,
            fonte=os.path.basename(caminho),
            metadata={"caminho": caminho},
            chunk_size=chunk_size,
        )

    def buscar(self, query: str, top_k: int = 5, categoria: str = None) -> list[dict]:
        """
        Busca chunks relevantes usando TF-IDF ranking.
        Retorna lista de resultados com score.
        """
        if not self.chunks:
            return []

        query_tokens = TFIDF.tokenize(query)
        if not query_tokens:
            return []

        # Filtrar por categoria se especificada
        candidatos = self.chunks
        if categoria:
            candidatos = [c for c in self.chunks if c.categoria == categoria]

        if not candidatos:
            return []

        # Construir corpus para IDF
        corpus = [c.tokens for c in candidatos]

        # Calcular scores
        resultados = []
        for chunk in candidatos:
            score = TFIDF.tfidf_score(query_tokens, chunk.tokens, corpus)
            if score > 0:
                resultados.append({
                    "chunk_id": chunk.id,
                    "texto": chunk.texto[:500],
                    "fonte": chunk.fonte,
                    "categoria": chunk.categoria,
                    "score": round(score, 4),
                    "metadata": chunk.metadata,
                })

        # Ordenar por score e retornar top_k
        resultados.sort(key=lambda x: x["score"], reverse=True)
        return resultados[:top_k]

    def buscar_por_categoria(self, categoria: str) -> list[dict]:
        """Retorna todos os chunks de uma categoria."""
        return [c.to_dict() for c in self.chunks if c.categoria == categoria]

    def listar_categorias(self) -> dict:
        """Lista categorias e contagem de chunks."""
        return dict(Counter(c.categoria for c in self.chunks))

    def stats(self) -> dict:
        """Retorna estatísticas da base."""
        if os.path.exists(self.stats_path):
            with open(self.stats_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"total_chunks": 0}

    def limpar_categoria(self, categoria: str) -> int:
        """Remove todos os chunks de uma categoria. Retorna quantidade removida."""
        antes = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.categoria != categoria]
        removidos = antes - len(self.chunks)
        if removidos > 0:
            self._salvar()
        return removidos


# ---------------------------------------------------------------------------
# Inicializador da Base de Conhecimento
# ---------------------------------------------------------------------------

def inicializar_base_conhecimento():
    """
    Popula a base RAG com conhecimento inicial do ecossistema Nexus.
    Roda uma vez para criar a base fundacional.
    """
    rag = RAGEngine()

    # --- Conhecimento sobre o ecossistema ---
    conhecimento_nexus = """
    O Nexus Autonomous é um ecossistema de agentes autônomos criado por Ronald Santos Assolari.
    O sistema é composto por 20 agentes organizados em 5 squads:
    Squad 1 Inteligência e Validação: Radar China busca tendências em Douyin WeChat Bilibili,
    Validador de Mercado valida demanda com Google Trends e SEMrush, CEO Agente decide e prioriza.
    Squad 2 Fábrica de Software: UX UI Designer cria wireframes, Arquiteto de Dados define schemas,
    Dev Rápido constrói MVPs em 24-48h, QA Segurança testa e verifica OWASP, DevOps configura CI CD.
    Squad 3 Marketing e Vendas: Copywriter, Gestor de Tráfego, Especialista Marketplace, Closer.
    Squad 4 Operações Financeiras: CFO, Especialista Cripto, Day Trade, Ações, Opções.
    O Squad 4 opera em modo sugestão até Ronald autorizar modo autônomo após 90 dias de backtesting.
    Squad 5 Automação e Aprendizado: Agente n8n para webhooks, Agente Estudante para base RAG.
    """
    rag.ingerir_texto("nexus_sistema", conhecimento_nexus, "inicializacao")

    # --- Produtos no pipeline ---
    produtos = """
    Produtos em desenvolvimento no ecossistema Nexus Autonomous:
    1. Influencers IA: geração de ebooks com inteligência artificial, monetização via Hotmart e Kiwify.
    2. Agente Viral TikTok: automação de conteúdo viral para TikTok com IA.
    3. ZapIA: SaaS B2B para automação de WhatsApp com chatbots inteligentes.
    4. Buscador de Preços WhatsApp: comparação de preços via chatbot no WhatsApp.
    5. Empreitaja: marketplace de construção civil conectando empreiteiros e clientes.
    Todos os produtos seguem o pipeline: Radar China detecta tendência, Validador confirma demanda,
    CEO Agente aprova, Squad 2 constrói MVP, Squad 3 lança e vende.
    """
    rag.ingerir_texto("nexus_produtos", produtos, "inicializacao")

    # --- Técnicas de trade (placeholder para Discord) ---
    trade_base = """
    Conceitos fundamentais de trade que o Ronald estuda:
    Análise técnica: suporte, resistência, médias móveis, RSI, MACD, volume.
    Operações em mini-índice e mini-dólar no mercado brasileiro B3.
    Day trade: operações intraday com stop loss e take profit definidos.
    Swing trade: operações de dias a semanas baseadas em tendências.
    Criptomoedas: análise de mercado crypto, DeFi, exchanges centralizadas.
    Opções: travas de alta e baixa, venda coberta, butterfly, condor.
    Gestão de risco: nunca arriscar mais de 2 porcento do capital por operação.
    Position sizing: calcular tamanho da posição baseado no risco por trade.
    """
    rag.ingerir_texto("trade", trade_base, "inicializacao", chunk_size=200)

    # --- Marketing digital ---
    marketing = """
    Estratégias de marketing digital do ecossistema:
    Funil de vendas: topo (awareness), meio (consideração), fundo (conversão).
    Tráfego pago: Facebook Ads, Google Ads, TikTok Ads com otimização de ROI.
    Copywriting: headlines magnéticas, storytelling, prova social, urgência, CTA claro.
    Landing pages: above the fold com proposta de valor, benefícios, depoimentos, CTA.
    Marketplaces: Hotmart para infoprodutos, Kiwify como alternativa, App Store para apps.
    WhatsApp marketing: listas de transmissão, chatbots, funil de vendas via WhatsApp.
    SEO: keywords long tail, conteúdo de valor, backlinks, Google Trends para validação.
    """
    rag.ingerir_texto("marketing", marketing, "inicializacao", chunk_size=200)

    # --- Tecnologia e stacks ---
    tech = """
    Stack tecnológica do Nexus Autonomous:
    Backend: Python 3.11+, FastAPI para APIs REST, Django para aplicações full-stack.
    Frontend: React, Next.js, Tailwind CSS, Shadcn UI.
    Banco de dados: PostgreSQL para dados relacionais, MongoDB para documentos.
    Infraestrutura: Docker, Docker Compose, GitHub Actions para CI CD.
    AI e LLMs: Claude API da Anthropic, OpenAI API, modelos locais via Ollama.
    Automação: n8n para webhooks e integração entre sistemas.
    Deploy: Railway, Vercel, AWS para produção.
    Monitoramento: health checks automáticos, logs estruturados, alertas.
    """
    rag.ingerir_texto("tecnologia", tech, "inicializacao", chunk_size=200)

    print(f"Base de conhecimento inicializada: {len(rag.chunks)} chunks")
    print(f"Categorias: {rag.listar_categorias()}")
    return rag


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nexus RAG Engine")
    parser.add_argument("--init", action="store_true", help="Inicializar base de conhecimento")
    parser.add_argument("--buscar", type=str, help="Buscar na base RAG")
    parser.add_argument("--categoria", type=str, help="Filtrar busca por categoria")
    parser.add_argument("--stats", action="store_true", help="Mostrar estatísticas")
    parser.add_argument("--ingerir", type=str, help="Ingerir arquivo na base")
    parser.add_argument("--cat", type=str, default="geral", help="Categoria para ingestão")
    parser.add_argument("--top-k", type=int, default=5, help="Número de resultados")
    args = parser.parse_args()

    if args.init:
        rag = inicializar_base_conhecimento()
    elif args.buscar:
        rag = RAGEngine()
        resultados = rag.buscar(args.buscar, top_k=args.top_k, categoria=args.categoria)
        if resultados:
            for i, r in enumerate(resultados, 1):
                print(f"\n--- Resultado {i} (score: {r['score']}) [{r['categoria']}] ---")
                print(r["texto"][:300])
        else:
            print("Nenhum resultado encontrado.")
    elif args.stats:
        rag = RAGEngine()
        stats = rag.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif args.ingerir:
        rag = RAGEngine()
        n = rag.ingerir_arquivo(args.ingerir, args.cat)
        print(f"{n} chunks ingeridos de {args.ingerir}")
    else:
        parser.print_help()
