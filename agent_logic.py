import os
import re
import json
import pandas as pd
from typing import Optional, Dict, Any, List
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
        print("Google Gemini AI initialized successfully!")
    else:
        print("No GOOGLE_API_KEY found. Using fallback logic.")
except ImportError:
    print("Google Generative AI not installed. Using fallback logic.")


def get_db_schema(engine) -> str:
    """Extract database schema with table and column information."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        schema_info = []
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            column_details = [f"`{col['name']}` ({col['type']})" for col in columns]
            schema_info.append(f"Table `{table_name}`: {', '.join(column_details)}")
        return "\n".join(schema_info)
    except Exception as e:
        print(f"Schema extraction error: {e}")
        return "Unable to extract schema"


def execute_query(engine, query: str) -> Optional[pd.DataFrame]:
    """Execute SQL query on database engine."""
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(query), connection)
    except Exception as e:
        print(f"Query execution error: {e}")
        return None


def generate_sql_with_intelligence(prompt: str, schema: str, source_type: str) -> str:
    """Generate SQL with better understanding of aggregation needs."""
    prompt_lower = prompt.lower()
    
    # Detect if we need grouping/aggregation
    needs_grouping = any(word in prompt_lower for word in ['by', 'group', 'each', 'per', 'distribution', 'breakdown'])
    needs_counting = any(word in prompt_lower for word in ['count', 'how many', 'number of', 'most', 'least'])
    needs_sum = any(word in prompt_lower for word in ['total', 'sum', 'revenue', 'sales'])
    
    # For file-based sources
    if source_type == 'file':
        # Example: "age and smoker" query
        if 'age' in prompt_lower and 'smok' in prompt_lower:
            return "SELECT `age`, `smoker`, COUNT(*) as count FROM df GROUP BY `age`, `smoker` ORDER BY `age`"
        
        # Generic grouping with count
        elif needs_grouping and needs_counting:
            # Try to find the grouping column from prompt
            return "SELECT * FROM df"
        
        return "SELECT * FROM df LIMIT 50"
    
    # For database sources
    else:
        if "category" in prompt_lower:
            return "SELECT category, COUNT(*) as count FROM products GROUP BY category"
        elif "revenue" in prompt_lower or "sales by" in prompt_lower:
            return "SELECT p.category, SUM(s.sale_price * s.quantity_sold) as revenue FROM sales s JOIN products p ON s.product_id = p.product_id GROUP BY p.category ORDER BY revenue DESC"
        
        return "SELECT * FROM sales LIMIT 50"


def generate_sql(prompt: str, schema: str, history: list, source_type: str) -> Optional[str]:
    """Generate SQL query using AI with better prompting."""
    
    if AI_AVAILABLE:
        try:
            if source_type == 'file':
                context = f"""You are analyzing a DataFrame named `df`.

**DataFrame Schema:**
{schema}

**CRITICAL INSTRUCTIONS:**
1. Always use 'df' as the table name
2. Wrap column names with spaces in backticks
3. If the question asks about relationships, use GROUP BY with COUNT/SUM
4. For "most", "least", "distribution" - use GROUP BY and ORDER BY
5. For age-based or categorical analysis - GROUP BY those columns"""
            else:
                context = f"""You are querying a SQLite database.

**Database Schema:**
{schema}

**CRITICAL INSTRUCTIONS:**
1. Use proper table names from schema
2. For aggregations, use GROUP BY with COUNT/SUM/AVG
3. Use JOIN when relating multiple tables
4. For "most", "least" - use ORDER BY with LIMIT"""

            full_prompt = f"""{context}

User Question: "{prompt}"

Think step by step:
1. What columns are relevant to this question?
2. Does this need aggregation (GROUP BY, COUNT, SUM)?
3. Does this need sorting (ORDER BY)?

Generate a SQL query that will return data ready for visualization.
Return ONLY the SQL query, no explanations.

