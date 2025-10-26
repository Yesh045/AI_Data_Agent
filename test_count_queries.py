#!/usr/bin/env python3
"""
Test script for the new count query functionality in ai_agent.py
"""

from ai_agent import AIAnalystAgent

def test_count_queries():
    agent = AIAnalystAgent()

    # Test queries for the new functionality
    test_queries = [
        # Course enrollment count queries
        "how many students in math",
        "number of students enrolled in physics",
        "students taking computer science",
        "count students in data structures",

        # City-based count queries
        "count students from Delhi",
        "students in city Mumbai",
        "how many students from Bangalore",

        # General count queries (existing functionality)
        "count students in computer science",
        "count students in mechanical engineering",

        # Edge cases
        "count students",  # No specific criteria
        "how many students in unknown course",  # Course that doesn't exist
    ]

    print("=== Testing New Count Query Functionality ===\n")

    for query in test_queries:
        print(f"Testing Query: '{query}'")
        try:
            response = agent.process_user_input(query)
            print(f"Intent: {response['context']['intent_confidence']}")
            print(f"Data Records: {len(response['data'])}")

            if response['data']:
                # Print first data record to see what was returned
                first_record = response['data'][0]
                print(f"Sample Data: {first_record}")

            print(f"Explanation: {response['explanation']}")
            print("-" * 60)

        except Exception as e:
            print(f"Error: {e}")
            print("-" * 60)

if __name__ == "__main__":
    test_count_queries()
