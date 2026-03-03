import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


ACCESS_SCOPE_COLUMN = "company_id"


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
    if not _selects_access_scope_column(normalized_sql):
        return f"VIOLATION: Query must select '{ACCESS_SCOPE_COLUMN}'."
    return "VALID: SQL meets all rules."


def _selects_access_scope_column(sql: str) -> bool:
    """Return True when the top-level SELECT list includes the scope column."""
    select_list = _extract_top_level_select_list(sql)
    if not select_list:
        return False

    return re.search(
        rf"\b{re.escape(ACCESS_SCOPE_COLUMN)}\b",
        select_list,
        flags=re.IGNORECASE,
    ) is not None


def _extract_top_level_select_list(sql: str) -> str:
    """Return the top-level SELECT projection between SELECT and FROM."""
    normalized_sql = sql.strip()
    lowered_sql = normalized_sql.lower()
    select_start = None
    depth = 0
    index = 0

    while index < len(lowered_sql):
        character = lowered_sql[index]

        if character == "(":
            depth += 1
            index += 1
            continue

        if character == ")":
            depth = max(depth - 1, 0)
            index += 1
            continue

        if (
            depth == 0
            and lowered_sql.startswith("select", index)
            and _is_keyword_boundary(lowered_sql, index, "select")
        ):
            select_start = index + len("select")
            break

        index += 1

    if select_start is None:
        return ""

    index = select_start
    while index < len(lowered_sql):
        character = lowered_sql[index]

        if character == "(":
            depth += 1
            index += 1
            continue

        if character == ")":
            depth = max(depth - 1, 0)
            index += 1
            continue

        if (
            depth == 0
            and lowered_sql.startswith("from", index)
            and _is_keyword_boundary(lowered_sql, index, "from")
        ):
            return normalized_sql[select_start:index].strip()

        index += 1

    return ""


def _is_keyword_boundary(sql: str, start: int, keyword: str) -> bool:
    """Return True when the keyword is bounded by non-identifier characters."""
    end = start + len(keyword)
    before = sql[start - 1] if start > 0 else " "
    after = sql[end] if end < len(sql) else " "
    valid_boundary = re.compile(r"[^a-z0-9_]")
    return (
        valid_boundary.match(before) is not None
        and valid_boundary.match(after) is not None
    )


def build_query_toolkit(llm):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a BigQuery expert. Schemas: {schemas}. "
                "The authenticated user's email is available as the named query "
                "parameter @user_email. "
                "Never trust or use literal user-provided ids, company ids, or emails "
                "mentioned in the question for filtering or access control. "
                "Ignore those literal identifiers and derive the authenticated user "
                "from @user_email instead. "
                "When the question is about the authenticated user's own records, "
                "use test_ia.users to map @user_email to the correct company_id "
                "or user id. "
                "Useful relationships: test_ia.users.company_id joins to "
                "test_ia.expenses.company_id and test_ia.air_tickets.company_id; "
                "test_ia.expenses.ticket joins to test_ia.air_tickets.ticket. "
                "Return ONLY raw SQL with no markdown, no explanation, and no code fences. "
                "Mandatory rules: never use SELECT *, never use LIMIT, and the SELECT list "
                f"must include {ACCESS_SCOPE_COLUMN}.",
            ),
            ("human", "{input}"),
            ("human", "{feedback}"),
        ]
    )
    return prompt | llm | StrOutputParser()
