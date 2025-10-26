from ai_agent import AIAnalystAgent

agent = AIAnalystAgent()

# Test pie chart for specific branches
test_queries = [
    'show me a pie chart of students by branch',
    'pie chart for computer science and mechanical engineering branches'
]

for query in test_queries:
    print(f'\n=== Testing: "{query}" ===')
    try:
        response = agent.process_user_input(query)
        print(f'Intent: {response["context"]["intent_confidence"]}')
        print(f'Data records: {len(response["data"])}')
        if response['visualization']:
            viz = response['visualization']
            print(f'Chart type: {viz["type"]}')
            print(f'Title: {viz["title"]}')
            print(f'Labels: {viz["labels"][:3]}...')  # Show first 3 labels
            print(f'Data points: {len(viz["data"])}')
        else:
            print('No visualization created')
    except Exception as e:
        print(f'Error: {e}')
