import os
import re
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import argparse # We import the library for handling command-line arguments

# --- AI SETUP ---
try:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    AI_AVAILABLE = True
    print("Gemini AI is ready.")
except Exception as e:
    AI_AVAILABLE = False
    print(f"Could not initialize AI: {e}")


def generate_pandas_code(prompt: str, schema: str) -> str:
    """
    Asks the AI to generate a single line of Pandas code.
    """
    if not AI_AVAILABLE:
        return "df.head(3)" # A simple fallback

    full_prompt = f"""
You are an expert Python data analyst. Your sole task is to generate a single line of Python code that uses a pandas DataFrame named `df` to answer the user's question.
- Do not add any introductory text, closing text, or explanations.
- Do not use markdown formatting or print statements.
- Just provide the raw pandas expression.

**DataFrame Schema (df.info()):**
{schema}

**User's Question:**
"{prompt}"

**Generated Pandas Code:**
"""
    try:
        response = model.generate_content(full_prompt)
        code_text = response.text.strip()
        # Clean the response to be safe
        return re.sub(r'```(python)?\s*|\s*```', '', code_text).strip()
    except Exception as e:
        print(f"AI Code Generation Error: {e}")
        return "df.head(3)" # Fallback on error


if __name__ == "__main__":
    # *** THE FIX IS HERE: We now get the filename from you. ***
    parser = argparse.ArgumentParser(description="AI Agent to analyze your Excel files.")
    parser.add_argument("filename", type=str, help="The path to your Excel file (e.g., 'my_data.xlsx')")
    args = parser.parse_args()
    
    EXCEL_FILE = args.filename
    
    try:
        # Load the Excel file you specified into our DataFrame named 'df'
        df = pd.read_excel(EXCEL_FILE)
        print(f"Successfully loaded '{EXCEL_FILE}'.")
        
        # Create the schema string
        from io import StringIO
        buffer = StringIO()
        df.info(buf=buffer)
        schema = buffer.getvalue()
        
        print("\n--- Agent is Ready ---")
        print(f"Ask questions about your data in '{EXCEL_FILE}'. Type 'exit' to quit.")
        
        while True:
            user_prompt = input("\nYour question: ")
            if user_prompt.lower() == 'exit':
                break

            # 1. Generate Pandas code
            pandas_code = generate_pandas_code(user_prompt, schema)
            print(f"\nAI Generated Code: \n{pandas_code}\n")

            # 2. Execute the code and show the result
            try:
                result = eval(pandas_code)
                print("--- Execution Result ---")
                print(result)
                print("-" * 24)
            except Exception as e:
                print(f"--- Code Execution Failed ---")
                print(f"Error: {e}")
                print("-" * 27)

    except FileNotFoundError:
        print(f"\nError: The file '{EXCEL_FILE}' was not found.")
        print("Please make sure the file is in the same folder as the script, or provide the full path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")