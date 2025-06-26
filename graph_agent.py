from models import BusinessIntelligenceState
from langchain_core.messages import SystemMessage
from config import llm
from tools import tools
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from config import ENABLE_SERVER_SQL_EXEC


def business_intelligence_agent(state: BusinessIntelligenceState):
    """
    Enhanced AI agent that uses reflection to validate SQL queries.
    This agent now has a quality assurance process!
    """
    if ENABLE_SERVER_SQL_EXEC:
        system_prompt = """You are a Senior Business Intelligence Analyst with a quality-first approach.

        Your enhanced workflow:
        1. For business questions, use generate_sql to create SQL queries
        2. ALWAYS use reflect_on_sql to validate queries before execution
        3. Only execute queries that pass reflection (confidence >= 7/10)
        4. If reflection suggests improvements, generate a new query
        5. Use execute_sql_with_analysis to get comprehensive results
        6. Provide business insights based on the data

        Tools available:
        - generate_sql: Convert questions to SQL queries
        - reflect_on_sql: Validate and analyze SQL queries
        - execute_sql_with_analysis: Execute queries with detailed analysis

        Always explain your reasoning and what the reflection process revealed.
    """
    else:
        system_prompt = """You are a Senior Business Intelligence Analyst with a quality-first approach.

        Your enhanced workflow:
        1. For business questions, use generate_sql to create SQL queries
        2. ALWAYS use reflect_on_sql to validate queries.
        3. Only return queries that pass reflection (confidence >= 7/10)
        4. If reflection suggests improvements, generate a new query

        Tools available:
        - generate_sql: Convert questions to SQL queries
        - reflect_on_sql: Validate and analyze SQL queries
    """
    
    messages = state["messages"]
    messages_with_system = [SystemMessage(content=system_prompt)] + messages
    
    model_with_tools = llm.bind_tools(tools)
    response = model_with_tools.invoke(messages_with_system)
    
    return {"messages": [response]}

# Same decision function as before
def should_continue(state: BusinessIntelligenceState):
    """Decide whether to continue with tools or finish"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    return "__end__"

# Create enhanced LangGraph agent
def create_enhanced_bi_agent():
    """
    Build our enhanced agent with reflection capabilities.
    This agent now has quality assurance built-in!
    """
    graph_builder = StateGraph(BusinessIntelligenceState)
    
    graph_builder.add_node("agent", business_intelligence_agent)
    graph_builder.add_node("tools", ToolNode(tools))
    
    graph_builder.set_entry_point("agent")
    
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": "__end__"
        }
    )
    
    graph_builder.add_edge("tools", "agent")
    
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)

agent = create_enhanced_bi_agent()