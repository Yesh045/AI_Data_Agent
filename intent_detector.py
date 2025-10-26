"""
Intent Detection Module for AI Analyst Agent
Handles detection of user intents from natural language queries
"""

class IntentDetector:
    """Detects user intents from input text"""

    def __init__(self):
        self.intent_patterns = {
            "count_students": [
                "how many", "count", "number of", "total students",
                "how many students", "student count", "students count"
            ],
            "list_tables": [
                "list tables", "show tables", "what tables", "tables in database",
                "database tables", "available tables", "list all tables",
                "what are the tables", "show me tables", "all tables",
                "list all the tables", "what are all the tables", "show all tables"
            ],
            "graph_by_city": [
                "bar graph", "graph of students", "by city", "students and their city",
                "city", "city distribution", "students by city", "city-wise",
                "city based", "students per city", "city chart", "chart by city",
                "plot by city", "visualize by city", "graph by city"
            ],
            "enrollment_number": [
                "enrollment number", "enrollment id", "enrollment of",
                "find enrollment", "enrollment for", "what is enrollment",
                "what is", "enrollment details"
            ],
            "show_table": [
                "show me", "data inside", "table data", "table contents",
                "contents of", "inside table", "display table", "show data",
                "show table", "data of", "table of", "show data of",
                "show table data", "display table data"
            ],
            "analysis": [
                "analyze", "compare", "trend", "pattern", "correlation",
                "cgpa trend", "gpa trend", "gpa patterns", "cgpa patterns",
                "patterns", "distribution", "performance analysis",
                "statistics", "stats", "line graph", "make a line graph",
                "cgpa from", "gpa from", "cgpa of", "gpa of"
            ],
            "visualization": [
                "plot", "chart", "graph", "visualize", "create chart",
                "make chart", "line chart", "pie chart", "create a",
                "make a", "scatter plot", "histogram"
            ],
            "data_exploration": [
                "show", "list", "find", "get", "display", "view",
                "see", "tell me", "give me", "all students"
            ],
            "insights": [
                "why", "what does this mean", "insight", "explain",
                "understanding", "interpretation"
            ],
            "filtering": [
                "filter", "where", "only", "specific", "particular",
                "students with", "in", "from"
            ]
        }

        # Priority order for intents (more specific first)
        self.intent_priority = [
            "enrollment_number", "count_students", "list_tables",
            "show_table", "graph_by_city", "analysis", "visualization",
            "filtering", "insights", "data_exploration"
        ]

    def detect_intent(self, user_input: str) -> dict:
        """Analyze user input and return detected intents"""

        user_lower = user_input.lower()
        detected_intents = []

        # Check each intent pattern
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in user_lower for pattern in patterns):
                detected_intents.append(intent_type)

        # Remove duplicates and sort by priority
        detected_intents = list(set(detected_intents))
        detected_intents.sort(key=lambda x: self.intent_priority.index(x) if x in self.intent_priority else len(self.intent_priority))

        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else "data_exploration"

        # Calculate confidence
        confidence = min(0.9, 0.5 + (len(detected_intents) * 0.1))

        return {
            "primary_intent": primary_intent,
            "secondary_intents": detected_intents[1:],
            "all_detected": detected_intents,
            "confidence": confidence
        }
