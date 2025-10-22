import os
import re
import json
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import inspect, text
from dotenv import load_dotenv

# --- AI SETUP ---
AI_AVAILABLE = False
model = None
try:
    import google.generativeai as genai
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        AI_AVAILABLE = True
        print("✅ Gemini AI initialized")
    else:
        print("⚠️ No API key")
except ImportError:
    print("⚠️ Google AI not installed")


def get_db_schema(engine) -> str:
    """Extract full schema with sample data."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        schema_parts = []
        
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            col_details = [f"`{col['name']}` ({col['type']})" for col in columns]
            
            # Get sample data for context
            with engine.connect() as conn:
                sample = pd.read_sql_query(text(f"SELECT * FROM {table_name} LIMIT 3"), conn)
                row_count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = row_count_result.scalar()
            
            schema_parts.append(
                f"Table `{table_name}` ({row_count} rows): {', '.join(col_details)}"
            )
        
        return "\n".join(schema_parts)
    except Exception as e:
        return f"Error: {e}"


def execute_query(engine, query: str) -> Optional[pd.DataFrame]:
    """Execute SQL query."""
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(query), connection)
    except Exception as e:
        print(f"Query error: {e}")
        return None


def detect_user_intent(prompt: str) -> Dict[str, Any]:
    """Understand what user wants."""
    prompt_lower = prompt.lower()
    
    intent = {
        "action": "query",
        "wants_visualization": False,
        "visualization_type": None,
        "needs_aggregation": False
    }
    
    # Explicit visualization requests
    viz_keywords = {
        'bar': ['bar chart', 'bar graph', 'bars'],
        'line': ['line chart', 'line graph', 'trend', 'over time'],
        'scatter': ['scatter plot', 'scatter', 'correlation', 'relationship'],
        'pie': ['pie chart', 'pie', 'distribution', 'breakdown'],
        'heatmap': ['heatmap', 'heat map', 'correlation matrix'],
        'histogram': ['histogram', 'frequency']
    }
    
    for viz_type, keywords in viz_keywords.items():
        if any(kw in prompt_lower for kw in keywords):
            intent['wants_visualization'] = True
            intent['visualization_type'] = viz_type
            break
    
    # General visualization words
    if any(word in prompt_lower for word in ['visualize', 'plot', 'graph', 'chart', 'show me']):
        intent['wants_visualization'] = True
    
    # Aggregation indicators
    if any(word in prompt_lower for word in ['total', 'sum', 'average', 'count', 'group by', 'by', 'per']):
        intent['needs_aggregation'] = True
    
    return intent


def intelligent_sql_generation(prompt: str, schema: str, source_type: str) -> Optional[str]:
    """Generate smart SQL that understands context."""
    
    if not AI_AVAILABLE:
        return fallback_sql(prompt, schema, source_type)
    
    try:
        system_prompt = f"""You are an expert SQL analyst. Your job is to understand the user's question and generate the PERFECT SQL query.

**CRITICAL INTELLIGENCE RULES:**
1. **Table Selection**: Analyze which table(s) the question is about. Don't always use the first table.
2. **Column Selection**: Only SELECT columns that are relevant to the question.
3. **Aggregation**: If question asks for totals, averages, counts - use GROUP BY with aggregation.
4. **Joins**: If question involves multiple tables, use proper JOINs.
5. **Filtering**: Add WHERE clauses if question mentions specific conditions.
6. **Sorting**: Use ORDER BY if question asks for "top", "best", "highest", "lowest".
7. **Limits**: Add LIMIT for large result sets unless user wants everything.

**Schema:**
{schema}

**Source Type:** {'DataFrame (use table name df)' if source_type == 'file' else 'Database (use actual table names)'}

**User Question:** "{prompt}"

**Think step by step:**
1. What table(s) does this question relate to?
2. What columns are needed?
3. Does this need GROUP BY? (for aggregations)
4. Does this need JOIN? (for multiple tables)
5. Does this need WHERE? (for filtering)
6. Does this need ORDER BY? (for sorting)

Generate ONLY the SQL query. No explanations, no markdown, just SQL.

