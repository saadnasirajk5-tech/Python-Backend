"""Compare a small keyword retriever with an LCEL RAG chain."""


def main() -> None:
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    class KeywordRetriever(BaseRetriever):
        documents: list[Document]
        k: int = 2

        def _get_relevant_documents(self, query: str, *, run_manager=None):
            query_words = set(query.lower().split())
            ranked = sorted(
                self.documents,
                key=lambda doc: len(query_words & set(doc.page_content.lower().split())),
                reverse=True,
            )
            return ranked[: self.k]

    documents = [
        Document("The terminal costs $499.", {"source": "pricing.md"}),
        Document("The terminal has a 3-year warranty.", {"source": "support.md"}),
        Document("Traffic is encrypted with AES-256.", {"source": "security.md"}),
    ]
    retriever = KeywordRetriever(documents=documents)
    model = FakeListChatModel(responses=["The terminal costs $499."])

    def format_documents(found: list[Document]) -> str:
        return "\n\n".join(f"[{doc.metadata['source']}] {doc.page_content}" for doc in found)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer only from this context:\n{context}"),
        ("human", "{question}"),
    ])
    chain = (
        {"context": retriever | format_documents, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    print(chain.invoke("What does the terminal cost?"))


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
