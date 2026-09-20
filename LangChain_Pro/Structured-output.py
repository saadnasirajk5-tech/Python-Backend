"""Extract validated support-ticket data from an LLM response."""

import os
from typing import Literal


def main() -> None:
    from pydantic import BaseModel, Field
    from langchain_groq import ChatGroq

    class SupportTicket(BaseModel):
        category: Literal["billing", "technical", "account", "other"] = Field(
            description="Main issue category"
        )
        urgency: Literal["low", "medium", "high", "critical"]
        summary: str = Field(description="One-sentence problem summary")
        order_id: str | None = Field(default=None, description="Order ID, if present")
        requires_human: bool

    if not os.getenv("GROQ_API_KEY"):
        print("Set GROQ_API_KEY to run the live structured-output example.")
        return

    model = ChatGroq(model="qwen/qwen3.8-27b", temperature=0)
    ticket = model.with_structured_output(SupportTicket).invoke(
        "My payment failed for order #4421. It is urgent."
    )
    print(ticket.model_dump_json(indent=2))

    if ticket.urgency == "critical" and ticket.requires_human:
        action = "PAGE ON-CALL ENGINEER"
    elif ticket.category == "billing" and ticket.order_id:
        action = f"AUTO-REFUND {ticket.order_id}"
    else:
        action = "QUEUE FOR STANDARD SUPPORT"
    print(f"Route: {action}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"Install langchain-groq and pydantic first: {exc}")
