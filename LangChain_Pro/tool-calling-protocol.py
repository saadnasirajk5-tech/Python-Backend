"""Show the message loop that LangChain agents automate."""


def main() -> None:
    from langchain_core.messages import AIMessage, ToolMessage
    from langchain_core.tools import tool

    @tool
    def get_weather(city: str) -> str:
        """Return demo weather data."""
        return {"paris": "15 C and cloudy"}.get(city.lower(), "unknown")

    response = AIMessage(
        content="",
        tool_calls=[{"name": "get_weather", "args": {"city": "Paris"}, "id": "call_1"}],
    )
    call = response.tool_calls[0]
    registry = {get_weather.name: get_weather}
    result = registry[call["name"]].invoke(call["args"])
    tool_message = ToolMessage(content=result, tool_call_id=call["id"])

    print("1. The model returns a tool call:", response.tool_calls)
    print("2. The application runs the tool:", result)
    print("3. The application sends back:", tool_message)
    print("4. The model uses the tool result to write the final answer.")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
