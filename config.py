import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.utilities import SQLDatabase
from sqlalchemy import inspect

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY not found in .env file!")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

ENABLE_SERVER_SQL_EXEC = os.getenv("ENABLE_SERVER_SQL_EXEC", "false").lower() == "true"

if ENABLE_SERVER_SQL_EXEC:
    sql_user = os.getenv("SQL_USER")
    sql_pass = os.getenv("SQL_PASSWORD")
    sql_server = os.getenv("SQL_SERVER")
    sql_db = os.getenv("SQL_DATABASE")
    sql_driver = os.getenv("SQL_DRIVER")
    db_path = os.getenv("DB_PATH")
    
    DB_URI = f"mssql+pyodbc://{sql_user}:{sql_pass}@{sql_server}/{sql_db}?driver={sql_driver}&TrustServerCertificate=yes"
    # DB_URI = db_path
    
    if not DB_URI:
        raise ValueError("SQL Server environment variable not set in .env file while ENABLE_SERVER_SQL_EXEC=true!")

    db = SQLDatabase.from_uri(DB_URI)
    engine = db._engine
    inspector = inspect(engine)
else:
    DB_URI = None
    db = None
    engine = None
    inspector = None


