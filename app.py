from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
import json

# Import the updated and new functions from our logic file
from agent_logic import get_db_schema, generate_sql, execute_query, generate_chat_response, analyze_data_for_insights

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
    Receives a question from the frontend, determines intent,
    and returns a multi-part response with AI-driven insights.
    """
    global chat_history
    user_prompt = request.json.get('prompt')
    if not user_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    # Simple intent detection
    is_chat_request = user_prompt.lower().startswith(('what is', 'is this', 'why', 'who', 'explain'))

    # Initialize the response object
    response_payload = {"sql": None, "results": None, "analysis": None, "chat_response": None}

    if not is_chat_request:
        # --- DATA QUERY & ANALYSIS PATH ---
        sql_query = generate_sql(user_prompt, db_schema, chat_history)
        if not sql_query:
            response_payload["chat_response"] = "I'm sorry, I couldn't generate a SQL query for that request."
            return jsonify(response_payload)
            
        response_payload["sql"] = sql_query
        chat_history.append({"user": user_prompt, "sql": sql_query})
        
        results_df = execute_query(engine, sql_query)
        
        if results_df is not None:
            if not results_df.empty:
                results_json = results_df.to_dict(orient='records')
                response_payload["results"] = results_json
                
                # *** The NEW Smart Step ***
                # Ask the AI to analyze the results and provide insights
                analysis_json_str = analyze_data_for_insights(user_prompt, results_df)
                response_payload["analysis"] = json.loads(analysis_json_str) # Parse the JSON string
            else:
                 response_payload["analysis"] = {"summary": "The query ran successfully but returned no data.", "chart_config": None}
        else:
            response_payload["analysis"] = {"summary": "There was an error executing the SQL query.", "chart_config": None}

    else:
        # --- CHAT PATH ---
        chat_response = generate_chat_response(user_prompt, db_schema, chat_history)
        response_payload["chat_response"] = chat_response
        chat_history.append({"user": user_prompt, "chat": chat_response})

    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(debug=True)