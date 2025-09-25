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

# --- MODEL REVERT ---
# We are reverting to the 1.5 Flash model. It is highly capable and has
# a more generous free tier, which will prevent the quota errors.
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

# --- AI LOGIC ---
def generate_sql(prompt: str, schema: str, history: list) -> str:
    formatted_history = "\n".join([f"User: {h.get('user')}\nAI SQL: {h.get('sql', '')}" for h in history if h.get('sql')])
    full_prompt = f"""You are an expert SQLite data analyst. Generate a SQLite query based on a user's question.
    **Rules:** Only output the SQL query. No other text.
    **Schema:**\n{schema}
    **History:**\n{formatted_history}
    **User's Question:** "{prompt}"
    **Generated SQLite Query:**"""
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip().replace("```sql", "").replace("```", "")
    except Exception as e:
        print(f"SQL Generation Error: {e}")
        return None

def generate_chat_response(prompt: str, schema: str, history: list) -> str:
    formatted_history = "\n".join([f"User: {h.get('user')}\nAI: {h.get('chat') or h.get('sql')}" for h in history])
    full_prompt = f"""You are a helpful data analyst assistant. Answer the user's question based on the database schema and conversation history.
    Be concise and helpful.
    **Schema:**\n{schema}
    **History:**\n{formatted_history}
    **User's Question:** "{prompt}"
    **Your Answer:**"""
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Chat Generation Error: {e}")
        return "Sorry, I encountered an error."

def analyze_data_for_insights(prompt: str, df: pd.DataFrame) -> str:
    """
    Analyzes a DataFrame and returns a JSON object with a summary and
    an optional Chart.js configuration.
    """
    df_head = df.head().to_string()
    columns = df.columns.tolist()
    
    full_prompt = f"""
    You are a principal data analyst. Your job is to analyze the results of a user's query and provide a summary and a potential visualization.
    Based on the user's request and the provided data, return a single JSON object with two keys:
    1.  "summary" (string): A concise, one-sentence summary of the data's main finding.
    2.  "chart_config" (object or null): If the data is suitable for visualization (e.g., has at least two columns, isn't just a single number), generate a valid Chart.js JSON configuration. Otherwise, this key's value should be null.

    **Rules for Chart Config:**
    - Choose the best chart type ('bar', 'line', 'pie').
    - Identify the correct columns for labels and data.
    - Create a descriptive title.
    - Do not include the actual data in the config; use column names as placeholders in an array, like "data": ["column_name"].

    **User's Request:** "{prompt}"
    **DataFrame Columns:** {columns}
    **Data Sample:**
    ```
    {df_head}
    ```

    **Your JSON Output:**
    """
    try:
        response = model.generate_content(full_prompt)
        # Ensure the response is clean JSON
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        # Validate the JSON to prevent errors
        json.loads(json_response)
        return json_response
    except Exception as e:
        print(f"Insight Generation Error: {e}")
        # Return a fallback JSON object on error
        return json.dumps({
            "summary": "I was unable to analyze the data for insights.",
            "chart_config": None
        })