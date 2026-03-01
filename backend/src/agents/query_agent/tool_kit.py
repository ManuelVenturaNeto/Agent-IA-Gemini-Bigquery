from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


def validate_sql_rules(sql: str) -> str:
    if "*" in sql:
        return "VIOLATION: You used 'SELECT *'. Specify exact column names."
    if "LIMIT" in sql.upper():
        return "VIOLATION: You used 'LIMIT'."
    if "id_empresa" not in sql.lower():
        return "VIOLATION: Query must select 'id_empresa'."
    return "VALID: SQL meets all rules."


def build_query_toolkit(llm):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a BigQuery expert. Schemas: {schemas}. "
                "Return ONLY raw SQL with no markdown, no explanation, and no code fences. "
                "Mandatory rules: never use SELECT *, never use LIMIT, and the SELECT list "
                "must include id_empresa.",
            ),
            ("human", "{input}"),
            ("human", "{feedback}"),
        ]
    )
    return prompt | llm | StrOutputParser()
