from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel, Field
from pydantic import BaseModel
from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class PotentialIssues(LangChainBaseModel):
    table_issues: list[str] = Field(description="List of potential table issues, for example: 'Table does not exist'")
    schema_issues: list[str] = Field(description="List of potential schema issues, for example: 'Column does not exist'")

class QueryReflection(LangChainBaseModel):
    """
    Schema for SQL query reflection analysis.
    This defines exactly what information we want from our reflection process.
    """
    is_valid: bool = Field(description="Whether the SQL is syntactically correct")
    matches_intent: bool = Field(description="Whether it addresses the user's question")
    potential_issues: PotentialIssues = Field(description="List of potential schema/table/column problems")
    suggestions: List[str] = Field(description="List of improvements or corrections")
    confidence: int = Field(description="1-10 score of query correctness", ge=1, le=10)
    explanation: str = Field(description="Detailed analysis of the query")

class BusinessIntelligenceState(TypedDict):
    """
    Enhanced agent memory that tracks reflection and validation steps.
    """
    messages: Annotated[List, add_messages]
    current_question: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"