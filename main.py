import json
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from config import llm, ENABLE_SERVER_SQL_EXEC
from helpers import execute_database_query
from models import ChatRequest
from graph_agent import agent

# fastAPI setup
app = FastAPI(
    title="BI Agent with SQL Reflection",
    description="A Business Intelligence Agent with built-in SQL validation and reflection!",
    version="1.0.0"
)

# just a home route to see if the server is running or not
@app.get("/")
async def hello_world():
    return {"message": "Hello World! My BI Agent now validates SQL with reflection!"}

# status route, to see if everything is working fine or not => not an important route
@app.get("/status")
async def check_status():
    """Enhanced status check with reflection testing"""
    try:
        # Test basic AI
        test_message = HumanMessage(content="Say 'Enhanced BI ready!'")
        ai_response = llm.invoke([test_message])
        if ai_response:
            ai_working = True
        else:        
            ai_working = False
    except Exception:
        ai_working = False
    
    if ENABLE_SERVER_SQL_EXEC:
        try:
            # Test database (simple lightweight query)
            results = execute_database_query("SELECT COUNT(*) as total FROM customers")
            if results:
                db_working = True
                total_customers = results[0]['total']
            else:
                db_working = False
                total_customers = 0    
        except Exception:
            db_working = False
            total_customers = 0
    else:
        db_working = False
        total_customers = 0
    
    try:
        # Test enhanced agent
        test_response = agent.invoke(
            {"messages": [HumanMessage(content="How many customers do we have?")]},
            config={"configurable": {"thread_id": "test"}}
        )
        if test_response:
            agent_working = True
        else:
            agent_working = False
    except Exception:
        agent_working = False
    
    return {
        "status": "running",
        "ai_working": ai_working,
        "database_working": db_working,
        "enhanced_agent_working": agent_working,
        "total_customers": total_customers
    }

# main route, responsible to taking the natural language qiestion in chat request
@app.post("/api/chat")
async def chat_with_enhanced_agent(request: ChatRequest):
    """
    Chat with our enhanced agent that uses reflection for quality assurance!
    """
    try:
        print(f"🧠 User asked: {request.message}")
        print(f"🆔 Thread ID: {request.thread_id}")
        
        # agent does the heavy lifting NL => SQL => Reflection on SQL => Regenrate SQL => Execute SQL(server side)
        response = agent.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.thread_id}}
        )
        
        last_message = response["messages"][-1]
        agent_reply = last_message.content
        
        print(f"🤖 Agent responded: {agent_reply}")
        
        # More robust analysis of tool usage and results
        used_tools = []
        reflection_results = None
        sql_query = None
        sql_results = None
        
        # Create a map of tool_call_id to tool_name for accurate lookup
        tool_call_map = {}
        for msg in response["messages"]:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_call_map[tool_call["id"]] = tool_call["name"]
                    if tool_call["name"] not in used_tools:
                        used_tools.append(tool_call["name"])

        # Find the results associated with each tool call
        for msg in response["messages"]:
            if isinstance(msg, ToolMessage):
                tool_name = tool_call_map.get(msg.tool_call_id)
                try:
                    data = json.loads(msg.content)
                    if tool_name == "reflect_on_sql":
                        reflection_results = data
                    elif tool_name == "execute_sql_with_analysis":
                        sql_results = data.get("results")
                        sql_query = data.get("sql_query")
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # ---------------------------------------------------------------
        # When server-side execution is DISABLED we still want to return
        # the generated SQL even though the execute_sql_with_analysis
        # tool is never invoked. In that case the query is usually
        # embedded inside the agent response within a markdown code block.
        # We extract it and clean it up so that callers receive a plain
        # runnable SQL string.
        # ---------------------------------------------------------------
        if not ENABLE_SERVER_SQL_EXEC and sql_query is None and isinstance(agent_reply, str):
            import re
            # Attempt to capture everything between ```sql ... ``` fences
            pattern = r"```sql\s*([\s\S]+?)\s*```"
            match = re.search(pattern, agent_reply, flags=re.IGNORECASE)
            if match:
                extracted_sql = match.group(1)
            else:
                # Fallback: grab the first semicolon-terminated statement
                fallback_match = re.search(r"SELECT[\s\S]+?;", agent_reply, flags=re.IGNORECASE)
                extracted_sql = fallback_match.group(0) if fallback_match else None
            if extracted_sql:
                # Strip newlines/tabs and collapse multiple spaces
                cleaned = " ".join(extracted_sql.split())
                sql_query = cleaned.strip()
        
        # Build the response payload. We return a leaner payload when
        # server-side execution is disabled, as the client can run the
        # query locally.
        if not ENABLE_SERVER_SQL_EXEC:
            return {
                "user_message": request.message,
                "tools_used": used_tools,
                "sql_query": sql_query,
                "reflection_applied": "reflect_on_sql" in used_tools,
                "reflection_results": reflection_results,
                "thread_id": request.thread_id,
                "success": True,
            }
        else:
            return {
                "user_message": request.message,
                "agent_response": agent_reply,
                "tools_used": used_tools,
                "sql_query": sql_query,
                "sql_results": sql_results,
                "reflection_applied": "reflect_on_sql" in used_tools,
                "reflection_results": reflection_results,
                "thread_id": request.thread_id,
                "success": True
            }
        
    except Exception as e:
        print(f"❌ Error in enhanced chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced agent chat failed: {str(e)}")