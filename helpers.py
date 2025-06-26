from config import engine, inspector, ENABLE_SERVER_SQL_EXEC
from decimal import Decimal
from sqlalchemy import text
from static_schema import static_schema

def execute_database_query(query: str):
    """Execute SQL via SQLAlchemy and return (list_of_dicts, row_count).

    When ENABLE_SERVER_SQL_EXEC is False the function raises immediately so that
    upstream callers can decide how to handle the situation (usually by
    returning the SQL back to the client for local execution).
    """
    if not ENABLE_SERVER_SQL_EXEC:
        raise Exception("Server-side SQL execution is disabled (ENABLE_SERVER_SQL_EXEC=false).")

    try:
        with engine.connect() as conn:
            result_proxy = conn.execute(text(query))
            columns = list(result_proxy.keys())
            # Provide fallback names for unnamed columns (e.g., COUNT(*))
            cleaned_columns: list[str] = []
            for idx, col in enumerate(columns):
                if col and str(col).strip():
                    cleaned_columns.append(str(col))
                else:
                    cleaned_columns.append("value" if len(columns) == 1 else f"col_{idx}")
            columns = cleaned_columns
            rows = result_proxy.fetchall()

        records: list[dict] = []
        for row in rows:
            row_dict = {
                col: (float(val) if isinstance(val, Decimal) else val)
                for col, val in zip(columns, row)
            }
            records.append(row_dict)
        return records, len(records)
    except Exception as e:
        raise Exception(f"Database query failed: {str(e)}")

def get_database_schema():
    """Return a textual representation of the schema.

    Behaviour depends on deployment mode:

    • ENABLE_SERVER_SQL_EXEC=True  → Introspect the live DB (legacy behaviour)
    • ENABLE_SERVER_SQL_EXEC=False → Load pre-generated schema from SCHEMA_PATH
    """

    # Remote execution – still have DB connection
    if ENABLE_SERVER_SQL_EXEC and inspector is not None:
        lines = ["Database Schema:\n"]
        for table in inspector.get_table_names():
            lines.append(f"Table: {table}")
            for col in inspector.get_columns(table):
                lines.append(f"- {col['name']} ({col['type']})")
            lines.append("")  # blank line between tables
        return "\n".join(lines)
    
    if not ENABLE_SERVER_SQL_EXEC and inspector is None:
        return static_schema

    # Fallback
    return "Schema information unavailable (server has no DB access and SCHEMA_PATH not set)."