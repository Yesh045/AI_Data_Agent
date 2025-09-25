import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import inspect
import json

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATABASE INTERACTION ---
def get_db_schema(engine):
    inspector = inspect(engine)
    schema_info = []
    tables = inspector.get_table_names()
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        column_details = [f"{col['name']} ({col['type']})" for col in columns]
        schema_info.append(f"Table '{table_name}': {', '.join(column_details)}")
    return "\n".join(schema_info)

def execute_query(engine, query):
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(query, connection)
    except Exception as e:
        print(f"Query Execution Error: {e}")
        return None

# --- AI LOGIC (STEP 1: Just get the SQL) ---
def generate_sql(prompt: str, schema: str, history: list) -> str:
    formatted_history = "\n".join([f"User: {h.get('user')}\nAI SQL: {h.get('sql', '')}" for h in history if h.get('sql')])
    full_prompt = f"""You are an expert SQLite data analyst. Your first and only job is to generate a single, valid SQLite query to answer the user's question.
    **Rules:**
    - Only output the SQL query.
    - Do not output any other text, explanations, or markdown.

    **Database Schema:**
    {schema}

    **Conversation History:**
    {history}

    **User's Question:**
    "{prompt}"

    **Generated SQLite Query:**"""
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip().replace("```sql", "").replace("```", "")
    except Exception as e:
        print(f"SQL Generation Error: {e}")
        return None

# --- AI LOGIC (STEP 2: Analyze the actual results) ---
def analyze_data_for_insights(prompt: str, df: pd.DataFrame) -> str:
    """
    Analyzes a DataFrame and returns a JSON object with a summary and
    an optional Chart.js configuration.
    """
    df_head = df.head(5).to_string()
    
    full_prompt = f"""
    You are a principal data analyst. You have been given the results of a user's query. Your job is to analyze these results and provide a summary and a potential visualization.
    Return a single JSON object with two keys:
    1.  "summary" (string): A concise, one-sentence summary of the data's main finding.
    2.  "chart_config" (object or null): Generate a valid Chart.js configuration ONLY IF the data is appropriate for a chart. Otherwise, the value MUST be null.

    **CRITICAL RULES FOR CHARTING:**
    - A chart is appropriate ONLY IF the data contains at least one categorical (text) column AND at least one numerical column.
    - Do NOT generate a chart if the query result is just a single number or a list of text items (like a list of table names).

    **User's Original Request:** "{prompt}"
    **Data Sample (first 5 rows):**
    ```
    {df_head}
    ```

    **Your JSON Output:**
    """
    try:
        response = model.generate_content(full_prompt)
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        json.loads(json_response) # Validate
        return json_response
    except Exception as e:
        print(f"Insight Generation Error: {e}")
        return json.dumps({
            "summary": "I was unable to analyze the data for insights.",
            "chart_config": None
        })