"""Check the LangChain packages used by the examples in this folder."""

from importlib import import_module


def package_version(package_name: str) -> str:
    """Return a package version without failing when it is unavailable."""
    try:
        package = import_module(package_name)
    except ImportError:
        return "not installed"
    return getattr(package, "__version__", "installed")


def main() -> None:
    for package_name in ("langchain", "langchain_core", "langgraph"):
        print(f"{package_name:<14} {package_version(package_name)}")

    print("\nInstall the examples' dependencies with:")
    print("  pip install langchain langgraph langchain-groq")


if __name__ == "__main__":
    main()
