from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
import json

# We now import the two separate functions
from agent_logic import get_db_schema, execute_query, generate_sql, analyze_data_for_insights

# --- FLASK APP SETUP ---
app = Flask(__name__)

# --- DATABASE SETUP ---
db_path = 'sales.db'
engine = create_engine(f'sqlite:///{db_path}')
db_schema = get_db_schema(engine)

chat_history = []

# --- API ROUTES ---
@app.route('/')
def index():
    """Renders the main web page."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_agent():
    """
    Implements the two-step process:
    1. Get SQL from AI.
    2. Execute SQL.
    3. Send results back to AI for analysis.
    """
    global chat_history
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    # --- Step 1: Generate SQL ---
    sql_query = generate_sql(user_prompt, db_schema, chat_history)
    if not sql_query:
        return jsonify({"analysis": {"summary": "I'm sorry, I couldn't understand that request."}})

    # --- Step 2: Execute SQL ---
    results_df = execute_query(engine, sql_query)
    
    # --- Step 3: Analyze Results ---
    analysis = None
    results_json = None
    if results_df is not None:
        if not results_df.empty:
            results_json = results_df.to_dict(orient='records')
            # Send the real results to the AI for analysis
            analysis_json_str = analyze_data_for_insights(user_prompt, results_df)
            analysis = json.loads(analysis_json_str)
        else:
            analysis = {"summary": "The query ran successfully but returned no data.", "chart_config": None}
    else:
        analysis = {"summary": "There was an error executing the SQL query.", "chart_config": None}

    # Update history
    chat_history.append({"user": user_prompt, "sql": sql_query})
    if len(chat_history) > 10: chat_history.pop(0)

    # --- Final Response ---
    response_payload = {
        "sql_query": sql_query,
        "analysis": analysis,
        "results": results_json
    }
    
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(debug=True)