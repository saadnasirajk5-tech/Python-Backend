"""Define typed LangChain tools with small, deterministic implementations."""

import ast
import operator


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def evaluate(expression: str) -> float | int:
    """Evaluate basic arithmetic without executing arbitrary Python."""
    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError("only basic arithmetic is supported")

    return visit(ast.parse(expression, mode="eval").body)


def main() -> None:
    from langchain_core.tools import tool

    @tool
    def get_weather(city: str) -> str:
        """Return demo weather data for a city."""
        weather = {"paris": "15 C and cloudy", "tokyo": "22 C and clear"}
        return weather.get(city.strip().lower(), f"No weather data for {city}")

    @tool
    def calculate(expression: str) -> str:
        """Calculate a basic arithmetic expression."""
        try:
            return str(evaluate(expression))
        except (SyntaxError, ValueError, ZeroDivisionError) as exc:
            return f"Error: {exc}"

    for tool_definition in (get_weather, calculate):
        print(f"{tool_definition.name}: {tool_definition.args}")
    print(get_weather.invoke({"city": "Paris"}))
    print(calculate.invoke({"expression": "23 * 47"}))
    print(calculate.invoke({"expression": "__import__('os')"}))


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-core first: {exc}")
