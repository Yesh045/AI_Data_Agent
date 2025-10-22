from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import pandas as pd
import json
import base64
import io
import os
from pandasql import sqldf
import agent_logic

app_state = {
    "data_source": None,
    "schema": None,
    "db_engine": None,
    "source_type": "none",
    "history": []
}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/connect', methods=['POST'])
def connect_data_source():
    """Connect to data source."""
    global app_state
    
    try:
        source_type = request.json.get('source_type')
        
        if source_type == 'sample_db':
            if not os.path.exists('sales.db'):
                return jsonify({"status": "error", "message": "Run 'python setup_db.py' first"}), 400
            
            engine = create_engine('sqlite:///sales.db')
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            schema = agent_logic.get_db_schema(engine)
            app_state.update({
                "db_engine": engine,
                "data_source": None,
                "schema": schema,
                "source_type": "db",
                "history": []
            })
            return jsonify({"status": "success", "message": "Connected to SQLite", "schema": schema})
        
        elif source_type == 'file':
            file_data_b64 = request.json.get('file_data')
            file_name = request.json.get('file_name')
            
            if not file_data_b64 or not file_name:
                return jsonify({"status": "error", "message": "File data missing"}), 400
            
            file_bytes = base64.b64decode(file_data_b64)
            
            if file_name.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif file_name.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                return jsonify({"status": "error", "message": "Unsupported file type"}), 400
            
            if df.empty:
                return jsonify({"status": "error", "message": "File is empty"}), 400
            
            df.columns = [f"`{str(col).strip()}`" for col in df.columns]
            schema = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])
            
            app_state.update({
                "data_source": df,
                "db_engine": None,
                "schema": schema,
                "source_type": "file",
                "history": []
            })
            
            return jsonify({"status": "success", "message": f"Loaded {file_name}", "schema": schema})
        
        return jsonify({"status": "error", "message": "Invalid source type"}), 400
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_agent():
    """Process conversational query."""
    global app_state
    
    try:
        prompt = request.json.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"analysis": {"summary": "Please ask a question.", "charts": []}}), 400
        
        if not app_state['schema']:
            return jsonify({"analysis": {"summary": "Please connect to a data source first.", "charts": []}})
        
        print(f"\n🔹 User: {prompt}")
        
        # Generate SQL
        sql_query = agent_logic.generate_sql(
            prompt, app_state['schema'], app_state['history'], app_state['source_type']
        )
        
        if not sql_query:
            return jsonify({
                "analysis": {"summary": "I couldn't understand that question. Can you rephrase?", "charts": []},
                "sql_query": None,
                "results": None
            })
        
        print(f"📊 SQL: {sql_query[:100]}...")
        
        # Execute query
        results_df = None
        
        if app_state['source_type'] == 'db':
            results_df = agent_logic.execute_query(app_state['db_engine'], sql_query)
        elif app_state['source_type'] == 'file':
            df = app_state['data_source'].copy()
            try:
                pysqldf = lambda q: sqldf(q, {'df': df})
                results_df = pysqldf(sql_query)
            except Exception as e:
                print(f"PandasSQL error: {e}")
                results_df = df.head(20)  # Fallback
        
        # Analyze and respond
        if results_df is not None and not results_df.empty:
            results_df.columns = [str(col).replace('`', '').strip() for col in results_df.columns]
            
            # Generate intelligent response
            analysis = agent_logic.analyze_data(prompt, results_df)
            results_json = results_df.head(100).to_dict(orient='records')
            
            print(f"✅ Response: {analysis['summary'][:100]}...")
            print(f"📈 Charts: {len(analysis['charts'])}")
            
        else:
            analysis = {"summary": "No data found for that query.", "charts": []}
            results_json = None
        
        # Update history
        app_state['history'].append({"user": prompt, "sql": sql_query})
        if len(app_state['history']) > 10:
            app_state['history'] = app_state['history'][-10:]
        
        return jsonify({
            "sql_query": sql_query,
            "analysis": analysis,
            "results": results_json,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "analysis": {"summary": f"Error: {str(e)}", "charts": []},
            "sql_query": None,
            "results": None
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI DATABASE ASSISTANT")
    print("="*60)
    print("Conversational database queries with intelligent visualization")
    print("http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)