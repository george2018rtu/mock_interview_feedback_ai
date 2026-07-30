import csv
from pathlib import Path

# Path to the CSV file containing all interview questions
DATASET_PATH = Path("questions.csv")

def load_questions_from_csv():
    # Dictionary where each key is a category and the value is a list of questions
    categories = {}

     # Check if the CSV file exists before trying to open it
    if not DATASET_PATH.exists():
        print(f"Warning: File {DATASET_PATH} was not found. Returning empty dataset.")
        return categories

     # Open the CSV file for reading
    with open(DATASET_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

         # Loop through every row in the CSV
        for idx, row in enumerate(reader):

             # Get the question text and remove extra whitespace
            q_text = row.get("question", "").strip()

            # Skip rows that don't contain a question
            if not q_text:
                continue

            # Read the category, defaulting to "General" if blank
            category = row.get("category", "General").strip() or "General"

            # Read additional information about the question
            role = row.get("role", "").strip()
            difficulty = (row.get("difficulty") or "").strip()

            # Use the ID from the CSV if it exists. If it doesn't, generate one.
            q_id = row.get("id", "").strip() or f"q_{idx + 1}"

            # Read the expected concepts.
            concepts_raw = row.get("expected_concepts", "").strip()
            concepts = [c.strip() for c in concepts_raw.split("|") if c.strip()] if concepts_raw else []

            # Store all information for the current question in a dictionary
            question_item = {
                "id": q_id,
                "question": q_text,
                "category": category,
                "role": role,
                "difficulty": difficulty,
                "expected_concepts": concepts
            }

            # If this category hasn't been seen before, create an empty list for it
            if category not in categories:
                categories[category] = []

            # Add the current question to its category
            categories[category].append(question_item)

    # Return the completed dictionary of categorized questions
    return categories

# Load all questions when the program starts
questions = load_questions_from_csv()