"""Reusable prompts, conversation history, and few-shot examples."""


def print_messages(prompt_value) -> None:
    for message in prompt_value.messages:
        print(f"[{message.type:6}] {message.content}")


def main() -> None:
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a {style} assistant specialising in {domain}."),
        ("human", "{question}"),
    ])
    print(f"Variables: {prompt.input_variables}")
    print_messages(prompt.invoke({
        "style": "concise",
        "domain": "geography",
        "question": "What is the capital of Egypt?",
    }))

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ])
    print("\nWith history:")
    print_messages(chat_prompt.invoke({
        "history": [
            HumanMessage(content="My name is Muhammad."),
            AIMessage(content="Nice to meet you, Muhammad."),
        ],
        "question": "What is my name?",
    }))

    few_shot = ChatPromptTemplate.from_messages([
        ("system", "Classify sentiment as positive, negative, or neutral."),
        ("human", "The food was incredible."),
        ("ai", "positive"),
        ("human", "It arrived broken."),
        ("ai", "negative"),
        ("human", "{text}"),
    ])
    print(f"\nFew-shot variables: {few_shot.input_variables}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
