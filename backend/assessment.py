"""Server-side quiz discovery and score calculation."""

from typing import Any


def find_module_questions(content: dict[str, Any], module_key: str) -> list[dict[str, str]]:
    """Find quiz questions for a module in a course revision."""
    modules = [item for item in content.get("modules", []) if isinstance(item, dict)]
    for level in content.get("levels", []):
        if isinstance(level, dict):
            modules.extend(item for item in level.get("modules", []) if isinstance(item, dict))

    for module in modules:
        if module.get("key") != module_key:
            continue
        questions = []
        for activity in module.get("activities", []):
            if not isinstance(activity, dict) or activity.get("type") != "quiz":
                continue
            for question in activity.get("questions", []):
                if not isinstance(question, dict):
                    continue
                key = question.get("key")
                answer = question.get("answer")
                if isinstance(key, str) and isinstance(answer, str):
                    questions.append({"key": key, "answer": answer})
        return questions
    return []


def calculate_score(answers: dict[str, str], questions: list[dict[str, str]]) -> int:
    """Calculate a whole-number percentage from trusted revision answers."""
    if not questions:
        raise ValueError("This module has no assessable quiz questions.")
    correct = sum(
        answers.get(question["key"], "").strip().casefold() == question["answer"].strip().casefold()
        for question in questions
    )
    return round(correct * 100 / len(questions))