SQL Query:"""
            
            response = model.generate_content(full_prompt)
            sql_text = response.text.strip()
            
            # Clean up response
            sql_text = re.sub(r'```sql\s*', '', sql_text)
            sql_text = re.sub(r'```\s*', '', sql_text)
            sql_text = sql_text.strip()
            
            if sql_text and 'SELECT' in sql_text.upper():
                print(f"AI Generated SQL: {sql_text}")
                return sql_text
            else:
                return generate_sql_with_intelligence(prompt, schema, source_type)
                
        except Exception as e:
            print(f"AI SQL generation error: {e}")
            return generate_sql_with_intelligence(prompt, schema, source_type)
    else:
        return generate_sql_with_intelligence(prompt, schema, source_type)


def preprocess_data_for_visualization(df: pd.DataFrame, prompt: str) -> pd.DataFrame:
    """Intelligently aggregate and prepare data for visualization."""
    
    if df.empty or len(df) == 0:
        return df
    
    prompt_lower = prompt.lower()
    
    # If data is already aggregated (has count/sum columns), return as is
    if 'count' in [col.lower() for col in df.columns]:
        print("Data already aggregated")
        return df
    
    # If we have too many rows, we need to aggregate
    if len(df) > 50:
        print(f"Data has {len(df)} rows, attempting intelligent aggregation...")
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
        
        # Remove ID-like columns from categorical
        categorical_cols = [col for col in categorical_cols if not col.lower().endswith('_id')]
        
        if categorical_cols:
            # Group by first categorical column and aggregate
            group_col = categorical_cols[0]
            
            if numeric_cols:
                # Aggregate numeric columns
                agg_dict = {col: 'sum' for col in numeric_cols}
                df_agg = df.groupby(group_col).agg(agg_dict).reset_index()
                print(f"Aggregated by {group_col}")
                return df_agg
            else:
                # Just count occurrences
                df_agg = df.groupby(group_col).size().reset_index(name='count')
                print(f"Counted by {group_col}")
                return df_agg
    
    return df


def create_chart_config(chart_type: str, title: str, labels_col: str, data_col: str) -> Dict[str, Any]:
    """Create Chart.js configuration for different chart types."""
    
    color_schemes = {
        'bar': ['#2ECC71', '#3498DB', '#E74C3C', '#9B59B6', '#F39C12', '#1ABC9C'],
        'line': '#3498DB',
        'pie': ['#2ECC71', '#3498DB', '#E74C3C', '#9B59B6', '#F39C12', '#1ABC9C', '#E67E22'],
        'doughnut': ['#9B59B6', '#3498DB', '#2ECC71', '#E74C3C', '#F39C12', '#1ABC9C'],
    }
    
    config = {
        "type": chart_type,
        "data": {
            "labels": [labels_col],
            "datasets": [{
                "label": title,
                "data": [data_col],
                "backgroundColor": color_schemes.get(chart_type, color_schemes['bar']),
                "borderColor": "#FFFFFF",
                "borderWidth": 2
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                },
                "title": {
                    "display": True,
                    "text": title,
                    "font": {
                        "size": 14,
                        "weight": "bold"
                    }
                }
            }
        }
    }
    
    if chart_type in ['bar', 'line']:
        config["options"]["scales"] = {
            "y": {
                "beginAtZero": True
            }
        }
    
    return config


def generate_intelligent_charts(df: pd.DataFrame, prompt: str) -> List[Dict[str, Any]]:
    """Generate smart charts based on data structure and question intent."""
    
    charts = []
    
    # First, preprocess the data
    df = preprocess_data_for_visualization(df, prompt)
    
    if df.empty or len(df) == 0:
        return []
    
    print(f"Generating charts for DataFrame with shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    # Remove ID columns
    categorical_cols = [col for col in categorical_cols if not col.lower().endswith('_id')]
    
    print(f"Numeric columns: {numeric_cols}")
    print(f"Categorical columns: {categorical_cols}")
    
    # CHART 1: Primary Bar Chart (most important visualization)
    if categorical_cols and numeric_cols:
        # Use the most meaningful columns
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        charts.append({
            "title": f"{y_col} by {x_col}",
            "config": create_chart_config('bar', f"{y_col} by {x_col}", x_col, y_col)
        })
        print(f"Chart 1: Bar chart - {y_col} by {x_col}")
    
    # CHART 2: Line Chart for Trends
    if len(numeric_cols) >= 2:
        charts.append({
            "title": f"{numeric_cols[0]} Trend",
            "config": create_chart_config('line', f"{numeric_cols[0]} Over Time", 
                                         categorical_cols[0] if categorical_cols else numeric_cols[1], 
                                         numeric_cols[0])
        })
        print(f"Chart 2: Line chart - {numeric_cols[0]}")
    elif categorical_cols and numeric_cols:
        # Alternative line chart
        charts.append({
            "title": f"{numeric_cols[0]} Progression",
            "config": create_chart_config('line', f"{numeric_cols[0]} by {categorical_cols[0]}", 
                                         categorical_cols[0], numeric_cols[0])
        })
        print(f"Chart 2: Line chart - {numeric_cols[0]} by {categorical_cols[0]}")
    
    # CHART 3: Pie Chart for Distribution
    if categorical_cols and numeric_cols:
        charts.append({
            "title": f"{categorical_cols[0]} Distribution",
            "config": create_chart_config('pie', f"{categorical_cols[0]} Breakdown", 
                                         categorical_cols[0], numeric_cols[0])
        })
        print(f"Chart 3: Pie chart - {categorical_cols[0]}")
    
    # CHART 4: Doughnut Chart for Alternative View
    if len(categorical_cols) > 1 and numeric_cols:
        charts.append({
            "title": f"{categorical_cols[1]} Overview",
            "config": create_chart_config('doughnut', f"{categorical_cols[1]} Distribution", 
                                         categorical_cols[1], numeric_cols[0])
        })
        print(f"Chart 4: Doughnut chart - {categorical_cols[1]}")
    elif len(numeric_cols) > 1 and categorical_cols:
        charts.append({
            "title": f"{numeric_cols[1]} Distribution",
            "config": create_chart_config('doughnut', f"{numeric_cols[1]} by {categorical_cols[0]}", 
                                         categorical_cols[0], numeric_cols[1])
        })
        print(f"Chart 4: Doughnut chart - {numeric_cols[1]} by {categorical_cols[0]}")
    
    print(f"Generated {len(charts)} charts")
    return charts[:4]  # Return maximum 4 charts


def analyze_data_for_insights(prompt: str, df: pd.DataFrame) -> str:
    """Analyze dataframe and generate insights with intelligent chart configurations."""
    
    if df.empty:
        return json.dumps({"summary": "No data available for analysis.", "charts": []})
    
    try:
        # Generate summary
        row_count = len(df)
        col_count = len(df.columns)
        
        print(f"\nAnalyzing data: {row_count} rows, {col_count} columns")
        
        # Get AI summary if available
        if AI_AVAILABLE:
            try:
                df_sample = df.head(5).to_string()
                summary_prompt = f"""Analyze this data and provide ONE concise sentence summarizing the key insight:

