import re
import json
import time
from config import llm, ENABLE_SERVER_SQL_EXEC
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
try:
    # `retriever` may be None when server-side DB access is disabled.
    from db_setup import retriever
except ImportError:
    retriever = None
from helpers import get_database_schema, execute_database_query
from models import QueryReflection

sql_prompt = ChatPromptTemplate.from_template(
    """
You are an expert SQL generator.
You have access to the following table schemas (only the most relevant ones are shown):

{schemas}

QUESTION:
{question}

Write ONLY the SQL query, with no explanation or code fences.
"""
)

sql_chain = sql_prompt | llm | StrOutputParser()

@tool
def generate_sql(question: str) -> str:
    """Convert a natural-language question into a SQL query.

    Behaviour:
        • When a live FAISS retriever is available (server can see the DB) we
          use it to grab the most relevant tables.
        • Otherwise we fall back to a full schema text obtained from
          helpers.get_database_schema().
    """
    try:
        if retriever is not None:
            docs = (
                retriever.invoke(question)
                if hasattr(retriever, "invoke")
                else retriever.get_relevant_documents(question)
            )
            schemas_text = "\n\n".join(d.page_content for d in docs)
        else:
            schemas_text = get_database_schema()

        raw_sql = sql_chain.invoke({"schemas": schemas_text, "question": question})
        sql_query = re.sub(r"^```sql\s*|```$", "", raw_sql, flags=re.IGNORECASE).strip()
        print(f"🤖 Generated SQL: {sql_query}")
        return sql_query
    except Exception as e:
        return f"Error generating SQL: {str(e)}"

@tool
def reflect_on_sql(sql_query: str, original_question: str) -> str:
    """
    NEW TOOL: Analyze and validate a SQL query before execution.
    This is like having a senior developer review the code!
    """
    schema = get_database_schema()

    json_parser = JsonOutputParser(pydantic_object=QueryReflection)
    format_instructions = json_parser.get_format_instructions()

    reflection_prompt = ChatPromptTemplate.from_template(
        """
You are a Senior SQL Developer reviewing a query for accuracy and best practices.

Database Schema:
{schema}

Original Question: {question}
Generated SQL Query: {sql_query}

Analyse this SQL query and provide structured feedback **strictly** in the
following JSON format (no additional keys, no additional text):

{format_instructions}
"""
    )
    
    reflection_chain = reflection_prompt | llm | json_parser
    
    try:
        reflection_result = reflection_chain.invoke({
            "schema": schema,
            "question": original_question,
            "sql_query": sql_query,
            "format_instructions": format_instructions
        })
        
        print(f"🔍 Reflection confidence: {reflection_result.get('confidence', 'unknown')}/10")
        print(f"🔍 Valid: {reflection_result.get('is_valid', 'unknown')}")
        print(f"🔍 Matches intent: {reflection_result.get('matches_intent', 'unknown')}")
        
        return json.dumps(reflection_result, indent=2)
        
    except Exception as e:
        # Fallback reflection if structured parsing fails
        fallback_reflection = {
            "is_valid": False,
            "matches_intent": False,
            "potential_issues": {
                "table_issues": ["Reflection step failed; see explanation"],
                "schema_issues": []
            },
            "suggestions": [
                "Ensure the reflection prompt variables are supplied correctly.",
                "Check SQL query for basic syntax and table/column names."
            ],
            "confidence": 1,
            "explanation": f"Reflection failed: {str(e)}"
        }
        return json.dumps(fallback_reflection, indent=2)

@tool
def execute_sql_with_analysis(sql_query: str) -> str:
    """Execute a SQL query and return comprehensive results with analysis.

    When server-side execution is disabled the function returns a stub payload
    containing the SQL and a message instructing the caller to run it locally.
    """
    if not ENABLE_SERVER_SQL_EXEC:
        return json.dumps(
            {
                "sql_query": sql_query,
                "success": False,
                "analysis": "Server-side execution disabled; please run this query against your own database and get the results",
            },
            indent=2,
        )

    start_time = time.time()
    
    try:
        print(f"📊 Executing: {sql_query}")
        results, count = execute_database_query(sql_query)
        execution_time = time.time() - start_time
        
        if count == 0:
            result = {
                "sql_query": sql_query,
                "results": [],
                "row_count": 0,
                "execution_time_seconds": execution_time,
                "success": True,
                "message": "Query executed successfully but returned no results",
                "analysis": "No data matches the query criteria. Consider checking if data exists or modifying query conditions."
            }
        else:
            # Basic analysis of results
            if count > 0:
                analysis = f"Successfully retrieved {count} records. "
                if count == 1:
                    analysis += "This appears to be a specific lookup query."
                elif count > 10:
                    analysis += "This query returned a substantial dataset suitable for analysis."
                else:
                    analysis += "This query returned a focused dataset."
            else:
                analysis = "Query executed but no results found."
        
            result = {
                "sql_query": sql_query,
                "results": results,
                "row_count": count,
                "execution_time_seconds": round(execution_time, 3),
                "success": True,
                "analysis": analysis
            }
        
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_result = {
            "sql_query": sql_query,
            "error": str(e),
            "execution_time_seconds": round(execution_time, 3),
            "success": False,
            "analysis": f"Query execution failed: {str(e)}"
        }
        return json.dumps(error_result, indent=2)
    


tools = [generate_sql, reflect_on_sql, execute_sql_with_analysis]
