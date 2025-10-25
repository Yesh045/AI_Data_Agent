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
        """Analyze what the user wants to accomplish"""
        
        # This would typically use a more sophisticated NLP model
        # For now, we'll use pattern matching with some intelligence
        
        intent_patterns = {
            "data_exploration": ["show", "list", "find", "get", "display"],
            "analysis": ["analyze", "compare", "trend", "pattern", "correlation", "cgpa trend", "gpa trend"],
            "visualization": ["plot", "chart", "graph", "visualize", "create chart", "make chart"],
            "insights": ["why", "what does this mean", "insight", "explain"],
            "comparison": ["compare", "vs", "versus", "difference", "better"],
            "prediction": ["predict", "forecast", "future", "will"],
            "filtering": ["filter", "where", "only", "students with", "in"]
        }
        
        user_lower = user_input.lower()
        detected_intents = []
        
        for intent_type, patterns in intent_patterns.items():
            if any(pattern in user_lower for pattern in patterns):
                detected_intents.append(intent_type)
        
        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else "data_exploration"
        
        # Extract entities (branches, years, etc.)
        entities = self._extract_entities(user_input)
        
        return {
            "primary_intent": primary_intent,
            "secondary_intents": detected_intents[1:],
            "entities": entities,
            "confidence": 0.8 if detected_intents else 0.3
        }
    
    def _extract_entities(self, user_input: str) -> Dict[str, List[str]]:
        """Extract relevant entities from user input"""
        
        # Get available branches from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT branch FROM students")
        branches = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        entities = {
            "branches": [],
            "years": [],
            "metrics": [],
            "chart_types": [],
            "filters": []
        }
        
        user_lower = user_input.lower()
        
        # Extract branches with fuzzy matching
        for branch in branches:
            branch_lower = branch.lower()
            # Check for partial matches
            if any(word in user_lower for word in branch_lower.split()):
                entities["branches"].append(branch)
            # Check for common abbreviations
            elif "cse" in user_lower and "computer science" in branch_lower:
                entities["branches"].append(branch)
            elif "ece" in user_lower and "electronics" in branch_lower:
                entities["branches"].append(branch)
            elif "me" in user_lower and "mechanical" in branch_lower:
                entities["branches"].append(branch)
        
        # Extract years
        import re
        years = re.findall(r'\b(20\d{2})\b', user_input)
        entities["years"] = years
        
        # Extract metrics with better detection
        metrics = ["cgpa", "gpa", "grade", "attendance", "credits", "semester", "marks", "score"]
        for metric in metrics:
            if metric in user_lower:
                entities["metrics"].append(metric)
        
        # Extract chart types with better detection
        chart_types = ["line", "bar", "pie", "scatter", "trend", "distribution", "graph", "chart", "plot"]
        for chart_type in chart_types:
            if chart_type in user_lower:
                entities["chart_types"].append(chart_type)
        
        # Extract filter words
        filter_words = ["only", "just", "specific", "particular", "filter", "where"]
        for word in filter_words:
            if word in user_lower:
                entities["filters"].append(word)
        
        return entities
    
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
            if entities.get("branches"):
                branch = entities["branches"][0]
                cursor.execute("SELECT * FROM students WHERE branch = ?", (branch,))
            else:
                cursor.execute("SELECT * FROM students LIMIT 10")
        
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
            else:
                # Default query for general visualization requests
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
                labels = list(counter.keys())[:10]
                counts = list(counter.values())[:10]
                
                return {
                    "type": chart_type,
                    "title": f"Students by City",
                    "labels": labels,
                    "data": counts,
                    "colors": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"]
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
    
    # Test the agent
    response = agent.process_user_input("show me computer science engineering students")
    print("Agent Response:")
    print(json.dumps(response, indent=2))
