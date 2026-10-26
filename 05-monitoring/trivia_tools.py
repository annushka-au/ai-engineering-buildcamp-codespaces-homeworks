
"""
TRIVIA TOOLS
------------
Fetches trivia categories and multiple-choice questions from
the Open Trivia Database (https://opentdb.com/).

Dependencies: requests
Install: uv add requests

Functions:
- get_categories(): Returns available categories and their IDs.
- get_questions(amount, category, difficulty):
  Fetches questions with correct and incorrect answers.

Parameters:
- amount: Number of questions (1-10).
- category: Category ID from get_categories().
- difficulty: easy, medium, or hard.

Uses requests to fetch JSON data and html.unescape()
to convert HTML entities into readable text.
"""

import html
import requests


class TriviaTools:
    def get_categories(self) -> str:
        """Get all available trivia categories with their IDs."""
        url = "https://opentdb.com/api_category.php"
        data = requests.get(url).json()

        lines = []
        for cat in data['trivia_categories']:
            lines.append(f"{cat['id']}: {cat['name']}")

        return "\n".join(lines)

    def get_questions(self, amount: int, category: int, difficulty: str) -> str:
        """Fetch trivia questions.

        Args:
            amount: Number of questions (1-10)
            category: Category ID (use get_categories to see options)
            difficulty: easy, medium, or hard
        """
        params = {
            'amount': amount,
            'category': category,
            'difficulty': difficulty,
            'type': 'multiple',
        }

        url = "https://opentdb.com/api.php"
        data = requests.get(url, params=params).json()

        lines = []
        for i, q in enumerate(data['results'], 1):
            question = html.unescape(q['question'])
            correct = html.unescape(q['correct_answer'])
            wrong = [html.unescape(a) for a in q['incorrect_answers']]
            lines.append(f"Question {i}: {question}")
            lines.append(f"  Correct answer: {correct}")
            lines.append(f"  Wrong answers: {', '.join(wrong)}")
            lines.append("")

        return "\n".join(lines)
