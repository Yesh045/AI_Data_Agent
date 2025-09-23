import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
import matplotlib.pyplot as plt
import subprocess
import sys

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
        with engine.connect() as connection:
            df = pd.read_sql_query(query, connection)
            return df
    except Exception as e:
        print(f"\nAn error occurred while executing the query:\n{e}")
        return None

def save_results_to_csv(df: pd.DataFrame):
    """Asks the user if they want to save the results and saves to CSV if they say yes."""
    save_prompt = input("Do you want to save these results to a CSV file? (y/n): ")
    if save_prompt.lower() != 'y':
        return

    filename = "query_results.csv"
    try:
        df.to_csv(filename, index=False)
        print(f"\nResults successfully saved to '{filename}' in your project folder.")
    except Exception as e:
        print(f"\nAn error occurred while saving the file: {e}")


# --- AI LOGIC ---

def generate_sql(prompt: str, schema: str, history: list) -> str:
    """
    Uses the Gemini AI to convert a natural language prompt into a SQL query,
    considering the conversation history.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    formatted_history = "\n".join([f"User: {h['user']}\nAI SQL: {h['sql']}" for h in history])

    full_prompt = f"""
    You are an expert SQLite data analyst. Your task is to generate a SQLite query based on a user's question about a database.
    You have access to the conversation history to understand context for follow-up questions.
    **Rules:**
    1. Only output the SQL query. Do not include any other text, explanations, or markdown formatting.
    2. The query should be a single line of text.
    3. Your query must be compatible with SQLite syntax.
    4. If the user's question is a follow-up, use the history to correctly interpret it.

    **Database Schema:**
    ```
    {schema}
    ```
    **Conversation History:**
    {formatted_history}
    **User's Current Question:**
    "{prompt}"
    **Generated SQLite Query:**
    """
    
    try:
        response = model.generate_content(full_prompt)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        return sql_query
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return None

def generate_plot(prompt: str, df: pd.DataFrame):
    """
    Asks the user if they want a plot and generates/displays it if they say yes.
    """
    plot_prompt = input("Do you want to generate a plot for these results? (y/n): ")
    if plot_prompt.lower() != 'y':
        return
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    df_head = df.head().to_string()

    # This is the corrected string with the closing """.
    full_prompt = f"""
    You are a data visualization expert. Your task is to generate Python code to plot data from a pandas DataFrame named `df`.
    The user wants to visualize the answer to their question: "{prompt}"

    **Rules:**
    1.  Only output Python code for the plot. Do not include any other text, explanations, or markdown.
    2.  Use the `matplotlib.pyplot` library. The DataFrame is already loaded as `df`.
    3.  Make the plot clear and informative (e.g., add titles and labels).
    4.  The code must save the plot to a file named 'plot.png'.
    5.  Do not include `import pandas as pd` or code to load the data; assume `df` is already available.

    **Data Sample (from df.head()):**
    ```
    {df_head}
    ```

    **Python Code for Visualization:**
    """
    
    print("\nGenerating visualization code...")
    try:
        response = model.generate_content(full_prompt)
        plot_code = response.text.strip().replace("```python", "").replace("```", "")
        
        print("Executing visualization code...")
        exec(plot_code, {'df': df, 'plt': plt})

        print("Plot saved to plot.png. Opening image...")
        
        if sys.platform == "win32":
            os.startfile('plot.png')
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, 'plot.png'])

    except Exception as e:
        print(f"An error occurred during visualization: {e}")


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    db_path = 'sales.db'
    engine = create_engine(f'sqlite:///{db_path}')
    
    db_schema = get_db_schema(engine)
    print("--- Database Schema Detected ---")
    print(db_schema)
    print("-" * 30)
    print("Agent is ready. Ask a question about your data. Type 'exit' to quit.")

    chat_history = []

    while True:
        user_prompt = input("\nYour question: ")
        
        if user_prompt.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_prompt:
            generated_query = generate_sql(user_prompt, db_schema, chat_history)
            
            if generated_query:
                print("\n--- Generated SQL Query ---")
                print(generated_query)
                
                chat_history.append({"user": user_prompt, "sql": generated_query})

                print("\n--- Query Results ---")
                results_df = execute_query(engine, generated_query)
                if results_df is not None:
                    if not results_df.empty:
                        print(results_df.to_string())
                        save_results_to_csv(results_df)
                        generate_plot(user_prompt, results_df)
                    else:
                        print("The query executed successfully but returned no results.")
                print("-" * 30)

            else:
                print("Could not generate a query for your question.")


    

