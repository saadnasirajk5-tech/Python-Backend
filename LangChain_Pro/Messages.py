"""Represent conversation turns with LangChain message objects."""


def main() -> None:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    messages = [
        SystemMessage(content="You are a concise geography tutor."),
        HumanMessage(content="What is the capital of France?"),
        AIMessage(content="Paris."),
        HumanMessage(content="How tall is the Eiffel Tower?"),
    ]

    for message in messages:
        print(f"[{message.type:6}] {message.content}")

    print("\nShorthand forms:")
    print([{"role": "user", "content": "Hello"}])
    print("A plain string is treated as a human message.")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
