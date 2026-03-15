"""
AGENTE ESTUDANTE — Squad 5: Automação & Aprendizado
Lê materiais do Ronald (Discord, Chrome bookmarks, cursos Eduzz) e alimenta
a base de conhecimento RAG em /inteligencia/.

Fontes suportadas:
- Discord: exportações JSON/CSV de canais
- Chrome: bookmarks exportados (HTML/JSON)
- Eduzz/Cursos: PDFs, textos, transcrições
- Arquivos locais: .md, .txt, .pdf, .json, .csv
"""

import os
import sys
import json
import csv
import re
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agente import BaseAgente, INTELIGENCIA_DIR, NEXUS_ROOT


# ---------------------------------------------------------------------------
# Configuração de Fontes
# ---------------------------------------------------------------------------

FONTES_CONFIG = {
    "discord": {
        "pasta_input": os.path.join(INTELIGENCIA_DIR, "discord_resumos"),
        "extensoes": [".json", ".csv", ".txt", ".md"],
        "chunk_size": 150,  # tokens menores para chat
        "descricao": "Mensagens e técnicas de trade do Discord do Ronald",
    },
    "cursos": {
        "pasta_input": os.path.join(INTELIGENCIA_DIR, "cursos_resumos"),
        "extensoes": [".md", ".txt", ".pdf", ".json"],
        "chunk_size": 400,  # tokens maiores para conteúdo educacional
        "descricao": "Materiais de cursos Eduzz e treinamentos",
    },
    "chrome": {
        "pasta_input": os.path.join(INTELIGENCIA_DIR, "chrome_bookmarks"),
        "extensoes": [".html", ".json", ".md"],
        "chunk_size": 300,
        "descricao": "Bookmarks e páginas salvas do Chrome",
    },
    "base_conhecimento": {
        "pasta_input": os.path.join(INTELIGENCIA_DIR, "base_conhecimento"),
        "extensoes": [".md", ".txt", ".json", ".csv"],
        "chunk_size": 400,
        "descricao": "Base de conhecimento geral do ecossistema",
    },
}


# ---------------------------------------------------------------------------
# Estruturas de Dados
# ---------------------------------------------------------------------------

@dataclass
class Documento:
    """Documento extraído de uma fonte."""
    id: str
    fonte: str
    titulo: str
    conteudo: str
    metadata: dict = field(default_factory=dict)
    data_extracao: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Chunk:
    """Pedaço de texto pronto para embedding."""
    id: str
    doc_id: str
    texto: str
    fonte: str
    posicao: int
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResumoFonte:
    """Resumo do processamento de uma fonte."""
    fonte: str
    arquivos_lidos: int = 0
    documentos_extraidos: int = 0
    chunks_gerados: int = 0
    erros: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Extratores por Tipo de Arquivo
# ---------------------------------------------------------------------------

class Extrator:
    """Extrai texto de diferentes formatos de arquivo."""

    @staticmethod
    def extrair(caminho: str) -> str:
        """Extrai texto de um arquivo baseado na extensão."""
        ext = Path(caminho).suffix.lower()
        extractors = {
            ".txt": Extrator._extrair_texto,
            ".md": Extrator._extrair_texto,
            ".json": Extrator._extrair_json,
            ".csv": Extrator._extrair_csv,
            ".html": Extrator._extrair_html,
        }
        extractor = extractors.get(ext, Extrator._extrair_texto)
        return extractor(caminho)

    @staticmethod
    def _extrair_texto(caminho: str) -> str:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _extrair_json(caminho: str) -> str:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        # Discord export format
        if isinstance(data, list):
            textos = []
            for item in data:
                if isinstance(item, dict):
                    # Discord message format
                    autor = item.get("author", item.get("username", ""))
                    conteudo = item.get("content", item.get("text", item.get("message", "")))
                    timestamp = item.get("timestamp", item.get("date", ""))
                    if conteudo:
                        textos.append(f"[{timestamp}] {autor}: {conteudo}")
                elif isinstance(item, str):
                    textos.append(item)
            return "\n".join(textos)
        elif isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False, indent=2)
        return str(data)

    @staticmethod
    def _extrair_csv(caminho: str) -> str:
        textos = []
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Discord CSV format: Author, Date, Content
                conteudo = row.get("Content", row.get("content", row.get("message", "")))
                autor = row.get("Author", row.get("author", ""))
                if conteudo:
                    if autor:
                        textos.append(f"{autor}: {conteudo}")
                    else:
                        textos.append(conteudo)
        return "\n".join(textos)

    @staticmethod
    def _extrair_html(caminho: str) -> str:
        """Extrai texto de HTML (Chrome bookmarks, etc)."""
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        # Strip HTML tags
        texto = re.sub(r"<[^>]+>", " ", html)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

