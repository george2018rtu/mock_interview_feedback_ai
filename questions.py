import csv
from pathlib import Path

DATASET_PATH = Path("questions.csv")

def load_questions_from_csv():
    categories = {}

    if not DATASET_PATH.exists():
        print(f"Warning: File {DATASET_PATH} was not found. Returning empty dataset.")
        return categories

    with open(DATASET_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        for idx, row in enumerate(reader):
            q_text = row.get("question", "").strip()
            if not q_text:
                continue

            category = row.get("category", "General").strip() or "General"
            role = row.get("role", "").strip()
            difficulty = row.get("difficulty", "").strip()

            concepts = []
            if role:
                concepts.append(role)
            if difficulty:
                concepts.append(f"{difficulty} level")

            question_item = {
                "id": f"q_{idx + 1}",
                "question": q_text,
                "category": category,
                "role": role,
                "difficulty": difficulty,
                "expected_concepts": concepts
            }

            if category not in categories:
                categories[category] = []
            categories[category].append(question_item)

    return categories

questions = load_questions_from_csv()