"""Use a fake chat model locally, then swap it for a hosted model."""

import os


def fake_model_demo() -> None:
    """Demonstrate the standard chat-model interface without an API key."""
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    model = FakeListChatModel(responses=["Paris is the capital of France."])
    response = model.invoke("What is the capital of France?")
    print(f"Fake model: {response.content}")


def groq_model_demo() -> None:
    """Call Groq when GROQ_API_KEY is configured in the environment."""
    from langchain_groq import ChatGroq

    if not os.getenv("GROQ_API_KEY"):
        print("Skipping Groq: set GROQ_API_KEY to run the live example.")
        return

    model = ChatGroq(model="qwen/qwen3.8-27b", temperature=0)
    response = model.invoke("What is the capital of Pakistan?")
    print(f"Groq model: {response.content}")


if __name__ == "__main__":
    try:
        fake_model_demo()
        groq_model_demo()
    except ImportError as exc:
        print(f"Install the required LangChain package first: {exc}")