class Chunker:
    """Divide documentos em chunks para embedding."""

    @staticmethod
    def chunk_texto(texto: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
        """
        Divide texto em chunks por contagem aproximada de tokens (palavras).
        Overlap garante contexto entre chunks adjacentes.
        """
        palavras = texto.split()
        if len(palavras) <= chunk_size:
            return [texto] if texto.strip() else []

        chunks = []
        inicio = 0
        while inicio < len(palavras):
            fim = min(inicio + chunk_size, len(palavras))
            chunk = " ".join(palavras[inicio:fim])
            if chunk.strip():
                chunks.append(chunk)
            inicio += chunk_size - overlap

        return chunks

    @staticmethod
    def chunk_por_paragrafos(texto: str, max_size: int = 400) -> list[str]:
        """Divide por parágrafos, agrupando parágrafos pequenos."""
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        chunks = []
        buffer = ""

        for p in paragrafos:
            palavras_p = len(p.split())
            palavras_buf = len(buffer.split()) if buffer else 0

            if palavras_buf + palavras_p <= max_size:
                buffer = f"{buffer}\n\n{p}" if buffer else p
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = p

        if buffer:
            chunks.append(buffer)

        return chunks


# ---------------------------------------------------------------------------
# Agente Estudante
# ---------------------------------------------------------------------------

class AgenteEstudante(BaseAgente):
    """Agente que lê materiais do Ronald e alimenta a base de conhecimento RAG."""

    def __init__(self):
        super().__init__(
            nome="Agente Estudante",
            squad="Squad 5 — Automação & Aprendizado",
            papel="Lê Discord/Chrome/Eduzz do Ronald e alimenta base RAG",
        )
        self.pasta_rag = os.path.join(INTELIGENCIA_DIR, "rag_store")
        self.pasta_docs = os.path.join(self.pasta_rag, "documentos")
        self.pasta_chunks = os.path.join(self.pasta_rag, "chunks")
        self.pasta_indice = os.path.join(self.pasta_rag, "indice")
        os.makedirs(self.pasta_docs, exist_ok=True)
        os.makedirs(self.pasta_chunks, exist_ok=True)
        os.makedirs(self.pasta_indice, exist_ok=True)

        self.catalogo_path = os.path.join(self.pasta_rag, "catalogo.json")
        self.catalogo = self._carregar_catalogo()

    def _carregar_catalogo(self) -> dict:
        """Carrega catálogo de documentos já processados."""
        if os.path.exists(self.catalogo_path):
            with open(self.catalogo_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"documentos": {}, "ultima_atualizacao": ""}

    def _salvar_catalogo(self):
        """Persiste catálogo."""
        self.catalogo["ultima_atualizacao"] = datetime.now().isoformat()
        with open(self.catalogo_path, "w", encoding="utf-8") as f:
            json.dump(self.catalogo, f, ensure_ascii=False, indent=2)

    def _hash_arquivo(self, caminho: str) -> str:
        """Gera hash de um arquivo para detectar mudanças."""
        with open(caminho, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def escanear_fonte(self, fonte_id: str) -> list[str]:
        """Escaneia uma fonte e retorna lista de arquivos novos ou modificados."""
        config = FONTES_CONFIG.get(fonte_id)
        if not config:
            return []

        pasta = config["pasta_input"]
        if not os.path.exists(pasta):
            os.makedirs(pasta, exist_ok=True)
            return []

        arquivos_novos = []
        for root, _, files in os.walk(pasta):
            for f in files:
                if any(f.lower().endswith(ext) for ext in config["extensoes"]):
                    caminho = os.path.join(root, f)
                    file_hash = self._hash_arquivo(caminho)

                    # Só processar se novo ou modificado
                    doc_id = f"{fonte_id}:{os.path.relpath(caminho, pasta)}"
                    if doc_id not in self.catalogo["documentos"] or \
                       self.catalogo["documentos"][doc_id].get("hash") != file_hash:
                        arquivos_novos.append(caminho)

        return arquivos_novos

    def processar_arquivo(self, caminho: str, fonte_id: str) -> tuple[Documento, list[Chunk]]:
        """Extrai texto, cria documento e gera chunks."""
        config = FONTES_CONFIG[fonte_id]
        nome_arquivo = os.path.basename(caminho)
        rel_path = os.path.relpath(caminho, config["pasta_input"])

        # Extrair texto
        texto = Extrator.extrair(caminho)
        if not texto.strip():
            return None, []

        # Criar documento
        doc_id = hashlib.md5(f"{fonte_id}:{rel_path}".encode()).hexdigest()[:12]
        doc = Documento(
            id=doc_id,
            fonte=fonte_id,
            titulo=nome_arquivo,
            conteudo=texto,
            metadata={
                "caminho_original": caminho,
                "rel_path": rel_path,
                "tamanho_bytes": os.path.getsize(caminho),
                "palavras": len(texto.split()),
            },
        )

        # Gerar chunks
        chunk_size = config["chunk_size"]
        if fonte_id == "discord":
            # Discord: chunk por parágrafos/mensagens
            textos_chunk = Chunker.chunk_por_paragrafos(texto, max_size=chunk_size)
        else:
            textos_chunk = Chunker.chunk_texto(texto, chunk_size=chunk_size, overlap=50)

        chunks = []
        for i, chunk_texto in enumerate(textos_chunk):
            chunk_id = f"{doc_id}_c{i:04d}"
            chunk = Chunk(
                id=chunk_id,
                doc_id=doc_id,
                texto=chunk_texto,
                fonte=fonte_id,
                posicao=i,
                metadata={
                    "titulo_doc": nome_arquivo,
                    "total_chunks": len(textos_chunk),
                },
            )
            chunks.append(chunk)

        return doc, chunks

    def processar_fonte(self, fonte_id: str) -> ResumoFonte:
        """Processa todos os arquivos novos/modificados de uma fonte."""
        resumo = ResumoFonte(fonte=fonte_id)
        config = FONTES_CONFIG.get(fonte_id)
        if not config:
            resumo.erros.append(f"Fonte desconhecida: {fonte_id}")
            return resumo

        self.registrar_log(f"Processando fonte: {fonte_id}", config["descricao"])

        arquivos = self.escanear_fonte(fonte_id)
        resumo.arquivos_lidos = len(arquivos)

        if not arquivos:
            self.registrar_log(f"Fonte {fonte_id}: nenhum arquivo novo")
            return resumo

        todos_chunks = []
        for caminho in arquivos:
            try:
                doc, chunks = self.processar_arquivo(caminho, fonte_id)
                if doc is None:
                    continue

                # Salvar documento
                doc_path = os.path.join(self.pasta_docs, f"{doc.id}.json")
                with open(doc_path, "w", encoding="utf-8") as f:
                    json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)

                # Registrar no catálogo
                rel_path = os.path.relpath(caminho, config["pasta_input"])
                cat_id = f"{fonte_id}:{rel_path}"
                self.catalogo["documentos"][cat_id] = {
                    "doc_id": doc.id,
                    "hash": self._hash_arquivo(caminho),
                    "chunks": len(chunks),
                    "palavras": doc.metadata.get("palavras", 0),
                    "processado_em": datetime.now().isoformat(),
                }

                todos_chunks.extend(chunks)
                resumo.documentos_extraidos += 1

            except Exception as e:
                resumo.erros.append(f"{caminho}: {str(e)}")
                self.registrar_log(f"Erro processando {caminho}", str(e))

        # Salvar chunks em batch
        if todos_chunks:
            agora = datetime.now().strftime("%Y%m%d_%H%M%S")
            chunks_path = os.path.join(self.pasta_chunks, f"{fonte_id}_{agora}.json")
            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in todos_chunks], f, ensure_ascii=False, indent=2)
            resumo.chunks_gerados = len(todos_chunks)

        self.registrar_log(
            f"Fonte {fonte_id} processada",
            f"{resumo.documentos_extraidos} docs, {resumo.chunks_gerados} chunks",
        )
        return resumo

    def construir_indice_busca(self):
        """
        Constrói índice de busca local (keyword-based).
        Fase 1: índice invertido simples para busca por palavras-chave.
        Fase 2+: ChromaDB/FAISS com embeddings para busca semântica.
        """
        self.registrar_log("Construindo índice de busca")
        indice = {}  # palavra -> [(chunk_id, score)]

        # Ler todos os chunks
        for arquivo in os.listdir(self.pasta_chunks):
            if not arquivo.endswith(".json"):
                continue
            caminho = os.path.join(self.pasta_chunks, arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            for chunk in chunks:
                palavras = set(chunk["texto"].lower().split())
                # Remover stopwords básicas em PT
                stopwords = {
                    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para",
                    "é", "com", "não", "uma", "os", "no", "se", "na", "por",
                    "mais", "as", "dos", "como", "mas", "foi", "ao", "ele",
                    "das", "tem", "à", "seu", "sua", "ou", "ser", "quando",
                }
                palavras_uteis = palavras - stopwords
                for palavra in palavras_uteis:
                    # Limpar pontuação
                    palavra_limpa = re.sub(r"[^\w]", "", palavra)
                    if len(palavra_limpa) >= 3:
                        if palavra_limpa not in indice:
                            indice[palavra_limpa] = []
                        indice[palavra_limpa].append(chunk["id"])

        # Salvar índice
        indice_path = os.path.join(self.pasta_indice, "indice_invertido.json")
        with open(indice_path, "w", encoding="utf-8") as f:
            json.dump(indice, f, ensure_ascii=False)

        self.registrar_log(
            "Índice construído",
            f"{len(indice)} termos indexados",
        )
        return len(indice)

    def buscar(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Busca keyword-based no índice.
        Retorna top_k chunks mais relevantes.
        """
        indice_path = os.path.join(self.pasta_indice, "indice_invertido.json")
        if not os.path.exists(indice_path):
            return []

        with open(indice_path, "r", encoding="utf-8") as f:
            indice = json.load(f)

        # Tokenizar query
        palavras = set(re.sub(r"[^\w\s]", "", query.lower()).split())
        chunk_scores = {}

        for palavra in palavras:
            if palavra in indice:
                for chunk_id in indice[palavra]:
                    chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + 1

        # Rankear por score
        ranked = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Buscar texto dos chunks
        resultados = []
        chunks_cache = {}
        for arquivo in os.listdir(self.pasta_chunks):
            if arquivo.endswith(".json"):
                with open(os.path.join(self.pasta_chunks, arquivo), "r", encoding="utf-8") as f:
                    for chunk in json.load(f):
                        chunks_cache[chunk["id"]] = chunk

        for chunk_id, score in ranked:
            if chunk_id in chunks_cache:
                c = chunks_cache[chunk_id]
                resultados.append({
                    "chunk_id": chunk_id,
                    "texto": c["texto"][:500],
                    "fonte": c["fonte"],
                    "score": score,
                    "metadata": c.get("metadata", {}),
                })

        return resultados

    def gerar_relatorio(self, resumos: list[ResumoFonte]) -> str:
        """Gera relatório de processamento."""
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        total_docs = sum(r.documentos_extraidos for r in resumos)
        total_chunks = sum(r.chunks_gerados for r in resumos)
        total_erros = sum(len(r.erros) for r in resumos)

        md = (
            f"# Relatório Agente Estudante\n"
            f"**Data:** {agora}\n"
            f"**Documentos processados:** {total_docs}\n"
            f"**Chunks gerados:** {total_chunks}\n"
            f"**Erros:** {total_erros}\n\n"
        )

        for r in resumos:
            status = "OK" if not r.erros else f"{len(r.erros)} erros"
            md += (
                f"## Fonte: {r.fonte}\n"
                f"- Arquivos escaneados: {r.arquivos_lidos}\n"
                f"- Documentos extraídos: {r.documentos_extraidos}\n"
                f"- Chunks gerados: {r.chunks_gerados}\n"
                f"- Status: {status}\n"
            )
            if r.erros:
                md += "- Erros:\n"
                for e in r.erros:
                    md += f"  - {e}\n"
            md += "\n"

        cat = self.catalogo
        md += (
            f"## Base RAG\n"
            f"- Total documentos no catálogo: {len(cat['documentos'])}\n"
            f"- Última atualização: {cat.get('ultima_atualizacao', 'nunca')}\n"
            f"- Pasta: {self.pasta_rag}\n"
        )
        return md

    def executar(self):
        """Loop principal: escaneia todas as fontes, processa e constrói índice."""
        self.atualizar_status("em_execucao")
        self.registrar_log("Agente Estudante iniciado", "Escaneando todas as fontes")

        resumos = []
        for fonte_id in FONTES_CONFIG:
            resumo = self.processar_fonte(fonte_id)
            resumos.append(resumo)

        # Construir índice de busca
        total_chunks = sum(r.chunks_gerados for r in resumos)
        if total_chunks > 0:
            termos = self.construir_indice_busca()
            self.registrar_log("Índice de busca atualizado", f"{termos} termos")
        else:
            self.registrar_log("Nenhum chunk novo", "Índice não atualizado")

        # Salvar catálogo
        self._salvar_catalogo()

        # Gerar e publicar relatório
        relatorio = self.gerar_relatorio(resumos)
        self.publicar_resultado("Processamento Agente Estudante", relatorio)

        self.atualizar_status("concluido")
        total_docs = sum(r.documentos_extraidos for r in resumos)
        self.registrar_log(
            "Agente Estudante finalizado",
            f"{total_docs} docs processados, {total_chunks} chunks gerados",
        )
        return resumos


# --- Execução direta ---
if __name__ == "__main__":
    agente = AgenteEstudante()
    print(f"Iniciando {agente}")
    resumos = agente.executar()
    for r in resumos:
        print(f"  {r.fonte}: {r.documentos_extraidos} docs, {r.chunks_gerados} chunks")
    print("Concluído.")
