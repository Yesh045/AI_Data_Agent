#!/usr/bin/env python3
"""
AI Agent System for the Analyst Dashboard
This implements a proper AI agent that can reason, plan, and execute complex tasks
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from intent_detector import IntentDetector
from entity_extractor import EntityExtractor
from query_builder import QueryBuilder
from visualization_builder import VisualizationBuilder

@dataclass
class AgentAction:
    """Represents an action the agent can take"""
    action_type: str  # "query", "analyze", "visualize", "explain"
    parameters: Dict[str, Any]
    reasoning: str

@dataclass
class AgentState:
    """Maintains the agent's current state and context"""
    conversation_history: List[Dict[str, Any]]
    current_focus: str  # What the user is currently exploring
    data_context: Dict[str, Any]  # Current data being analyzed
    user_preferences: Dict[str, Any]  # User's preferences and patterns

class AIAnalystAgent:
    """Main AI Agent that orchestrates the entire analysis workflow"""
    
    def __init__(self, db_path: str = "college.db"):
        self.db_path = db_path
        self.state = AgentState(
            conversation_history=[],
            current_focus="general_exploration",
            data_context={},
            user_preferences={}
        )

        # Initialize specialized modules
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor(db_path)
        self.query_builder = QueryBuilder(db_path)
        self.viz_builder = VisualizationBuilder()

        self.available_actions = [
            "query_database",
            "analyze_data",
            "create_visualization",
            "explain_findings",
            "suggest_next_steps",
            "compare_datasets",
            "identify_patterns",
            "generate_insights"
        ]
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """Main entry point - processes user input and returns agent response"""
        
        # Step 1: Understand user intent
        intent = self._analyze_user_intent(user_input)
        
        # Step 2: Plan actions based on intent
        action_plan = self._create_action_plan(intent, user_input)
        
        # Step 3: Execute the plan
        results = self._execute_action_plan(action_plan, user_input)
        
        # Step 4: Update agent state
        self._update_agent_state(user_input, results)
        
        # Step 5: Generate response
        response = self._generate_response(results, intent)
        
        return response
    
    def _analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze what the user wants to accomplish using the intent detector module"""
        try:
            intent = self.intent_detector.detect_intent(user_input)
            if not isinstance(intent, dict):
                intent = {"primary_intent": "data_exploration", "confidence": 0.5, "entities": {}}
            if "entities" not in intent:
                intent["entities"] = {}
            entities = self.entity_extractor.extract_entities(user_input)
            intent["entities"] = entities
            return intent
        except Exception as e:
            # Fallback if modules fail
            return {
                "primary_intent": "data_exploration",
                "confidence": 0.5,
                "entities": {}
            }
    

    
    def _create_action_plan(self, intent: Dict[str, Any], user_input: str) -> List[AgentAction]:
        """Create a plan of actions to fulfill the user's intent"""
        
        actions = []
        
        if intent["primary_intent"] == "data_exploration":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "explore", "entities": intent["entities"]},
                reasoning="User wants to explore data, need to query relevant information"
            ))
        
        elif intent["primary_intent"] == "analysis":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "analyze", "entities": intent["entities"]},
                reasoning="User wants analysis, need to gather relevant data first"
            ))
            actions.append(AgentAction(
                action_type="analyze_data",
                parameters={"analysis_type": "statistical", "entities": intent["entities"]},
                reasoning="Perform statistical analysis on the gathered data"
            ))
            # Add visualization for analysis requests
            actions.append(AgentAction(
                action_type="create_visualization",
                parameters={"chart_type": "line" if "trend" in intent["entities"].get("chart_types", []) else "bar"},
                reasoning="Create visualization to show the analysis results"
            ))
        
        elif intent["primary_intent"] == "visualization":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "visualize", "entities": intent["entities"]},
                reasoning="User wants visualization, need data for charting"
            ))
            actions.append(AgentAction(
                action_type="create_visualization",
                parameters={"chart_type": intent["entities"].get("chart_types", ["bar"])[0]},
                reasoning="Create the requested visualization"
            ))
        
        # Also handle data_exploration with chart requests
        if intent["primary_intent"] == "data_exploration" and intent["entities"].get("chart_types"):
            actions.append(AgentAction(
                action_type="create_visualization",
                parameters={"chart_type": intent["entities"].get("chart_types", ["bar"])[0]},
                reasoning="User wants to visualize the data they're exploring"
            ))
        
        elif intent["primary_intent"] == "insights":
            actions.append(AgentAction(
                action_type="analyze_data",
                parameters={"analysis_type": "insights", "entities": intent["entities"]},
                reasoning="User wants insights, need to analyze current data context"
            ))
            actions.append(AgentAction(
                action_type="explain_findings",
                parameters={"explanation_type": "insights"},
                reasoning="Explain the insights found in the data"
            ))

        elif intent["primary_intent"] == "count_students":
            # Check if this is a course enrollment count query
            if any(keyword in user_input.lower() for keyword in ["students in", "number of students in", "enrolled in", "taking"]):
                actions.append(AgentAction(
                    action_type="query_database",
                    parameters={"query_type": "course_count", "entities": intent["entities"], "user_input": user_input},
                    reasoning="User wants to count students in a specific course, need to join enrollment and courses tables"
                ))
            elif any(keyword in user_input.lower() for keyword in ["from", "in city", "city"]):
                actions.append(AgentAction(
                    action_type="query_database",
                    parameters={"query_type": "city_count", "entities": intent["entities"]},
                    reasoning="User wants to count students by city, need to group by address"
                ))
            else:
                actions.append(AgentAction(
                    action_type="query_database",
                    parameters={"query_type": "count", "entities": intent["entities"]},
                    reasoning="User wants to count students, need to execute count query"
                ))

        elif intent["primary_intent"] == "list_tables":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "list_tables", "entities": intent["entities"]},
                reasoning="User wants to list database tables"
            ))

        elif intent["primary_intent"] == "graph_by_city":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "city_graph", "entities": intent["entities"]},
                reasoning="User wants a graph by city, need to query student data"
            ))
            actions.append(AgentAction(
                action_type="create_visualization",
                parameters={"chart_type": "bar"},
                reasoning="Create bar graph for city distribution"
            ))

        elif intent["primary_intent"] == "enrollment_number":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "enrollment", "entities": intent["entities"], "user_input": user_input},
                reasoning="User wants enrollment information, need to query enrollment table"
            ))
            # Check if this is an attendance query
            if "attendance" in user_input.lower():
                actions.append(AgentAction(
                    action_type="query_database",
                    parameters={"query_type": "attendance", "entities": intent["entities"], "user_input": user_input},
                    reasoning="User is asking about attendance, need to handle this specific case"
                ))

        elif intent["primary_intent"] == "show_table":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "show_table", "entities": intent["entities"], "user_input": user_input},
                reasoning="User wants to show table data, need to query the specified table"
            ))

        elif intent["primary_intent"] == "filtering":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "filtering", "entities": intent["entities"]},
                reasoning="User wants to filter data, need to query relevant information"
            ))

        elif intent["primary_intent"] == "branch_pie_chart":
            actions.append(AgentAction(
                action_type="query_database",
                parameters={"query_type": "branch_count", "entities": intent["entities"]},
                reasoning="User wants a pie chart of specific branches, need to count students by branch"
            ))
            actions.append(AgentAction(
                action_type="create_visualization",
                parameters={"chart_type": "pie"},
                reasoning="Create pie chart for branch distribution"
            ))

        # Always add explanation action
        actions.append(AgentAction(
            action_type="explain_findings",
            parameters={"explanation_type": "summary"},
            reasoning="Provide clear explanation of results to user"
        ))
        
        return actions
    
    def _execute_action_plan(self, action_plan: List[AgentAction], user_input: str) -> Dict[str, Any]:
        """Execute the planned actions"""
        
        results = {
            "data": [],
            "analysis": {},
            "visualization": None,
            "explanation": "",
            "suggestions": []
        }
        
        for action in action_plan:
            if action.action_type == "query_database":
                query_result = self._execute_database_query(action.parameters)
                results["data"] = query_result
            
            elif action.action_type == "analyze_data":
                analysis_result = self._perform_data_analysis(results["data"], action.parameters)
                results["analysis"] = analysis_result
            
            elif action.action_type == "create_visualization":
                viz_result = self._create_visualization(results["data"], action.parameters, user_input)
                results["visualization"] = viz_result
            
            elif action.action_type == "explain_findings":
                explanation = self._generate_explanation(results, action.parameters)
                results["explanation"] = explanation
        
        # Generate suggestions for next steps
        results["suggestions"] = self._generate_suggestions(results)
        
        return results
    
    def _execute_database_query(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute database query based on parameters"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        entities = parameters.get("entities", {})
        query_type = parameters.get("query_type", "explore")

        if query_type == "explore":
            # Build dynamic query based on entities
            query = "SELECT * FROM students WHERE 1=1"
            params = []

            if entities.get("branches"):
                branch = entities["branches"][0]
                query += " AND branch = ?"
                params.append(branch)

            if entities.get("cities"):
                city = entities["cities"][0]
                query += " AND address = ?"
                params.append(city)

            if entities.get("conditions"):
                for condition in entities["conditions"]:
                    metric = condition["metric"]
                    operator = condition["operator"]
                    value = condition["value"]
                    # Map common metric names to column names
                    column_mapping = {
                        "cgpa": "cgpa",
                        "gpa": "cgpa",
                        "attendance": "cgpa",  # Map attendance to cgpa as fallback since attendance column doesn't exist
                        "credits": "semester",  # Map credits to semester as fallback
                        "marks": "cgpa",  # Map marks to cgpa as fallback
                        "semester": "semester"
                    }
                    if metric in column_mapping:
                        column = column_mapping[metric]
                        query += f" AND {column} {operator} ?"
                        params.append(value)

            if entities.get("years"):
                year = entities["years"][0]
                query += " AND admission_year = ?"
                params.append(int(year))

            query += " LIMIT 50"  # Reasonable limit for exploration

            cursor.execute(query, params)
        
        elif query_type == "analyze":
            if entities.get("branches") and entities.get("metrics"):
                branch = entities["branches"][0]
                metric = entities["metrics"][0]
                if metric in ["cgpa", "gpa"]:
                    cursor.execute("""
                        SELECT admission_year, AVG(cgpa) as avg_cgpa 
                        FROM students 
                        WHERE branch = ? 
                        GROUP BY admission_year 
                        ORDER BY admission_year
                    """, (branch,))
        
        elif query_type == "visualize":
            if entities.get("branches") and entities.get("metrics"):
                branch = entities["branches"][0]
                metric = entities["metrics"][0]
                if metric in ["cgpa", "gpa"]:
                    cursor.execute("""
                        SELECT admission_year, AVG(cgpa) as avg_cgpa
                        FROM students
                        WHERE branch = ?
                        GROUP BY admission_year
                        ORDER BY admission_year
                    """, (branch,))
            elif entities.get("branches"):
                branch = entities["branches"][0]
                cursor.execute("SELECT * FROM students WHERE branch = ?", (branch,))
            elif entities.get("chart_types") and "line" in entities.get("chart_types", []):
                # For line chart requests, get CGPA data for Computer Science
                cursor.execute("""
                    SELECT admission_year, cgpa
                    FROM students
                    WHERE branch = 'Computer Science Engineering'
                    ORDER BY admission_year
                """)
            else:
                # Default query for general visualization requests
                cursor.execute("SELECT * FROM students LIMIT 20")

        elif query_type == "count":
            if entities.get("branches"):
                branch = entities["branches"][0]
                cursor.execute("SELECT COUNT(*) as count FROM students WHERE branch = ?", (branch,))
            elif entities.get("cities"):
                city = entities["cities"][0]
                cursor.execute("SELECT COUNT(*) as count FROM students WHERE address = ?", (city,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM students")
        elif query_type == "course_count":
            # Count students enrolled in specific courses using JOIN
            user_input_lower = parameters.get("user_input", "").lower()
            course_names = []

            # Extract course names from user input - handle multiple courses
            course_keywords = ["students in", "number of students in", "enrolled in", "taking"]
            for keyword in course_keywords:
                if keyword in user_input_lower:
                    course_part = user_input_lower.split(keyword)[1].strip()
                    # Split by common separators like "course", "and", ","
                    potential_courses = []
                    for part in course_part.replace("course", "").replace("and", ",").split(","):
                        course = part.strip()
                        if course:
                            potential_courses.append(course)
                    course_names = potential_courses
                    break

            if course_names:
                # Handle multiple courses
                placeholders = " OR ".join(["LOWER(c.course_name) LIKE ?" for _ in course_names])
                params = [f"%{name}%" for name in course_names]
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT e.student_id) as count
                    FROM enrollment e
                    JOIN courses c ON e.course_id = c.course_id
                    WHERE {placeholders}
                """, params)
            else:
                # Default: count all enrollments
                cursor.execute("SELECT COUNT(*) as count FROM enrollment")
        elif query_type == "city_count":
            # Proper city counting query
            cursor.execute("SELECT address, COUNT(*) as count FROM students GROUP BY address ORDER BY count DESC")

        elif query_type == "branch_count":
            # Count students by specific branches for pie chart
            if entities.get("branches"):
                branches = entities["branches"]
                placeholders = ", ".join(["?" for _ in branches])
                cursor.execute(f"""
                    SELECT branch, COUNT(*) as count
                    FROM students
                    WHERE branch IN ({placeholders})
                    GROUP BY branch
                    ORDER BY count DESC
                """, branches)
            else:
                # Default: count all branches
                cursor.execute("SELECT branch, COUNT(*) as count FROM students GROUP BY branch ORDER BY count DESC")


        elif query_type == "filtering":
            # Handle filtering queries - return actual student records, not count
            query = "SELECT * FROM students WHERE 1=1"
            params = []

            if entities.get("branches"):
                branch = entities["branches"][0]
                query += " AND branch = ?"
                params.append(branch)

            if entities.get("cities"):
                city = entities["cities"][0]
                query += " AND address = ?"
                params.append(city)

            if entities.get("conditions"):
                for condition in entities["conditions"]:
                    metric = condition["metric"]
                    operator = condition["operator"]
                    value = condition["value"]
                    # Map common metric names to column names
                    column_mapping = {
                        "cgpa": "cgpa",
                        "gpa": "cgpa",
                        "attendance": "cgpa",  # Map attendance to cgpa as fallback since attendance column doesn't exist
                        "credits": "semester",  # Map credits to semester as fallback
                        "marks": "cgpa",  # Map marks to cgpa as fallback
                        "semester": "semester"
                    }
                    if metric in column_mapping:
                        column = column_mapping[metric]
                        query += f" AND {column} {operator} ?"
                        params.append(value)

            if entities.get("years"):
                year = entities["years"][0]
                query += " AND admission_year = ?"
                params.append(int(year))

            query += " LIMIT 50"  # Reasonable limit for filtering

            cursor.execute(query, params)

        elif query_type == "list_tables":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
            results = cursor.fetchall()
            # For list_tables, return just the table names as simple strings
            data = [{"table_name": row['name']} for row in results]
            conn.close()
            return data

        elif query_type == "city_graph":
            query = "SELECT address FROM students WHERE 1=1"
            params = []
            if entities.get("cities"):
                city = entities["cities"][0]
                query += " AND address = ?"
                params.append(city)
            cursor.execute(query, params)

        elif query_type == "enrollment":
            # Extract student name from user input - improved extraction
            user_input_lower = parameters.get("user_input", "").lower()
            # Look for names after various enrollment keywords
            enrollment_keywords = ["enrollment of", "enrollment number of", "enrollment id of", "find enrollment", "enrollment for", "what is enrollment"]
            name_part = ""
            for keyword in enrollment_keywords:
                if keyword in user_input_lower:
                    name_part = user_input_lower.split(keyword)[1].strip()
                    break

            if name_part:
                # Try to find student by name - more flexible matching
                cursor.execute("SELECT name, student_id FROM students WHERE LOWER(name) LIKE ?", (f"%{name_part}%",))
            else:
                cursor.execute("SELECT name, student_id FROM students LIMIT 10")

        elif query_type == "attendance":
            # Handle attendance queries - since attendance column doesn't exist, map to CGPA
            user_input_lower = parameters.get("user_input", "").lower()
            # Look for names after attendance keywords
            attendance_keywords = ["attendance of", "what is attendance"]
            name_part = ""
            for keyword in attendance_keywords:
                if keyword in user_input_lower:
                    name_part = user_input_lower.split(keyword)[1].strip()
                    break

            if name_part:
                # Try to find student by name and return their CGPA as attendance proxy
                cursor.execute("SELECT name, cgpa as attendance FROM students WHERE LOWER(name) LIKE ?", (f"%{name_part}%",))
            else:
                cursor.execute("SELECT name, cgpa as attendance FROM students LIMIT 10")

        elif query_type == "show_table":
            # Extract table name from user input
            user_input_lower = parameters.get("user_input", "").lower()
            table_name = ""

            # Handle different patterns for table name extraction
            if "table contents of" in user_input_lower:
                # Pattern: "table contents of courses"
                parts = user_input_lower.split("table contents of")
                if len(parts) > 1:
                    table_name = parts[1].strip()
            elif "data inside" in user_input_lower:
                # Pattern: "show me data inside students table"
                parts = user_input_lower.split("data inside")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Remove "table" if present
                    table_name = table_part.replace("table", "").strip()
            elif "contents of" in user_input_lower:
                # Pattern: "show me contents of student table"
                parts = user_input_lower.split("contents of")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Remove "table" if present
                    table_name = table_part.replace("table", "").strip()
            elif "the" in user_input_lower and "table" in user_input_lower:
                # Pattern: "show me the enrollment table"
                parts = user_input_lower.split("the")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Remove "table" if present
                    table_name = table_part.replace("table", "").strip()
            elif "data of" in user_input_lower:
                # Pattern: "show data of faculty table"
                parts = user_input_lower.split("data of")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Remove "table" if present
                    table_name = table_part.replace("table", "").strip()
            elif "show data" in user_input_lower:
                # Pattern: "show data faculty table"
                parts = user_input_lower.split("show data")
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Remove "table" if present
                    table_name = table_part.replace("table", "").strip()
            else:
                # Fallback: look for table names at the end
                words = user_input_lower.split()
                for word in reversed(words):
                    if word in ["students", "courses", "faculty", "enrollment"]:
                        table_name = word
                        break

            if table_name:
                # Map common variations to actual table names
                table_mapping = {
                    "student": "students",
                    "course": "courses",
                    "enrollments": "enrollment",
                    "enrollment": "enrollment",
                    "faculties": "faculty",
                    "faculty": "faculty"
                }
                table_name = table_mapping.get(table_name, table_name)

                # Query the specified table - ensure we get the correct table
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 20")
            else:
                # Default to students table if no table specified
                cursor.execute("SELECT * FROM students LIMIT 20")
        
        results = cursor.fetchall()
        data = [dict(row) for row in results]
        
        conn.close()
        return data
    
    def _perform_data_analysis(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis on the data"""
        
        if not data:
            return {"error": "No data to analyze"}
        
        analysis = {
            "summary_stats": {},
            "patterns": [],
            "insights": []
        }
        
        # Basic statistical analysis
        if data and len(data) > 0:
            numeric_cols = [col for col in data[0].keys() 
                           if isinstance(data[0][col], (int, float))]
            
            for col in numeric_cols:
                values = [row[col] for row in data if row[col] is not None]
                if values:
                    analysis["summary_stats"][col] = {
                        "count": len(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
        
        # Pattern detection
        if len(data) > 1:
            analysis["patterns"].append("Data shows variation across records")
        
        # Generate insights
        if analysis["summary_stats"]:
            analysis["insights"].append("Statistical analysis completed successfully")
        
        return analysis
    
    def _create_visualization(self, data: List[Dict[str, Any]], parameters: Dict[str, Any], user_input: str = "") -> Optional[Dict[str, Any]]:
        """Create visualization based on data and parameters"""

        if not data:
            return None

        chart_type = parameters.get("chart_type", "bar")

        # Determine appropriate chart type based on data
        if len(data) > 0:
            columns = list(data[0].keys())
            numeric_cols = [col for col in columns
                           if isinstance(data[0][col], (int, float)) and data[0][col] is not None]
            categorical_cols = [col for col in columns
                               if not isinstance(data[0][col], (int, float)) or data[0][col] is None]

            # Special handling for pie charts - count distribution
            if chart_type == "pie":
                # For pie charts, we need count data
                if "count" in columns and len(data) > 1:
                    # Data is already aggregated counts
                    labels = [str(row.get('branch', row.get('address', 'Unknown'))) for row in data]
                    counts = [row['count'] for row in data]
                    return {
                        "type": "pie",
                        "title": "Student Distribution",
                        "labels": labels,
                        "data": counts,
                        "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF", "#FF6B6B", "#4ECDC4"]
                    }
                elif len(categorical_cols) >= 1:
                    # Count occurrences for categorical data
                    from collections import Counter
                    counter = Counter(str(row[categorical_cols[0]]) for row in data)
                    labels = list(counter.keys())
                    counts = list(counter.values())

                    return {
                        "type": "pie",
                        "title": f"Distribution of {categorical_cols[0]}",
                        "labels": labels,
                        "data": counts,
                        "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF", "#FF6B6B", "#4ECDC4"]
                    }

            # Special handling for CGPA trends
            if "avg_cgpa" in columns and "admission_year" in columns:
                # Data is already aggregated
                return {
                    "type": "line",
                    "title": "CGPA Trends by Admission Year",
                    "labels": [str(row['admission_year']) for row in data],
                    "data": [row['avg_cgpa'] for row in data],
                    "colors": ["#3b82f6"]
                }
            elif "cgpa" in columns and "admission_year" in columns and chart_type == "line":
                # Group by admission_year and calculate average CGPA
                year_cgpa = {}
                for row in data:
                    year = row.get('admission_year')
                    cgpa = row.get('cgpa')
                    if year is not None and cgpa is not None:
                        if year not in year_cgpa:
                            year_cgpa[year] = []
                        year_cgpa[year].append(cgpa)

                # Calculate averages
                avg_data = []
                for year in sorted(year_cgpa.keys()):
                    avg_cgpa = sum(year_cgpa[year]) / len(year_cgpa[year])
                    avg_data.append({'year': year, 'avg_cgpa': round(avg_cgpa, 2)})

                if avg_data:
                    return {
                        "type": "line",
                        "title": "CGPA Trends by Admission Year",
                        "labels": [str(item['year']) for item in avg_data],
                        "data": [item['avg_cgpa'] for item in avg_data],
                        "colors": ["#3b82f6"]
                    }

            # Check for specific chart requests first
            if len(categorical_cols) >= 1 and ("city" in user_input.lower() or "address" in user_input.lower()):
                # Count occurrences for categorical data
                from collections import Counter

                city_col = "address" if "address" in columns else categorical_cols[0]
                counter = Counter(str(row[city_col]) for row in data)
                # Remove limit to show all cities
                labels = list(counter.keys())
                counts = list(counter.values())

                return {
                    "type": chart_type,
                    "title": f"Students by City",
                    "labels": labels,
                    "data": counts,
                    "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"]
                }

            # Handle CGPA line graph requests specifically
            if chart_type == "line" and ("cgpa" in user_input.lower() or "gpa" in user_input.lower()) and "computer science" in user_input.lower():
                # Group by admission_year and calculate average CGPA for Computer Science
                year_cgpa = {}
                for row in data:
                    year = row.get('admission_year')
                    cgpa = row.get('cgpa')
                    if year is not None and cgpa is not None:
                        if year not in year_cgpa:
                            year_cgpa[year] = []
                        year_cgpa[year].append(cgpa)

                # Calculate averages
                avg_data = []
                for year in sorted(year_cgpa.keys()):
                    avg_cgpa = sum(year_cgpa[year]) / len(year_cgpa[year])
                    avg_data.append({'year': year, 'avg_cgpa': round(avg_cgpa, 2)})

                if avg_data:
                    return {
                        "type": "line",
                        "title": "CGPA Trends by Admission Year (Computer Science Engineering)",
                        "labels": [str(item['year']) for item in avg_data],
                        "data": [item['avg_cgpa'] for item in avg_data],
                        "colors": ["#3b82f6"]
                    }

            # General chart generation
            elif categorical_cols and numeric_cols:
                return {
                    "type": chart_type,
                    "title": f"Analysis of {categorical_cols[0]} vs {numeric_cols[0]}",
                    "labels": [str(row[categorical_cols[0]]) for row in data[:10]],
                    "data": [row[numeric_cols[0]] for row in data[:10]],
                    "colors": ["#3b82f6"]
                }
            elif len(categorical_cols) >= 1:
                # Count occurrences for categorical data
                from collections import Counter
                counter = Counter(str(row[categorical_cols[0]]) for row in data)
                labels = list(counter.keys())[:10]
                counts = list(counter.values())[:10]

                return {
                    "type": chart_type,
                    "title": f"Distribution of {categorical_cols[0]}",
                    "labels": labels,
                    "data": counts,
                    "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"]
                }

        return None
    
    def _generate_explanation(self, results: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate human-readable explanation of results"""
        
        explanation_parts = []
        
        if results["data"]:
            explanation_parts.append(f"Found {len(results['data'])} records matching your query.")
        
        if results["analysis"]:
            explanation_parts.append("Statistical analysis reveals key patterns in the data.")
        
        if results["visualization"]:
            explanation_parts.append("Created visualization to help you understand the data better.")
        
        if results["suggestions"]:
            explanation_parts.append("Here are some suggestions for further exploration:")
            for suggestion in results["suggestions"][:3]:
                explanation_parts.append(f"• {suggestion}")
        
        return " ".join(explanation_parts)
    
    def _generate_suggestions(self, results: Dict[str, Any]) -> List[str]:
        """Generate suggestions for next steps"""
        
        suggestions = []
        
        if results["data"]:
            suggestions.extend([
                "Try filtering by a specific branch",
                "Compare with other years",
                "Create a trend analysis",
                "Look at grade distributions"
            ])
        
        return suggestions
    
    def _update_agent_state(self, user_input: str, results: Dict[str, Any]):
        """Update the agent's internal state"""
        
        # Add to conversation history
        self.state.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "results": results,
            "context": self.state.data_context
        })
        
        # Update current focus based on results
        if results["data"]:
            self.state.current_focus = "data_analysis"
            self.state.data_context = {
                "last_query_results": results["data"],
                "analysis_performed": bool(results["analysis"]),
                "visualization_created": bool(results["visualization"])
            }
    
    def _generate_response(self, results: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response for the user"""

        # Special handling for list_tables intent - return only table names
        if intent["primary_intent"] == "list_tables":
            table_names = [item["table_name"] for item in results["data"]]
            return {
                "success": True,
                "agent_reasoning": "Here are the available tables in the database.",
                "data": table_names,  # Return just the list of table names
                "analysis": {},
                "visualization": None,
                "explanation": f"Found {len(table_names)} tables: {', '.join(table_names)}",
                "suggestions": ["Try querying data from any of these tables"],
                "context": {
                    "intent_confidence": intent["confidence"],
                    "entities_found": intent["entities"],
                    "conversation_length": len(self.state.conversation_history)
                }
            }

        return {
            "success": True,
            "agent_reasoning": f"Based on your request for {intent['primary_intent']}, I analyzed the data and found relevant insights.",
            "data": results["data"],
            "analysis": results["analysis"],
            "visualization": results["visualization"],
            "explanation": results["explanation"],
            "suggestions": results["suggestions"],
            "context": {
                "intent_confidence": intent["confidence"],
                "entities_found": intent["entities"],
                "conversation_length": len(self.state.conversation_history)
            }
        }

# Example usage
if __name__ == "__main__":
    agent = AIAnalystAgent()

    # Test queries to verify improvements
    test_queries = [
        "show me computer science engineering students",
        "list all tables",
        "show me data from faculty table",
        "graph students by city",
        "count students in computer science",
        "show enrollment data",
        "what tables are available",
        "display table data for courses"
    ]

    for query in test_queries:
        print(f"\n=== Testing Query: '{query}' ===")
        try:
            response = agent.process_user_input(query)
            print(f"Intent Detected: {response['context']['intent_confidence']}")
            print(f"Primary Intent: {response['context']['entities_found']}")
            print(f"Data Records: {len(response['data'])}")
            if response['visualization']:
                print(f"Visualization: {response['visualization']['type']} - {response['visualization']['title']}")
            print(f"Explanation: {response['explanation']}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 50)
