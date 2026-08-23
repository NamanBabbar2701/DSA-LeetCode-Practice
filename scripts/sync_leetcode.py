import re
import sys
from pathlib import Path

import requests


LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"


QUESTION_QUERY = """
query questionData($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionFrontendId
        title
        titleSlug
        difficulty
        content
        topicTags {
            name
            slug
        }
    }
}
"""


def get_repository_root():
    """
    Returns the repository root.

    The script expects to be run from the root of
    DSA-LeetCode-Practice.
    """
    return Path.cwd()


def extract_slug(folder_name):
    """
    Convert:

        0075-sort-colors

    into:

        sort-colors
    """

    match = re.match(r"^\d{1,4}-(.+)$", folder_name)

    if not match:
        return None

    return match.group(1)


def fetch_question(slug):
    """
    Fetch question information from LeetCode GraphQL API.
    """

    payload = {
        "query": QUESTION_QUERY,
        "variables": {
            "titleSlug": slug
        }
    }

    response = requests.post(
        LEETCODE_GRAPHQL_URL,
        json=payload,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    question = data.get("data", {}).get("question")

    if not question:
        return None

    return question


def create_question_markdown(folder, question):
    """
    Create Question.md inside the problem folder.
    """

    question_file = folder / "Question.md"

    topics = question.get("topicTags", [])

    topic_names = [
        topic["name"]
        for topic in topics
    ]

    topics_text = ", ".join(topic_names)

    content = f"""# {question['questionFrontendId']}. {question['title']}

**Difficulty:** {question['difficulty']}

**LeetCode:** https://leetcode.com/problems/{question['titleSlug']}/

**Topics:** {topics_text}

---

{question['content']}
"""

    question_file.write_text(
        content,
        encoding="utf-8"
    )

    return question_file


def process_repository(repo_root):
    """
    Find all LeetCode problem folders and create
    Question.md where it does not already exist.
    """

    processed = 0
    skipped = 0
    failed = 0

    for folder in sorted(repo_root.iterdir()):

        if not folder.is_dir():
            continue

        slug = extract_slug(folder.name)

        if not slug:
            continue

        # Make sure this actually looks like a LeetCode
        # solution folder.
        solution_files = list(folder.glob("*.*"))

        if not solution_files:
            continue

        question_file = folder / "Question.md"

        if question_file.exists():
            print(f"[SKIP] {folder.name} - Question.md already exists")
            skipped += 1
            continue

        print(f"[FETCH] {folder.name} -> {slug}")

        try:
            question = fetch_question(slug)

            if not question:
                print(
                    f"[ERROR] Could not find LeetCode problem: {slug}"
                )
                failed += 1
                continue

            created_file = create_question_markdown(
                folder,
                question
            )

            print(f"[CREATED] {created_file}")

            processed += 1

        except Exception as error:
            print(
                f"[ERROR] {folder.name}: {error}"
            )
            failed += 1

    print()
    print("===================================")
    print("LeetCode Question Sync Complete")
    print("===================================")
    print(f"Created : {processed}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")


def main():
    repo_root = get_repository_root()

    print(f"Repository: {repo_root}")
    print()

    process_repository(repo_root)


if __name__ == "__main__":
    main()
