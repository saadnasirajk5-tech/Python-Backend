"""Add retries and fallbacks to LangChain runnables."""


def main() -> None:
    from langchain_core.runnables import RunnableLambda

    attempts = {"count": 0}

    def flaky_operation(_: str) -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError(f"temporary failure {attempts['count']}")
        return f"success on attempt {attempts['count']}"

    resilient = RunnableLambda(flaky_operation).with_retry(
        stop_after_attempt=4,
        wait_exponential_jitter=False,
    )
    print(f"retry: {resilient.invoke('input')}")

    primary = RunnableLambda(lambda _: (_ for _ in ()).throw(
        RuntimeError("primary service is unavailable")
    ))
    backup = RunnableLambda(lambda _: "response from the backup")
    print(f"fallback: {primary.with_fallbacks([backup]).invoke('input')}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