Data preview:
{df_sample}

Total rows: {row_count}

One sentence summary:"""
                
                response = model.generate_content(summary_prompt)
                summary = response.text.strip()
                # Remove quotes if present
                summary = summary.strip('"').strip("'")
            except Exception as e:
                print(f"AI summary error: {e}")
                summary = f"Analysis shows {row_count} data points across {col_count} dimensions."
        else:
            summary = f"Analysis shows {row_count} data points across {col_count} dimensions."
        
        # Generate intelligent charts
        charts = generate_intelligent_charts(df, prompt)
        
        return json.dumps({
            "summary": summary,
            "charts": charts
        })
        
    except Exception as e:
        print(f"Data analysis error: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "summary": f"Analysis completed with {len(df)} records.",
            "charts": []
        })


if __name__ == '__main__':
    print("Testing agent_logic...")
    
    # Test with sample data
    test_df = pd.DataFrame({
        'age': [25, 30, 35, 25, 30, 35, 40, 45],
        'smoker': ['yes', 'no', 'yes', 'yes', 'no', 'no', 'yes', 'no'],
        'count': [10, 15, 8, 12, 20, 18, 5, 22]
    })
    
    result = analyze_data_for_insights("show age and smoker distribution", test_df)
    print("\nTest Analysis Result:")
    print(json.dumps(json.loads(result), indent=2))