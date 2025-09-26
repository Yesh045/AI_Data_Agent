import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import inspect
import json
import re

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
genai.configure(api_key=api_key)

# --- MODEL (Using the working name you discovered) ---
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# --- DATABASE INTERACTION (No changes here) ---
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

# --- AI LOGIC (STEP 1: This function is already stable) ---
def generate_sql(prompt: str, schema: str, history: list) -> str:
    full_prompt = f"""You are an expert SQLite data analyst. Your task is to generate a single, valid SQLite query to answer the user's question.
    **CRITICAL RULE:** You MUST wrap your final query in a ```sql markdown block. For example:
    ```sql
    SELECT * FROM sales;
    ```
    Do not add any other conversational text or explanations outside of this block.

    **Database Schema:**
    {schema}

    **User's Question:**
    "{prompt}"
    """
    try:
        response = model.generate_content(full_prompt)
        full_response_text = response.text
        sql_match = re.search(r"```sql\n(.*?)\n```", full_response_text, re.DOTALL)
        
        if sql_match:
            sql_query = sql_match.group(1).strip()
            print(f"Successfully extracted SQL: {sql_query}")
            return sql_query
        else:
            print(f"--- FAILED TO EXTRACT SQL ---")
            print(f"AI Full Response: {full_response_text}")
            return full_response_text.strip() # Fallback
        
    except Exception as e:
        print(f"SQL Generation Error: {e}")
        return None

# --- AI LOGIC (STEP 2: A More Precise Prompt for Charting) ---
def analyze_data_for_insights(prompt: str, df: pd.DataFrame) -> str:
    df_head = df.head(5).to_string()
    
    full_prompt = f"""
    You are a principal data analyst. You have been given the results of a user's query. Your job is to analyze these results and provide a summary and a potential visualization.
    Return a single, valid JSON object with two keys:
    1.  "summary" (string): A concise, one-sentence summary of the data's main finding.
    2.  "chart_config" (object or null): Generate a valid Chart.js configuration ONLY IF the data is appropriate for a chart. Otherwise, the value MUST be null.

    **CRITICAL RULES FOR CHARTING:**
    - A chart is appropriate ONLY IF the data contains at least one categorical (text) column AND at least one numerical column.
    - Do NOT generate a chart if the query result is just a single number or a list of text items.
    
    **Chart.js Blueprint Rules:**
    - The "labels" key MUST point to a single string: the name of the column to be used for the x-axis labels.
    - The "datasets" array's "data" key MUST point to a single string: the name of the column for the y-axis data.
    - Example: "labels": "category", "data": "total_sales"

    **User's Original Request:** "{prompt}"
    **Data Sample (first 5 rows):**
    ```
    {df_head}
    ```

    **Your JSON Output:**
    """
    try:
        response = model.generate_content(full_prompt)
        # A more robust way to extract JSON
        text_response = response.text
        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            json.loads(json_str) # Validate
            return json_str
        else:
             print(f"--- FAILED TO EXTRACT JSON ---")
             print(f"AI Full Response: {text_response}")
             return json.dumps({"summary": "I couldn't format my analysis correctly.", "chart_config": None})

    except Exception as e:
        print(f"Insight Generation Error: {e}")
        return json.dumps({
            "summary": "I was unable to analyze the data for insights.",
            "chart_config": None
        })