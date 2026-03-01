from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class RouterGuardrail(BaseModel):
    context: Literal["TRAVEL", "EXPENSE", "COMMERCIAL", "SERVICE"] = Field(
        description="The matched business context."
    )


def build_router_toolkit(llm):
    prompt = ChatPromptTemplate.from_template(
        "Classify the user query into exactly one business context: TRAVEL, EXPENSE, "
        "COMMERCIAL, or SERVICE. Return only the structured context.\n"
        "Question: {question_text}"
    )
    return prompt | llm.with_structured_output(RouterGuardrail)