SQL Query:"""
        
        response = model.generate_content(system_prompt)
        sql = response.text.strip()
        sql = re.sub(r'```sql\s*|\s*```', '', sql).strip()
        
        if 'SELECT' in sql.upper():
            print(f"🤖 AI Generated SQL: {sql}")
            return sql
        
    except Exception as e:
        print(f"AI SQL error: {e}")
    
    return fallback_sql(prompt, schema, source_type)


def fallback_sql(prompt: str, schema: str, source_type: str) -> str:
    """Smart fallback when AI isn't available."""
    prompt_lower = prompt.lower()
    
    if source_type == 'file':
        table_name = 'df'
    else:
        # Try to extract table name from schema
        tables = re.findall(r'Table `(\w+)`', schema)
        
        # Try to match table name in question
        table_name = None
        for table in tables:
            if table.lower() in prompt_lower:
                table_name = table
                break
        
        if not table_name:
            table_name = tables[0] if tables else 'sales'
    
    # Build intelligent query
    if 'count' in prompt_lower or 'how many' in prompt_lower:
        return f"SELECT COUNT(*) as count FROM {table_name}"
    elif any(word in prompt_lower for word in ['group', 'by', 'category', 'per']):
        return f"SELECT * FROM {table_name} LIMIT 50"
    elif 'total' in prompt_lower or 'sum' in prompt_lower:
        return f"SELECT * FROM {table_name} LIMIT 50"
    else:
        return f"SELECT * FROM {table_name} LIMIT 100"


def generate_sql(prompt: str, schema: str, history: list, source_type: str) -> Optional[str]:
    """Main SQL generation with intelligence."""
    return intelligent_sql_generation(prompt, schema, source_type)


def analyze_dataframe_intelligence(df: pd.DataFrame) -> Dict[str, Any]:
    """Deep analysis of dataframe structure."""
    
    if df.empty:
        return {"error": "Empty dataframe"}
    
    analysis = {
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": {},
        "recommended_visualizations": []
    }
    
    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "unique_count": df[col].nunique(),
            "null_count": df[col].isnull().sum(),
            "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
            "is_categorical": pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]),
            "is_datetime": pd.api.types.is_datetime64_any_dtype(df[col]),
            "is_id": 'id' in col.lower() or col.lower().endswith('_id'),
            "sample_values": df[col].dropna().head(3).tolist() if not df[col].empty else []
        }
        
        # Calculate visualization suitability score
        score = 0
        if col_info['is_id']:
            score = -100  # Never visualize IDs
        elif col_info['is_numeric'] and not col_info['is_id']:
            if col_info['unique_count'] > 20:
                score = 90  # Great for continuous viz
            else:
                score = 70  # Good for discrete viz
        elif col_info['is_categorical']:
            if 2 <= col_info['unique_count'] <= 20:
                score = 95  # Perfect for categorical viz
            elif col_info['unique_count'] > 50:
                score = 20  # Too many categories
            else:
                score = 60
        
        col_info['viz_score'] = score
        analysis['columns'][col] = col_info
    
    return analysis


def recommend_visualizations(df: pd.DataFrame, prompt: str, intent: Dict) -> List[Dict[str, Any]]:
    """Intelligently recommend visualizations based on data structure."""
    
    analysis = analyze_dataframe_intelligence(df)
    
    # Get high-value columns
    sorted_cols = sorted(analysis['columns'].items(), key=lambda x: x[1]['viz_score'], reverse=True)
    
    numeric_cols = [col for col, info in sorted_cols if info['is_numeric'] and not info['is_id']]
    categorical_cols = [col for col, info in sorted_cols if info['is_categorical'] and not info['is_id']]
    
    print(f"\n📊 Data Analysis:")
    print(f"   Numeric columns: {numeric_cols[:3]}")
    print(f"   Categorical columns: {categorical_cols[:3]}")
    
    recommendations = []
    
    # Rule 1: If user specified chart type, prioritize that
    if intent.get('visualization_type'):
        viz_type = intent['visualization_type']
        if viz_type == 'scatter' and len(numeric_cols) >= 2:
            recommendations.append({
                "type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "reason": "User requested scatter plot"
            })
        elif viz_type == 'line' and categorical_cols and numeric_cols:
            recommendations.append({
                "type": "line",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "reason": "User requested line chart"
            })
        elif viz_type == 'pie' and categorical_cols:
            recommendations.append({
                "type": "pie",
                "x": categorical_cols[0],
                "y": "count",
                "reason": "User requested pie chart"
            })
    
    # Rule 2: Categorical + Numeric = Bar Chart (most common and useful)
    if categorical_cols and numeric_cols:
        # Don't repeat if already added
        if not any(r['type'] == 'bar' and r['x'] == categorical_cols[0] for r in recommendations):
            recommendations.append({
                "type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "reason": f"Comparing {numeric_cols[0]} across {categorical_cols[0]}"
            })
    
    # Rule 3: Two numeric columns = Scatter Plot (shows correlation)
    if len(numeric_cols) >= 2:
        if not any(r['type'] == 'scatter' for r in recommendations):
            recommendations.append({
                "type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "reason": f"Relationship between {numeric_cols[0]} and {numeric_cols[1]}"
            })
    
    # Rule 4: Single categorical = Pie/Doughnut (shows distribution)
    if categorical_cols:
        cat_col = categorical_cols[0]
        unique_count = analysis['columns'][cat_col]['unique_count']
        
        if 2 <= unique_count <= 10:  # Good for pie charts
            if not any(r['type'] == 'pie' and r['x'] == cat_col for r in recommendations):
                recommendations.append({
                    "type": "pie",
                    "x": cat_col,
                    "y": "count",
                    "reason": f"Distribution of {cat_col}"
                })
    
    # Rule 5: Multiple categoricals = Grouped bar chart
    if len(categorical_cols) >= 2 and numeric_cols:
        if not any(r['type'] == 'bar' and r['x'] == categorical_cols[1] for r in recommendations):
            recommendations.append({
                "type": "bar",
                "x": categorical_cols[1],
                "y": numeric_cols[0],
                "reason": f"Alternative view: {numeric_cols[0]} by {categorical_cols[1]}"
            })
    
    print(f"   Recommendations: {len(recommendations)} visualizations")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec['type'].upper()}: {rec['reason']}")
    
    return recommendations[:4]  # Limit to 4 charts


