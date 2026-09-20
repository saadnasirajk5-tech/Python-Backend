# ChromaDB Notes

ChromaDB is a local-first vector database for storing text and finding semantically similar content. In a LangChain RAG application, it usually replaces a toy keyword retriever while keeping the same retriever interface.

## Install

```bash
pip install chromadb langchain-chroma langchain-openai langchain-text-splitters
```

## Core workflow

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="orbital_kb")

collection.upsert(
    ids=["pricing", "support", "security"],
    documents=[
        "The Orbital Link terminal costs $499 for consumers.",
        "The terminal has a 3-year limited warranty.",
        "Traffic is encrypted with AES-256.",
    ],
    metadatas=[
        {"source": "pricing.md", "section": "hardware"},
        {"source": "support.md", "section": "warranty"},
        {"source": "security.md", "section": "encryption"},
    ],
)

results = collection.query(
    query_texts=["What does the terminal cost?"],
    n_results=2,
)

for document, metadata, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0],
):
    print(f"[{metadata['source']}] {distance:.3f}: {document}")
```

`PersistentClient` keeps data between runs. `Client()` is useful for disposable tests, while `HttpClient` connects to a separately hosted Chroma server.

## LangChain integration

```python
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

vector_store = Chroma(
    collection_name="orbital_kb",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    persist_directory="./chroma_db",
)

documents = [
    Document("The terminal costs $499.", {"source": "pricing.md"}),
    Document("The terminal has a 3-year warranty.", {"source": "support.md"}),
]
vector_store.add_documents(documents, ids=["pricing", "support"])

retriever = vector_store.as_retriever(search_kwargs={"k": 2})
matching_documents = retriever.invoke("What does the terminal cost?")
```

The important replacement is `KeywordRetriever(...)` with `vector_store.as_retriever(...)`. The rest of an LCEL RAG chain can remain unchanged.

## Embeddings

Chroma needs an embedding function. Its default local embedding function is convenient for experimentation. In production, configure a model explicitly so the embedding choice is stable across environments, for example `OpenAIEmbeddings` or a local Hugging Face model.

## Practical rules

- Split long documents before indexing. `RecursiveCharacterTextSplitter` is a good starting point.
- Use stable IDs and `upsert` when a script may run more than once.
- Filter by metadata when a query should search only one tenant, product, or document section: `where={"section": "warranty"}`.
- Keep `chroma_db/` out of source control because it is generated application data.
- Choose the distance metric and embedding model together; do not change either casually after indexing.
- Treat retrieval as one stage of RAG: retrieve, format context, prompt the model, then cite sources in the answer.
