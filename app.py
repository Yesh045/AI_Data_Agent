from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
import pandas as pd

# Import the functions from your existing agent.py
from agent import get_db_schema, generate_sql, execute_query

# --- FLASK APP SETUP ---
app = Flask(__name__)

# --- DATABASE SETUP ---
db_path = 'sales.db'
engine = create_engine(f'sqlite:///{db_path}')
db_schema = get_db_schema(engine)

# Keep a simple chat history in memory (for this example)
chat_history = []

# --- API ROUTES ---

@app.route('/')
def index():
    """Renders the main web page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_agent():
    """Receives a question from the frontend and returns the AI's response."""
    global chat_history # Use the global history list
    
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    # 1. Generate SQL Query
    sql_query = generate_sql(user_prompt, db_schema, chat_history)
    if not sql_query:
        return jsonify({"error": "Failed to generate SQL query."}), 500
        
    # Add to history for context in the next turn
    chat_history.append({"user": user_prompt, "sql": sql_query})

    # 2. Execute Query
    results_df = execute_query(engine, sql_query)
    
    # 3. Format the response
    if results_df is None:
        return jsonify({
            "sql": sql_query,
            "results": "Error executing query.",
            "viz": None
        })
    
    # Convert DataFrame to a format that can be sent as JSON
    results_json = results_df.to_dict(orient='records')
    
    # For now, we'll send the data back and let the frontend handle plotting
    return jsonify({
        "sql": sql_query,
        "results": results_json
    })

if __name__ == '__main__':
    app.run(debug=True)
