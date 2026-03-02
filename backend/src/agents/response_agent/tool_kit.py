from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_response_toolkit(llm):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a data analyst writing a concise natural-language report. "
                "Database response: {response_data}. "
                "Precomputed analytical brief: {analysis_summary}. "
                "Answer the user's question directly, explain what the returned data means, "
                "and keep the explanation grounded in the returned rows. "
                "Write 2 to 4 short paragraphs in prose. "
                "Explicitly cover highlights, insights, averages, mode/frequency, outliers, "
                "and trends whenever the data supports them. "
                "Do not paste the raw rows, JSON, bullet lists, SQL, or field-by-field dumps.",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question_text}"),
        ]
    )
    return prompt | llm | StrOutputParser()