def create_chart_config(chart_type: str, title: str, x_col: str, y_col: str) -> Dict[str, Any]:
    """Create Chart.js configuration."""
    
    colors = {
        'bar': ['#2ECC71', '#3498DB', '#E74C3C', '#9B59B6', '#F39C12', '#1ABC9C'],
        'scatter': '#E74C3C',
        'line': '#3498DB',
        'pie': ['#2ECC71', '#3498DB', '#E74C3C', '#9B59B6', '#F39C12', '#1ABC9C', '#E67E22', '#16A085'],
    }
    
    config = {
        "type": chart_type,
        "data": {
            "labels": [x_col],
            "datasets": [{
                "label": title,
                "data": [y_col],
                "backgroundColor": colors.get(chart_type, colors['bar']),
                "borderColor": "#FFFFFF" if chart_type in ['pie'] else colors.get(chart_type, '#3498DB'),
                "borderWidth": 2 if chart_type in ['pie'] else 1
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": chart_type in ['pie', 'line']},
                "title": {"display": True, "text": title, "font": {"size": 14, "weight": "bold"}}
            }
        }
    }
    
    if chart_type in ['bar', 'line', 'scatter']:
        config["options"]["scales"] = {
            "y": {"beginAtZero": True},
            "x": {"display": True}
        }
    
    if chart_type == 'scatter':
        config["data"]["datasets"][0]["showLine"] = False
        config["data"]["datasets"][0]["pointRadius"] = 6
        config["data"]["datasets"][0]["pointBackgroundColor"] = '#E74C3C'
    
    return config


def generate_natural_response(prompt: str, df: pd.DataFrame, intent: Dict) -> str:
    """Generate conversational response."""
    
    if df.empty:
        return "I didn't find any data matching that query."
    
    row_count = len(df)
    
    if AI_AVAILABLE and row_count <= 100:
        try:
            sample = df.head(5).to_string()
            response_prompt = f"""User asked: "{prompt}"

Result: {row_count} rows

Sample:
{sample}

Provide a brief, natural answer (1-2 sentences) about what this data shows.
Be conversational and don't use robotic phrases like "the data shows"."""
            
            response = model.generate_content(response_prompt)
            return response.text.strip()
        except:
            pass
    
    # Fallback
    cols = ', '.join(df.columns.tolist()[:3])
    return f"Found {row_count} records with columns: {cols}{'...' if len(df.columns) > 3 else ''}."


def analyze_data(prompt: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Main intelligence function."""
    
    intent = detect_user_intent(prompt)
    
    print(f"\n🎯 Intent: {intent}")
    
    # Generate natural response
    summary = generate_natural_response(prompt, df, intent)
    
    # Decide on visualizations
    charts = []
    if intent['wants_visualization'] or len(df) <= 50:
        print("🎨 Generating visualizations...")
        recommendations = recommend_visualizations(df, prompt, intent)
        
        for rec in recommendations:
            title = f"{rec['y']} by {rec['x']}" if rec['y'] != 'count' else f"{rec['x']} Distribution"
            charts.append({
                "title": title,
                "config": create_chart_config(rec['type'], title, rec['x'], rec['y']),
                "recommendation": rec
            })
    
    return {
        "summary": summary,
        "charts": charts,
        "intent": intent
    }