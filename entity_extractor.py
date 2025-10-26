"""
Entity Extraction Module for AI Analyst Agent
Extracts relevant entities like branches, cities, metrics from user input
"""

import re
import sqlite3

class EntityExtractor:
    """Extracts entities from user input text"""

    def __init__(self, db_path="college.db"):
        self.db_path = db_path
        self.branches = self._load_branches()
        self.cities = [
            "mumbai", "delhi", "chennai", "kolkata", "pune",
            "bangalore", "hyderabad", "ahmedabad", "jaipur", "lucknow"
        ]
        self.metrics = ["cgpa", "gpa", "grade", "attendance", "credits", "semester", "marks", "score"]
        self.chart_types = ["line", "bar", "pie", "scatter", "trend", "distribution", "graph", "chart", "plot"]

    def _load_branches(self) -> list:
        """Load available branches from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT branch FROM students")
            branches = [row[0] for row in cursor.fetchall()]
            conn.close()
            return branches
        except:
            return ["Computer Science Engineering", "Electronics", "Mechanical", "Civil"]

    def extract_entities(self, user_input: str) -> dict:
        """Extract all relevant entities from user input"""

        user_lower = user_input.lower()

        entities = {
            "branches": self._extract_branches(user_lower),
            "years": self._extract_years(user_input),
            "cities": self._extract_cities(user_lower),
            "metrics": self._extract_metrics(user_lower),
            "chart_types": self._extract_chart_types(user_lower),
            "conditions": self._extract_conditions(user_lower),
            "table_names": self._extract_table_names(user_lower),
            "student_names": self._extract_student_names(user_input)
        }

        return entities

    def _extract_branches(self, user_lower: str) -> list:
        """Extract branch names from input"""
        found_branches = []

        for branch in self.branches:
            branch_lower = branch.lower()
            # Exact match
            if branch_lower in user_lower:
                found_branches.append(branch)
            # Common abbreviations and partial matches
            elif "cse" in user_lower and "computer science" in branch_lower:
                found_branches.append(branch)
            elif "ece" in user_lower and "electronics" in branch_lower:
                found_branches.append(branch)
            elif "me" in user_lower and "mechanical" in branch_lower:
                found_branches.append(branch)
            # Handle partial branch names
            elif "computer science" in user_lower and "computer science" in branch_lower:
                found_branches.append(branch)
            elif "science" in user_lower and "computer science" in branch_lower:
                found_branches.append(branch)

        return list(set(found_branches))  # Remove duplicates

    def _extract_years(self, user_input: str) -> list:
        """Extract years from input"""
        years = re.findall(r'\b(20\d{2})\b', user_input)
        return [int(year) for year in years]

    def _extract_cities(self, user_lower: str) -> list:
        """Extract city names from input"""
        found_cities = []
        for city in self.cities:
            if city in user_lower:
                found_cities.append(city.capitalize())
        return found_cities

    def _extract_metrics(self, user_lower: str) -> list:
        """Extract metrics from input"""
        found_metrics = []
        for metric in self.metrics:
            if metric in user_lower:
                found_metrics.append(metric)
        return found_metrics

    def _extract_chart_types(self, user_lower: str) -> list:
        """Extract chart types from input"""
        found_charts = []
        for chart_type in self.chart_types:
            if chart_type in user_lower:
                found_charts.append(chart_type)
        return found_charts

    def _extract_conditions(self, user_lower: str) -> list:
        """Extract conditions like 'cgpa > 8.5' from input"""
        conditions = []

        # Pattern for direct operators: attendance < 80, cgpa > 8.5
        direct_pattern = r'(\w+)\s*([<>=]+)\s*(\d+(?:\.\d+)?)'
        matches = re.findall(direct_pattern, user_lower)
        for match in matches:
            metric, operator, value = match
            if metric in self.metrics:
                conditions.append({
                    "metric": metric,
                    "operator": operator,
                    "value": float(value) if '.' in value else int(value)
                })

        # Pattern for natural language: "attendance is less than 80"
        nl_patterns = [
            (r'(\w+)\s+is\s+less\s+than\s+(\d+(?:\.\d+)?)', '<'),
            (r'(\w+)\s+is\s+greater\s+than\s+(\d+(?:\.\d+)?)', '>'),
            (r'(\w+)\s+is\s+equal\s+to\s+(\d+(?:\.\d+)?)', '='),
            (r'(\w+)\s+less\s+than\s+(\d+(?:\.\d+)?)', '<'),
            (r'(\w+)\s+greater\s+than\s+(\d+(?:\.\d+)?)', '>'),
            (r'(\w+)\s+equal\s+to\s+(\d+(?:\.\d+)?)', '=')
        ]

        for pattern, operator in nl_patterns:
            matches = re.findall(pattern, user_lower)
            for match in matches:
                metric, value = match
                if metric in self.metrics:
                    conditions.append({
                        "metric": metric,
                        "operator": operator,
                        "value": float(value) if '.' in value else int(value)
                    })

        return conditions

    def _extract_table_names(self, user_lower: str) -> list:
        """Extract table names from input"""
        table_keywords = ["students", "courses", "faculty", "enrollment", "student", "course", "enrollments"]
        found_tables = []

        for table in table_keywords:
            if table in user_lower:
                # Map to actual table names
                table_mapping = {
                    "student": "students",
                    "course": "courses",
                    "enrollments": "enrollment"
                }
                actual_table = table_mapping.get(table, table)
                found_tables.append(actual_table)

        return list(set(found_tables))

    def _extract_student_names(self, user_input: str) -> list:
        """Extract student names from input"""
        # This is a simple implementation - in a real system you'd have a name database
        # For now, we'll extract words that look like names after keywords

        name_indicators = ["enrollment of", "enrollment number of", "find enrollment", "enrollment for", "attendance of", "what is attendance"]
        names = []

        user_lower = user_input.lower()
        for indicator in name_indicators:
            if indicator in user_lower:
                parts = user_lower.split(indicator)
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    # Extract potential name (first few words)
                    words = name_part.split()[:3]  # Take first 3 words as potential name
                    if words:
                        names.append(" ".join(words).title())

        return names
