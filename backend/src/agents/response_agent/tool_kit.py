from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_response_toolkit(llm):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a data assistant. Database response: {response_data}. "
                "Format the answer clearly and keep it grounded in the returned rows.",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question_text}"),
        ]
    )
    return prompt | llm | StrOutputParser()
