"""Compose prompts, models, parsers, and runnable branches with LCEL."""


def main() -> None:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableParallel, RunnablePassthrough
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer in one short sentence."),
        ("human", "{question}"),
    ])
    model = FakeListChatModel(responses=["A concise answer."] * 5)
    chain = prompt | model | StrOutputParser()

    print(f"invoke: {chain.invoke({'question': 'What is LCEL?'})}")
    print(f"batch: {chain.batch([{'question': 'Q1'}, {'question': 'Q2'}])}")

    parallel = RunnableParallel(
        answer=chain,
        original=RunnablePassthrough(),
    )
    print(f"parallel: {parallel.invoke({'question': 'What is 2 + 2?'})}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
