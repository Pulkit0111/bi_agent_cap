import os
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from config import embedding_model, ENABLE_SERVER_SQL_EXEC

if not ENABLE_SERVER_SQL_EXEC:
    retriever = None
else:
    from config import db, engine, inspector

def get_table_schema_from_uri(table_name: str):
    """Return detailed schema info and sample rows for a table."""
    try:
        cols_info = inspector.get_columns(table_name)
        parsed_columns = [
            {
                "column_name": col["name"],
                "data_type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
            }
            for col in cols_info
        ]

        # Grab a few sample rows (dialect aware)
        try:
            if engine.dialect.name.lower() in ("mssql", "microsoft sql server"):
                sample_rows = db.run(f"SELECT TOP 3 * FROM {table_name}")
            else:
                sample_rows = db.run(f"SELECT * FROM {table_name} LIMIT 3")
        except Exception:
            sample_rows = []

        return {
            "table_name": table_name,
            "columns": parsed_columns,
            "sample_data": sample_rows,
        }
    except Exception as e:
        print(f"Warning: Error getting schema for {table_name}: {e}")
        return None

# Build or load a FAISS index over the table schemas so we can RAG the schema text
INDEX_PATH = "faiss_schema_index"

if os.path.exists(INDEX_PATH):
    try:
        vector_index = FAISS.load_local(
            INDEX_PATH,
            embedding_model,
            allow_dangerous_deserialization=True,  # Index created locally and trusted
        )
    except Exception as e:
        print(f"⚠️  Unable to load existing FAISS index ({e}). Rebuilding …")
        vector_index = None  # Trigger rebuild below
else:
    vector_index = None  # No index directory yet

if ENABLE_SERVER_SQL_EXEC:
    if vector_index is None:
        schema_docs: list[Document] = []
        for table in inspector.get_table_names():
            if table.startswith("_xlnm"):
                # Skip potential Excel filter tables in some databases
                continue
            info = get_table_schema_from_uri(table)
            if not info:
                continue

            cols_text = "\n".join(
                f"- {col['column_name']} ({col['data_type']}, nullable={col['nullable']})"
                for col in info["columns"]
            )
            sample_text = "\n".join(str(r) for r in info["sample_data"][:2])

            content = (
                f"Table: {table}\n\n"
                f"Columns:\n{cols_text}\n\n"
                f"Sample Rows:\n{sample_text}"
            )
            schema_docs.append(Document(page_content=content, metadata={"table": table}))

        # If we actually collected docs, build the index
        if schema_docs:
            vector_index = FAISS.from_documents(schema_docs, embedding_model)
            vector_index.save_local(INDEX_PATH)
        else:
            raise RuntimeError("No tables discovered to build schema index.")

    # Create a retriever for the agent
    retriever = vector_index.as_retriever(search_kwargs={"k": 3})