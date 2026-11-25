import time
from pathlib import Path
from langchain_core.tools import tool
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Resolve paths relative to project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = ROOT_DIR / "data" / "curriculum_docs"
CHROMA_DIR = ROOT_DIR / "data" / "chroma_db"
COLLECTION_NAME = "sprints_curriculum"

# Local embedding model (no API key required, works alongside Groq)
_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
_vectorstore = None


def _get_vectorstore() -> Chroma:
    """Load existing ChromaDB collection or build it from data/document/*.md."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    # If ChromaDB already exists on disk, load it directly (fast startup)
    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()):
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=_embeddings,
            persist_directory=str(CHROMA_DIR),
        )
        return _vectorstore

    # Otherwise, load .md docs from data/document/, chunk (500 / 50), and persist
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Curriculum folder not found at: {DOCS_DIR}")

    loader = DirectoryLoader(
        str(DOCS_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    raw_docs = loader.load()
    if not raw_docs:
        raise ValueError(f"No .md files found inside {DOCS_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(raw_docs)

    _vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )
    return _vectorstore


@tool
def search_sprints_curriculum(query: str) -> str:
    """
    Search the Sprints curriculum and hiring partner knowledge base using ChromaDB semantic search.

    Args:
        query: Natural-language question about Sprints tracks, module prerequisites,
               or Tier-1/Tier-2 hiring partner requirements (e.g., Fawry, InstaPay).

    Returns:
        str: Top matching curriculum excerpts with source metadata and retrieval latency.
    """
    start_time = time.perf_counter()
    try:
        vs = _get_vectorstore()
        results = vs.similarity_search(query, k=3)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if not results:
            return f"No relevant curriculum chunks found for query: '{query}'."

        formatted_chunks = []
        for idx, doc in enumerate(results, start=1):
            source_name = Path(doc.metadata.get("source", "sprints_curriculum.md")).name
            formatted_chunks.append(f"[Chunk {idx} | Source: {source_name}]\n{doc.page_content.strip()}")

        print(f"[RAG Trace] Retrieved {len(results)} chunks in {elapsed_ms:.1f} ms for query: '{query}'")
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        return f"Unable to retrieve curriculum context: {str(e)}"


# Quick standalone test
if __name__ == "__main__":
    print("=== TEST 1: Fawry Partner Requirements ===")
    print(search_sprints_curriculum.invoke({"query": "What modules and score are required for Fawry?"}))

    print("\n=== TEST 2: Module AI-104 Prerequisites ===")
    print(search_sprints_curriculum.invoke({"query": "Prerequisites for Multi-Agent Orchestration AI-104"}))