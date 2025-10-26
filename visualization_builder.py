"""
Visualization Builder Module for AI Analyst Agent
Creates appropriate visualizations based on data and intent
"""

from typing import List, Dict, Any, Optional
from collections import Counter

class VisualizationBuilder:
    """Creates visualizations from data"""

    def __init__(self):
        self.chart_colors = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
            "#FF9F40", "#FF6384", "#C9CBCF", "#FF6384", "#36A2EB"
        ]

    def create_visualization(self, data: List[Dict[str, Any]], intent: str, entities: dict, user_input: str = "") -> Optional[Dict[str, Any]]:
        """Create appropriate visualization based on intent and data"""

        if not data:
            return None

        if intent == "graph_by_city":
            return self._create_city_bar_chart(data, entities)
        elif intent == "analysis":
            return self._create_analysis_chart(data, entities)
        elif intent == "visualization":
            return self._create_custom_chart(data, entities, user_input)
        elif intent == "count_students":
            return self._create_count_chart(data)
        else:
            return self._create_default_chart(data, entities, user_input)

    def _create_city_bar_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create bar chart for city distribution"""
        # Check if data has address column
        if not data or "address" not in data[0]:
            return None

        # Count students by city
        city_counts = Counter()
        for row in data:
            city = row.get("address", "Unknown")
            if city:
                city_counts[city] += 1

        if not city_counts:
            return None

        # Sort by count descending
        sorted_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "type": "bar",
            "title": "Students by City",
            "labels": [city for city, count in sorted_cities],
            "data": [count for city, count in sorted_cities],
            "colors": self.chart_colors[:len(sorted_cities)],
            "x_label": "City",
            "y_label": "Number of Students"
        }

    def _create_analysis_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create analysis chart (trends, patterns)"""
        if not data:
            return None

        # Check for CGPA trend data
        if "avg_cgpa" in data[0] and "admission_year" in data[0]:
            return self._create_cgpa_trend_chart(data)

        # Check for time-based data
        if "admission_year" in data[0] and "cgpa" in data[0]:
            return self._create_cgpa_trend_chart(data)

        # Default to distribution chart
        return self._create_distribution_chart(data, entities)

    def _create_cgpa_trend_chart(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create CGPA trend chart"""
        # Group by year if needed
        year_data = {}
        for row in data:
            if "avg_cgpa" in row and "admission_year" in row:
                year = row["admission_year"]
                cgpa = row["avg_cgpa"]
            elif "cgpa" in row and "admission_year" in row:
                year = row["admission_year"]
                cgpa = row["cgpa"]
                if year not in year_data:
                    year_data[year] = []
                year_data[year].append(cgpa)
            else:
                continue

        # Calculate averages if raw data
        if year_data:
            avg_data = []
            for year in sorted(year_data.keys()):
                if isinstance(year_data[year], list):
                    avg_cgpa = sum(year_data[year]) / len(year_data[year])
                    avg_data.append({"year": year, "avg_cgpa": round(avg_cgpa, 2)})
                else:
                    avg_data.append({"year": year, "avg_cgpa": year_data[year]})

            return {
                "type": "line",
                "title": "CGPA Trends by Admission Year",
                "labels": [str(item["year"]) for item in avg_data],
                "data": [item["avg_cgpa"] for item in avg_data],
                "colors": ["#3b82f6"],
                "x_label": "Admission Year",
                "y_label": "Average CGPA"
            }

        return None

    def _create_custom_chart(self, data: List[Dict[str, Any]], entities: dict, user_input: str) -> Optional[Dict[str, Any]]:
        """Create custom chart based on user request"""
        chart_types = entities.get("chart_types", [])
        if not chart_types:
            return self._create_default_chart(data, entities, user_input)

        chart_type = chart_types[0].lower()

        if chart_type == "line":
            return self._create_line_chart(data, entities)
        elif chart_type == "pie":
            return self._create_pie_chart(data, entities)
        elif chart_type == "bar":
            return self._create_bar_chart(data, entities)
        else:
            return self._create_default_chart(data, entities, user_input)

    def _create_count_chart(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create chart for count results"""
        if not data or "count" not in data[0]:
            return None

        count_value = data[0]["count"]

        return {
            "type": "metric",
            "title": "Student Count",
            "value": count_value,
            "icon": "👥",
            "color": "#3b82f6"
        }

    def _create_line_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create line chart"""
        if "admission_year" in data[0] and "cgpa" in data[0]:
            return self._create_cgpa_trend_chart(data)
        return None

    def _create_pie_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create pie chart"""
        # Find categorical column
        categorical_cols = []
        for col in data[0].keys():
            if not isinstance(data[0][col], (int, float)) or data[0][col] is None:
                categorical_cols.append(col)

        if not categorical_cols:
            return None

        # Use first categorical column
        cat_col = categorical_cols[0]
        counts = Counter(row[cat_col] for row in data if row[cat_col])

        return {
            "type": "pie",
            "title": f"Distribution by {cat_col.title()}",
            "labels": list(counts.keys()),
            "data": list(counts.values()),
            "colors": self.chart_colors[:len(counts)]
        }

    def _create_bar_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create bar chart"""
        return self._create_city_bar_chart(data, entities) or self._create_distribution_chart(data, entities)

    def _create_distribution_chart(self, data: List[Dict[str, Any]], entities: dict) -> Optional[Dict[str, Any]]:
        """Create distribution chart"""
        if not data:
            return None

        # Find suitable columns
        columns = list(data[0].keys())
        categorical_cols = [col for col in columns if not isinstance(data[0][col], (int, float)) or data[0][col] is None]

        if categorical_cols:
            cat_col = categorical_cols[0]
            counts = Counter(str(row[cat_col]) for row in data)
            top_items = counts.most_common(10)  # Top 10

            return {
                "type": "bar",
                "title": f"Distribution of {cat_col.title()}",
                "labels": [item[0] for item in top_items],
                "data": [item[1] for item in top_items],
                "colors": self.chart_colors[:len(top_items)],
                "x_label": cat_col.title(),
                "y_label": "Count"
            }

        return None

    def _create_default_chart(self, data: List[Dict[str, Any]], entities: dict, user_input: str) -> Optional[Dict[str, Any]]:
        """Create default chart based on data structure"""
        if not data:
            return None

        # Check for city-related queries
        if "city" in user_input.lower() or "address" in user_input.lower():
            return self._create_city_bar_chart(data, entities)

        # Check for count data
        if len(data) == 1 and "count" in data[0]:
            return self._create_count_chart(data)

        # Default to distribution chart
        return self._create_distribution_chart(data, entities)
