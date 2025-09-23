import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# --- SETUP ---
# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)

# --- DATABASE INTERACTION ---

def get_db_schema(engine):
    """
    Retrieves the database schema (table names, columns, types).
    This is the "map" we give to the AI.
    """
    inspector = inspect(engine)
    schema_info = []
    tables = inspector.get_table_names()
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        column_details = [f"{col['name']} ({col['type']})" for col in columns]
        schema_info.append(f"Table '{table_name}': {', '.join(column_details)}")
    return "\n".join(schema_info)

def execute_query(engine, query):
    """Executes the SQL query and returns the result as a pandas DataFrame."""
    try:
        # The 'with' statement ensures the connection is properly closed.
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection)
            return df
    except Exception as e:
        print(f"An error occurred while executing the query: {e}")
        return None

# --- AI LOGIC ---

def generate_sql(prompt: str, schema: str) -> str:
    """
    Uses the Gemini AI to convert a natural language prompt into a SQL query.
    """
    # This is our "meta-prompt" or the master instruction for the AI.
    # It tells the AI its role, the rules, and provides the necessary context.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    full_prompt = f"""
    You are an expert SQLite data analyst. Your task is to generate a SQLite query based on a user's question about a database.

    **Rules:**
    1.  Only output the SQL query. Do not include any other text, explanations, or markdown formatting.
    2.  The query should be a single line of text.
    3.  Your query must be compatible with SQLite syntax.

    **Database Schema:**
    ```
    {schema}
    ```

    **User's Question:**
    "{prompt}"

    **Generated SQLite Query:**
    """
    
    try:
        response = model.generate_content(full_prompt)
        # Clean up the response to ensure it's just the SQL query
        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        return sql_query
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return None

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Path to your SQLite database
    db_path = 'sales.db'
    
    # Create the database engine using SQLAlchemy
    # The 'sqlite:///' part tells SQLAlchemy it's a SQLite database
    engine = create_engine(f'sqlite:///{db_path}')
    
    # 1. Get the database schema
    db_schema = get_db_schema(engine)
    print("--- Database Schema Detected ---")
    print(db_schema)
    print("-" * 30)
    
    # 2. Get the user's question
    user_prompt = input("Ask a question about your data: ")
    
    if user_prompt:
        # 3. Generate the SQL query
        generated_query = generate_sql(user_prompt, db_schema)
        
        if generated_query:
            print("\n--- Generated SQL Query ---")
            print(generated_query)
            print("-" * 30)

            # 4. Execute the query and display the results
            print("\n--- Query Results ---")
            results_df = execute_query(engine, generated_query)
            if results_df is not None:
                if not results_df.empty:
                    # Using .to_string() ensures the full DataFrame is printed
                    print(results_df.to_string())
                else:
                    print("The query executed successfully but returned no results.")
            print("-" * 30)

        else:
            print("Could not generate a query for your question.")


