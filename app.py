"""
AI Analyst Dashboard - Complete Flask Application with AI Agent
Connects to SQLite database and provides AI-powered analysis via AI Agent + Gemini API
"""

import os
import sqlite3
import json
import re
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from ai_agent import AIAnalystAgent

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyBqJhQqJhQqJhQqJhQqJhQqJhQqJhQqJhQqJhQq')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize AI Agent
ai_agent = AIAnalystAgent(db_path="college.db")

# Database configuration
DB_PATH = 'college.db'


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_database_schema():
    """Get database schema information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    schema = {}
    for table in tables:
        table_name = table['name']
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_data = cursor.fetchall()
        
        schema[table_name] = {
            'columns': [dict(col) for col in columns],
            'sample_data': [dict(row) for row in sample_data]
        }

    conn.close()
    return schema


def execute_sql_query(query):
    """Execute SQL query safely (read-only)"""
    # Basic SQL injection protection - only allow SELECT statements
    query_upper = query.strip().upper()
    if not query_upper.startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Execute the original query (not the uppercase version)
        cursor.execute(query.strip())
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        # Convert to list of dictionaries
        data = [dict(zip(columns, row)) for row in results]

        conn.close()
        return data
    except Exception as e:
        conn.close()
        raise e


def generate_dashboard_data():
    """Generate initial dashboard data"""
    dashboard_data = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Chart 1: Total Students Metric
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        dashboard_data.append({
            "type": "metric",
            "title": "Total Students",
            "value": total_students,
            "icon": "👥"
        })

        # Chart 2: Students by Branch
        cursor.execute("""
            SELECT branch, COUNT(*) as count 
            FROM students 
            GROUP BY branch 
            ORDER BY count DESC
        """)
        branches_data = cursor.fetchall()
        dashboard_data.append({
            "type": "bar",
            "title": "Students by Branch",
            "labels": [row['branch'] for row in branches_data],
            "data": [row['count'] for row in branches_data],
            "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
        })
        
        # Chart 3: Average CGPA by Branch
        cursor.execute("""
            SELECT branch, ROUND(AVG(cgpa), 2) as avg_cgpa 
            FROM students 
            WHERE cgpa IS NOT NULL
            GROUP BY branch 
            ORDER BY avg_cgpa DESC
        """)
        cgpa_data = cursor.fetchall()
        dashboard_data.append({
            "type": "line",
            "title": "Average CGPA by Branch",
            "labels": [row['branch'] for row in cgpa_data],
            "data": [row['avg_cgpa'] for row in cgpa_data],
            "colors": ["#4CAF50"]
        })

        # Chart 4: Course Enrollment
        cursor.execute("""
            SELECT c.course_name, COUNT(e.enrollment_id) as enrollments
            FROM courses c
            LEFT JOIN enrollment e ON c.course_id = e.course_id
            GROUP BY c.course_id, c.course_name
            ORDER BY enrollments DESC
        """)
        course_data = cursor.fetchall()
        dashboard_data.append({
            "type": "pie",
            "title": "Course Enrollment",
            "labels": [row['course_name'] for row in course_data],
            "data": [row['enrollments'] for row in course_data],
            "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"]
        })

    except Exception as e:
        print(f"Dashboard generation error: {e}")
        # Fallback data
        dashboard_data = [
            {
                "type": "metric",
                "title": "Total Students",
                "value": 0,
                "icon": "👥"
            }
        ]

    conn.close()
    return dashboard_data


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/init_dashboard')
def init_dashboard():
    """Initialize dashboard with pre-built charts"""
    try:
        dashboard_data = generate_dashboard_data()
        return jsonify({
            "success": True,
            "charts": dashboard_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages using AI Agent"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()

        if not user_question:
            return jsonify({
                "success": False,
                "error": "No question provided"
            })

        # Use AI Agent to process the request
        agent_response = ai_agent.process_user_input(user_question)
        
        # Extract data for backward compatibility
        query_results = agent_response.get('data', [])
        chart_data = agent_response.get('visualization')
        explanation = agent_response.get('explanation', '')
        
        # Generate summary using Gemini for natural language
        try:
            schema = get_database_schema()
            summary_prompt = f"""
            Based on this database schema: {json.dumps(schema, indent=2)}
            And this user question: {user_question}
            And these results: {json.dumps(query_results[:3], indent=2)}
            
            Provide a brief, natural summary of what the user asked and what was found.
            Keep it conversational and helpful.
            """
            
            summary_response = model.generate_content(summary_prompt)
            summary = summary_response.text
        except Exception as e:
            summary = explanation or "Analysis completed successfully."

        return jsonify({
            "success": True,
            "explanation": explanation,
            "summary": summary,
            "data": query_results,
            "chart_data": chart_data,
            "agent_reasoning": agent_response.get('agent_reasoning', ''),
            "suggestions": agent_response.get('suggestions', []),
            "context": agent_response.get('context', {})
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == '__main__':
    print("Starting AI Analyst Dashboard with AI Agent...")
    print("Available endpoints:")
    print("  GET  / - Main dashboard page")
    print("  GET  /init_dashboard - Initialize dashboard charts")
    print("  POST /chat - Handle AI chat queries")
    app.run(debug=True, host='0.0.0.0', port=5000)
