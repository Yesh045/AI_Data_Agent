"""
Query Builder Module for AI Analyst Agent
Builds SQL queries based on detected intents and entities
"""

import sqlite3
from typing import List, Dict, Any, Optional

class QueryBuilder:
    """Builds SQL queries from intents and entities"""

    def __init__(self, db_path="college.db"):
        self.db_path = db_path

    def build_query(self, intent: str, entities: dict, user_input: str = "") -> str:
        """Build appropriate SQL query based on intent and entities"""

        if intent == "count_students":
            return self._build_count_query(entities)
        elif intent == "list_tables":
            return self._build_list_tables_query()
        elif intent == "graph_by_city":
            return self._build_city_graph_query(entities)
        elif intent == "enrollment_number":
            return self._build_enrollment_query(entities, user_input)
        elif intent == "show_table":
            return self._build_show_table_query(entities, user_input)
        elif intent == "analysis":
            return self._build_analysis_query(entities)
        elif intent == "visualization":
            return self._build_visualization_query(entities)
        elif intent == "data_exploration":
            return self._build_exploration_query(entities)
        elif intent == "filtering":
            return self._build_filter_query(entities)
        else:
            return self._build_default_query(entities)

    def _build_count_query(self, entities: dict) -> str:
        """Build count query for students"""
        query = "SELECT COUNT(*) as count FROM students WHERE 1=1"
        params = []

        if entities.get("branches"):
            query += " AND branch = ?"
            params.append(entities["branches"][0])

        if entities.get("cities"):
            query += " AND address = ?"
            params.append(entities["cities"][0])

        if entities.get("conditions"):
            for condition in entities["conditions"]:
                column = self._map_metric_to_column(condition["metric"])
                if column:
                    query += f" AND {column} {condition['operator']} ?"
                    params.append(condition["value"])

        if entities.get("years"):
            query += " AND admission_year = ?"
            params.append(entities["years"][0])

        return query, params

    def _build_list_tables_query(self) -> tuple:
        """Build query to list all tables"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        return query, []

    def _build_city_graph_query(self, entities: dict) -> tuple:
        """Build query for city-based graph"""
        query = "SELECT address, COUNT(*) as count FROM students WHERE 1=1"
        params = []

        if entities.get("branches"):
            query += " AND branch = ?"
            params.append(entities["branches"][0])

        if entities.get("cities"):
            query += " AND address = ?"
            params.append(entities["cities"][0])

        query += " GROUP BY address ORDER BY count DESC"
        return query, params

    def _build_enrollment_query(self, entities: dict, user_input: str) -> tuple:
        """Build query for enrollment information"""
        # Try to find student by name
        student_names = entities.get("student_names", [])
        if student_names:
            name = student_names[0]
            query = """
                SELECT s.name, s.student_id, e.course_id, e.semester, e.grade
                FROM students s
                LEFT JOIN enrollment e ON s.student_id = e.student_id
                WHERE LOWER(s.name) LIKE ?
            """
            params = [f"%{name.lower()}%"]
        else:
            # Default: show enrollment table
            query = "SELECT * FROM enrollment LIMIT 20"
            params = []

        return query, params

    def _build_show_table_query(self, entities: dict, user_input: str) -> tuple:
        """Build query to show table contents"""
        table_names = entities.get("table_names", [])
        if table_names:
            table = table_names[0]
            query = f"SELECT * FROM {table} LIMIT 50"
            params = []
        else:
            # Default to students table
            query = "SELECT * FROM students LIMIT 50"
            params = []

        return query, params

    def _build_analysis_query(self, entities: dict) -> tuple:
        """Build analysis query"""
        if entities.get("branches") and entities.get("metrics"):
            branch = entities["branches"][0]
            metric = entities["metrics"][0]
            column = self._map_metric_to_column(metric)

            if column and metric in ["cgpa", "gpa"]:
                query = f"""
                    SELECT admission_year, AVG({column}) as avg_{metric},
                           COUNT(*) as student_count
                    FROM students
                    WHERE branch = ?
                    GROUP BY admission_year
                    ORDER BY admission_year
                """
                params = [branch]
            else:
                query = f"SELECT * FROM students WHERE branch = ? LIMIT 50"
                params = [branch]
        else:
            query = "SELECT * FROM students LIMIT 50"
            params = []

        return query, params

    def _build_visualization_query(self, entities: dict) -> tuple:
        """Build visualization query"""
        if entities.get("branches"):
            branch = entities["branches"][0]
            query = "SELECT * FROM students WHERE branch = ?"
            params = [branch]
        elif entities.get("cities"):
            city = entities["cities"][0]
            query = "SELECT * FROM students WHERE address = ?"
            params = [city]
        else:
            query = "SELECT * FROM students LIMIT 100"
            params = []

        return query, params

    def _build_exploration_query(self, entities: dict) -> tuple:
        """Build exploration query"""
        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if entities.get("branches"):
            query += " AND branch = ?"
            params.append(entities["branches"][0])

        if entities.get("cities"):
            query += " AND address = ?"
            params.append(entities["cities"][0])

        if entities.get("conditions"):
            for condition in entities["conditions"]:
                column = self._map_metric_to_column(condition["metric"])
                if column:
                    query += f" AND {column} {condition['operator']} ?"
                    params.append(condition["value"])

        if entities.get("years"):
            query += " AND admission_year = ?"
            params.append(entities["years"][0])

        query += " LIMIT 50"
        return query, params

    def _build_filter_query(self, entities: dict) -> tuple:
        """Build filter query"""
        return self._build_exploration_query(entities)

    def _build_default_query(self, entities: dict) -> tuple:
        """Build default query"""
        return "SELECT * FROM students LIMIT 20", []

    def _map_metric_to_column(self, metric: str) -> Optional[str]:
        """Map metric names to database columns"""
        mapping = {
            "cgpa": "cgpa",
            "gpa": "cgpa",
            "grade": "cgpa",  # Approximation
            "attendance": "cgpa",  # No attendance column, use cgpa as fallback
            "credits": "semester",  # Approximation
            "semester": "semester",
            "marks": "cgpa",  # Approximation
            "score": "cgpa"  # Approximation
        }
        return mapping.get(metric.lower())

    def execute_query(self, query: str, params: list = None) -> List[Dict[str, Any]]:
        """Execute the query and return results"""
        if params is None:
            params = []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(query, params)
            results = cursor.fetchall()
            data = [dict(row) for row in results]

            conn.close()
            return data
        except Exception as e:
            print(f"Query execution error: {e}")
            return []
