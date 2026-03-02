import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


def validate_sql_rules(sql: str) -> str:
    normalized_sql = sql.strip()

    if not normalized_sql:
        return "VIOLATION: SQL was empty."
    if not re.match(r"^(SELECT|WITH)\b", normalized_sql, flags=re.IGNORECASE):
        return "VIOLATION: Only a single SELECT query is allowed."
    if ";" in normalized_sql:
        return "VIOLATION: Multiple statements are not allowed."
    if "--" in normalized_sql or "/*" in normalized_sql or "*/" in normalized_sql:
        return "VIOLATION: SQL comments are not allowed."
    if re.search(
        r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|CALL|EXEC|EXECUTE|DECLARE|SET|BEGIN|COMMIT)\b",
        normalized_sql,
        flags=re.IGNORECASE,
    ):
        return "VIOLATION: Only read-only SELECT queries are allowed."
    if re.search(r"\bSELECT\s+\*", normalized_sql, flags=re.IGNORECASE):
        return "VIOLATION: You used 'SELECT *'. Specify exact column names."
    if "LIMIT" in normalized_sql.upper():
        return "VIOLATION: You used 'LIMIT'."
    if "id_empresa" not in normalized_sql.lower():
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
