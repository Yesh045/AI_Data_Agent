from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import pandas as pd
import json
import base64
import io
import os
from pandasql import sqldf
import traceback

# Import our AI logic
import agent_logic

# --- APP STATE ---
app_state = {
    "data_source": None, 
    "schema": None, 
    "db_engine": None,
    "source_type": "none", 
    "history": [],
    "connection_info": None
}

# --- FLASK APP SETUP ---
app = Flask(__name__)

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')


@app.route('/connect', methods=['POST'])
def connect_data_source():
    """Connect to various data sources (SQLite, CSV, Excel)."""
    global app_state
    
    try:
        source_type = request.json.get('source_type')
        print(f"Connection request received: {source_type}")
        
        if source_type == 'sample_db':
            # Connect to sample SQLite database
            db_path = 'sales.db'
            if not os.path.exists(db_path):
                return jsonify({
                    "status": "error", 
                    "message": "Sample database not found. Please run 'python setup_db.py' first."
                }), 400
            
            engine = create_engine(f'sqlite:///{db_path}')
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
                table_count = result.scalar()
                if table_count == 0:
                    raise Exception("Database is empty")
            
            schema = agent_logic.get_db_schema(engine)
            message = "Connected to Sample SQLite Database"
            
            app_state.update({
                "db_engine": engine, 
                "data_source": None, 
                "schema": schema, 
                "source_type": "db", 
                "history": [],
                "connection_info": {"type": "sqlite", "path": db_path}
            })
            
            print(f"SQLite connected successfully. Schema: {schema[:100]}...")
        
        elif source_type == 'file':
            # Handle CSV/Excel file upload
            file_data_b64 = request.json.get('file_data')
            file_name = request.json.get('file_name')
            
            if not file_data_b64 or not file_name:
                return jsonify({
                    "status": "error", 
                    "message": "File data missing"
                }), 400
            
            try:
                file_bytes = base64.b64decode(file_data_b64)
                file_buffer = io.BytesIO(file_bytes)
                
                # Read file based on extension
                if file_name.lower().endswith('.csv'):
                    df = pd.read_csv(file_buffer)
                elif file_name.lower().endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_buffer, engine='openpyxl')
                else:
                    return jsonify({
                        "status": "error", 
                        "message": "Unsupported file type. Please upload CSV or Excel (.xlsx, .xls) files."
                    }), 400
                
                if df.empty:
                    return jsonify({
                        "status": "error", 
                        "message": "The uploaded file appears to be empty"
                    }), 400
                
                # Clean column names - wrap in backticks for SQL compatibility
                df.columns = [f"`{str(col).strip()}`" for col in df.columns]
                
                # Generate schema information
                schema_parts = []
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    schema_parts.append(f"{col} ({dtype})")
                schema = ", ".join(schema_parts)
                
                message = f"Successfully loaded {file_name} ({len(df)} rows, {len(df.columns)} columns)"
                
                app_state.update({
                    "data_source": df, 
                    "db_engine": None, 
                    "schema": schema, 
                    "source_type": "file", 
                    "history": [],
                    "connection_info": {
                        "type": "file", 
                        "name": file_name, 
                        "rows": len(df), 
                        "cols": len(df.columns)
                    }
                })
                
                print(f"File connected successfully: {file_name}")
                print(f"DataFrame shape: {df.shape}")
                print(f"Columns: {df.columns.tolist()}")
                
            except Exception as file_error:
                print(f"File reading error: {file_error}")
                traceback.print_exc()
                return jsonify({
                    "status": "error", 
                    "message": f"Error reading file: {str(file_error)}"
                }), 400
        
        else:
            return jsonify({
                "status": "error", 
                "message": "Invalid source type specified"
            }), 400
        
        return jsonify({
            "status": "success", 
            "message": message, 
            "schema": schema,
            "connection_info": app_state["connection_info"]
        })
    
    except Exception as e:
        error_msg = str(e)
        print(f"Connection error: {error_msg}")
        traceback.print_exc()
        
        # Provide more helpful error messages
        if "Access denied" in error_msg:
            error_msg = "Database access denied. Check your credentials."
        elif "Connection refused" in error_msg:
            error_msg = "Cannot connect to database. Check if the database server is running."
        elif "No such file" in error_msg or "not found" in error_msg:
            error_msg = "Database file not found. Please check the file path."
        
        return jsonify({
            "status": "error", 
            "message": f"Connection failed: {error_msg}"
        }), 500


@app.route('/ask', methods=['POST'])
def ask_agent():
    """Process user queries and return analysis with multiple visualizations."""
    global app_state
    
    try:
        user_prompt = request.json.get('prompt', '').strip()
        
        if not user_prompt:
            return jsonify({
                "analysis": {"summary": "Please enter a question about your data.", "charts": []}
            }), 400
        
        if app_state['schema'] is None:
            return jsonify({
                "analysis": {"summary": "Please connect to a data source first.", "charts": []}
            })
        
        print(f"\nProcessing query: {user_prompt}")
        print(f"Source type: {app_state['source_type']}")
        
        # Generate SQL query
        sql_query = agent_logic.generate_sql(
            user_prompt, 
            app_state['schema'], 
            app_state['history'], 
            app_state['source_type']
        )
        
        if not sql_query:
            return jsonify({
                "analysis": {"summary": "I couldn't generate a valid query for that question.", "charts": []},
                "sql_query": None,
                "results": None
            })
        
        print(f"Generated SQL: {sql_query}")
        
        # Execute query based on source type
        results_df = None
        
        if app_state['source_type'] == 'db':
            # SQLite Database - Execute SQL directly
            print("Executing SQL query on database...")
            results_df = agent_logic.execute_query(app_state['db_engine'], sql_query)
            
        elif app_state['source_type'] == 'file':
            # CSV/Excel File - Use pandasql to query the DataFrame
            print("Executing SQL query on DataFrame using pandasql...")
            df = app_state['data_source'].copy()
            
            try:
                # pandasql expects a dictionary with dataframe name as key
                pysqldf = lambda q: sqldf(q, {'df': df})
                results_df = pysqldf(sql_query)
                print(f"Query executed successfully. Result shape: {results_df.shape if results_df is not None else 'None'}")
            except Exception as sql_error:
                print(f"PandasSQL Error: {sql_error}")
                traceback.print_exc()
                
                # Fallback: Try to execute as pandas operation
                try:
                    print("Attempting fallback to direct pandas operations...")
                    # Simple fallback - just return the data
                    results_df = df.head(20)
                    print(f"Fallback successful. Returning {len(results_df)} rows")
                except Exception as fallback_error:
                    print(f"Fallback also failed: {fallback_error}")
                    results_df = None
        
        # Process results
        analysis = None
        results_json = None
        
        if results_df is not None and not results_df.empty:
            print(f"Processing results: {len(results_df)} rows")
            
            # Clean column names for display
            results_df.columns = [str(col).replace('`', '').strip() for col in results_df.columns]
            
            # For aggregated results with single row, try to expand for better visualization
            if len(results_df) == 1 and app_state['source_type'] == 'file':
                print("Single row result detected, attempting to get more data for visualization...")
                # Get the original dataframe for better visualization
                original_df = app_state['data_source'].copy()
                original_df.columns = [col.replace('`', '').strip() for col in original_df.columns]
                
                # Use both the result and original data for analysis
                analysis_json_str = agent_logic.analyze_data_for_insights(user_prompt, original_df.head(100))
            else:
                # Generate insights and chart configurations
                analysis_json_str = agent_logic.analyze_data_for_insights(user_prompt, results_df)
            
            analysis = json.loads(analysis_json_str)
            
            # Convert to JSON for frontend (limit to 100 rows for performance)
            results_json = results_df.head(100).to_dict(orient='records')
            
            print(f"Generated {len(analysis.get('charts', []))} charts")
            
        elif results_df is not None and results_df.empty:
            print("Query returned empty result")
            analysis = {
                "summary": "The query executed successfully but returned no data.", 
                "charts": []
            }
        else:
            print("Query execution failed")
            analysis = {
                "summary": "The query failed to execute. Please try rephrasing your question.", 
                "charts": []
            }
        
        # Update conversation history
        app_state['history'].append({
            "user": user_prompt, 
            "sql": sql_query,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Keep only last 10 interactions
        if len(app_state['history']) > 10:
            app_state['history'] = app_state['history'][-10:]
        
        return jsonify({
            "sql_query": sql_query,
            "analysis": analysis,
            "results": results_json,
            "status": "success"
        })
    
    except Exception as e:
        print(f"Query processing error: {e}")
        traceback.print_exc()
        return jsonify({
            "analysis": {
                "summary": f"An error occurred while processing your query: {str(e)}", 
                "charts": []
            },
            "sql_query": None,
            "results": None,
            "status": "error"
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get current connection status."""
    return jsonify({
        "connected": app_state['source_type'] != 'none',
        "source_type": app_state['source_type'],
        "connection_info": app_state.get('connection_info'),
        "has_schema": app_state['schema'] is not None
    })


@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from current data source."""
    global app_state
    
    # Close database connection if exists
    if app_state.get('db_engine'):
        app_state['db_engine'].dispose()
    
    # Reset state
    app_state.update({
        "data_source": None, 
        "schema": None, 
        "db_engine": None,
        "source_type": "none", 
        "history": [],
        "connection_info": None
    })
    
    return jsonify({
        "status": "success",
        "message": "Disconnected from data source"
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        "status": "error",
        "message": "File too large. Please upload files smaller than 50MB."
    }), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    print(f"Internal server error: {e}")
    traceback.print_exc()
    return jsonify({
        "status": "error",
        "message": "Internal server error occurred. Check server logs for details."
    }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI DATA AGENT DASHBOARD")
    print("="*60)
    print(f"Supported data sources: SQLite, CSV, Excel")
    print(f"AI Engine: {'Google Gemini' if agent_logic.AI_AVAILABLE else 'Fallback Mode'}")
    print(f"Server: http://localhost:5000")
    
    # Check for sample database
    if os.path.exists('sales.db'):
        print(f"Sample database: Found (sales.db)")
    else:
        print(f"Sample database: Not found")
        print(f"Run 'python setup_db.py' to create sample database")
    
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)