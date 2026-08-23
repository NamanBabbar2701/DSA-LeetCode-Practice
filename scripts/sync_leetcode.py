import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# Configuration
# ============================================================

load_dotenv()

LEETCODE_SESSION = os.getenv("LEETCODE_SESSION")
LEETCODE_CSRF_TOKEN = os.getenv("LEETCODE_CSRF_TOKEN")

GRAPHQL_URL = "https://leetcode.com/graphql"

REPOSITORY_ROOT = (
    Path(__file__).resolve().parent.parent
)

METRICS_DIR = REPOSITORY_ROOT / "metrics"

SUBMISSIONS_FILE = (
    METRICS_DIR / "submissions.json"
)

STATS_FILE = (
    METRICS_DIR / "stats.json"
)


# ============================================================
# Validation
# ============================================================

if not LEETCODE_SESSION:
    raise RuntimeError(
        "LEETCODE_SESSION is missing from .env"
    )

if not LEETCODE_CSRF_TOKEN:
    raise RuntimeError(
        "LEETCODE_CSRF_TOKEN is missing from .env"
    )


# ============================================================
# HTTP Headers
# ============================================================

HEADERS = {
    "Content-Type": "application/json",

    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),

    "Referer": "https://leetcode.com/",
    "Origin": "https://leetcode.com",

    "x-csrftoken": LEETCODE_CSRF_TOKEN,

    "Cookie": (
        f"LEETCODE_SESSION={LEETCODE_SESSION}; "
        f"csrftoken={LEETCODE_CSRF_TOKEN}"
    ),
}


# ============================================================
# GraphQL Queries
# ============================================================

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


SUBMISSION_QUERY = """
query submissionList(
    $offset: Int!
    $limit: Int!
) {
    submissionList(
        offset: $offset
        limit: $limit
    ) {
        hasNext

        submissions {
            id
            title
            titleSlug
            statusDisplay
            lang
            runtime
            memory
            timestamp
        }
    }
}
"""


# ============================================================
# Generic GraphQL Request
# ============================================================

def graphql_request(query, variables):

    response = requests.post(
        GRAPHQL_URL,
        json={
            "query": query,
            "variables": variables,
        },
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(
            data["errors"]
        )

    return data


# ============================================================
# Fetch Question
# ============================================================

def fetch_question(slug):

    data = graphql_request(
        QUESTION_QUERY,
        {
            "titleSlug": slug
        },
    )

    return (
        data
        .get("data", {})
        .get("question")
    )


# ============================================================
# Fetch All Recent Submissions
# ============================================================

def fetch_submissions(required_slugs):
    """
    Fetch LeetCode submissions until we have found
    the latest submission for every problem that exists
    in the GitHub repository.
    """

    submissions = []

    found_slugs = set()

    offset = 0
    limit = 100

    while True:

        print(
            f"[FETCH] Submissions "
            f"offset={offset}"
        )

        data = graphql_request(
            SUBMISSION_QUERY,
            {
                "offset": offset,
                "limit": limit,
            },
        )

        submission_data = (
            data
            .get("data", {})
            .get("submissionList")
        )

        if not submission_data:
            break

        batch = submission_data.get(
            "submissions",
            []
        )

        submissions.extend(batch)

        # ----------------------------------------
        # Find problems we already have
        # ----------------------------------------

        for submission in batch:

            slug = submission[
                "titleSlug"
            ]

            if slug in required_slugs:

                found_slugs.add(slug)

        # ----------------------------------------
        # Stop when every GitHub problem
        # has been found
        # ----------------------------------------

        if found_slugs >= required_slugs:

            print(
                "[INFO] Found latest submission "
                "for every GitHub problem."
            )

            break

        # ----------------------------------------
        # No more submissions available
        # ----------------------------------------

        has_next = submission_data.get(
            "hasNext",
            False
        )

        if not has_next:
            break

        offset += limit

    return submissions

# ============================================================
# Find GitHub Problems
# ============================================================

def get_github_problems():

    problems = {}

    for folder in sorted(
        REPOSITORY_ROOT.iterdir()
    ):

        if not folder.is_dir():
            continue

        if folder.name in {
            "scripts",
            "metrics",
            ".git",
        }:
            continue

        match = re.match(
            r"^(\d{1,4})-(.+)$",
            folder.name,
        )

        if not match:
            continue

        problem_number = int(
            match.group(1)
        )

        slug = match.group(2)

        problems[slug] = {
            "number": problem_number,
            "folder": folder,
        }

    return problems


# ============================================================
# Create Question.md
# ============================================================

def create_question_file(
    folder,
    question,
):

    question_file = (
        folder / "Question.md"
    )

    # Don't overwrite an existing question.
    if question_file.exists():

        print(
            f"[SKIP] Question.md exists: "
            f"{folder.name}"
        )

        return

    topics = question.get(
        "topicTags",
        []
    )

    topic_names = [
        topic["name"]
        for topic in topics
    ]

    topics_text = ", ".join(
        topic_names
    )

    content = f"""# {question["questionFrontendId"]}. {question["title"]}

**Difficulty:** {question["difficulty"]}

**LeetCode:** https://leetcode.com/problems/{question["titleSlug"]}/

**Topics:** {topics_text}

---

{question["content"]}
"""

    question_file.write_text(
        content,
        encoding="utf-8",
    )

    print(
        f"[CREATED] Question.md: "
        f"{folder.name}"
    )


# ============================================================
# Find Latest Submission
# ============================================================

def get_latest_submissions(
    github_problems,
    submissions,
):

    latest = {}

    # LeetCode returns newest submissions first.
    for submission in submissions:

        slug = submission[
            "titleSlug"
        ]

        # Ignore problems that aren't
        # part of our GitHub repository.
        if slug not in github_problems:
            continue

        # First occurrence is the latest.
        if slug not in latest:

            latest[slug] = submission

    return latest


# ============================================================
# Build Submission Record
# ============================================================

def build_submission_record(
    slug,
    question,
    submission,
    github_problem,
):

    return {
        "problemNumber": int(
            question[
                "questionFrontendId"
            ]
        ),

        "title": question[
            "title"
        ],

        "slug": slug,

        "folder": github_problem[
            "folder"
        ].name,

        "difficulty": question[
            "difficulty"
        ],

        "status": submission[
            "statusDisplay"
        ],

        "language": submission[
            "lang"
        ],

        "runtime": submission[
            "runtime"
        ],

        "memory": submission[
            "memory"
        ],

        "submissionId": submission[
            "id"
        ],

        "timestamp": submission[
            "timestamp"
        ],
    }


# ============================================================
# Load Existing Submissions
# ============================================================

def load_existing_submissions():

    if not SUBMISSIONS_FILE.exists():

        return {}

    try:

        with open(
            SUBMISSIONS_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return data.get(
            "submissions",
            {}
        )

    except json.JSONDecodeError:

        print(
            "[WARNING] Invalid "
            "submissions.json"
        )

        return {}


# ============================================================
# Save Submissions
# ============================================================

def save_submissions(
    submissions,
):

    METRICS_DIR.mkdir(
        exist_ok=True
    )

    data = {
        "submissions": submissions
    }

    with open(
        SUBMISSIONS_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"[SAVED] {SUBMISSIONS_FILE}"
    )


# ============================================================
# Generate Global Statistics
# ============================================================

def generate_stats(
    submissions,
):

    total_problems = len(
        submissions
    )

    difficulty = {
        "Easy": 0,
        "Medium": 0,
        "Hard": 0,
    }

    statuses = {
        "Accepted": 0,
        "Wrong Answer": 0,
        "Time Limit Exceeded": 0,
        "Memory Limit Exceeded": 0,
        "Runtime Error": 0,
        "Compile Error": 0,
        "Other": 0,
    }

    languages = {}

    for submission in (
        submissions.values()
    ):

        # ----------------------------------------
        # Difficulty
        # ----------------------------------------

        problem_difficulty = (
            submission.get(
                "difficulty"
            )
        )

        if problem_difficulty in difficulty:

            difficulty[
                problem_difficulty
            ] += 1

        # ----------------------------------------
        # Status
        # ----------------------------------------

        status = submission.get(
            "status",
            "Other",
        )

        if status in statuses:

            statuses[status] += 1

        else:

            statuses["Other"] += 1

        # ----------------------------------------
        # Language
        # ----------------------------------------

        language = submission.get(
            "language",
            "Unknown",
        )

        languages[language] = (
            languages.get(
                language,
                0,
            ) + 1
        )

    # --------------------------------------------
    # Acceptance Rate
    # --------------------------------------------

    accepted = statuses[
        "Accepted"
    ]

    if total_problems > 0:

        acceptance_rate = round(
            (
                accepted
                / total_problems
            ) * 100,
            2,
        )

    else:

        acceptance_rate = 0.0

    # --------------------------------------------
    # Final object
    # --------------------------------------------

    return {
        "totalProblems": total_problems,

        "difficulty": difficulty,

        "statuses": statuses,

        "languages": languages,

        "acceptanceRate": acceptance_rate,
    }


# ============================================================
# Save Statistics
# ============================================================

def save_stats(
    stats,
):

    METRICS_DIR.mkdir(
        exist_ok=True
    )

    with open(
        STATS_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            stats,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"[SAVED] {STATS_FILE}"
    )

def generate_readme(submissions, stats):
    """
    Generate the root README.md from submissions.json
    and stats.json data.
    """

    readme_file = REPOSITORY_ROOT / "README.md"

    total = stats["totalProblems"]

    difficulty = stats["difficulty"]
    statuses = stats["statuses"]
    languages = stats["languages"]

    acceptance_rate = stats["acceptanceRate"]

    difficulty_emoji = {
        "Easy": "🟢",
        "Medium": "🟡",
        "Hard": "🔴",
    }

    rows = []

    for submission in sorted(
        submissions.values(),
        key=lambda item: item["problemNumber"]
    ):

        number = submission["problemNumber"]
        title = submission["title"]
        slug = submission["slug"]
        difficulty_name = submission["difficulty"]
        language = submission["language"]
        runtime = submission["runtime"]
        memory = submission["memory"]
        status = submission["status"]

        emoji = difficulty_emoji.get(
            difficulty_name,
            "⚪"
        )

        status_display = (
            "✅ Accepted"
            if status == "Accepted"
            else status
        )

        rows.append(
            f"| {number} | "
            f"[{title}](./{submission['folder']}/) | "
            f"{emoji} {difficulty_name} | "
            f"{language} | "
            f"{runtime} | "
            f"{memory} | "
            f"{status_display} |"
        )

    problem_rows = "\n".join(rows)

    language_rows = "\n".join(
        f"| {language} | {count} |"
        for language, count in sorted(
            languages.items(),
            key=lambda item: (-item[1], item[0])
        )
    )

    content = f"""# DSA LeetCode Practice

A collection of my LeetCode solutions, questions, and submission performance.

> Automatically synchronized from LeetCode using GitHub Actions.

## 📊 Progress

| Metric | Count |
|---|---:|
| **Total Problems** | **{total}** |
| Easy | {difficulty["Easy"]} |
| Medium | {difficulty["Medium"]} |
| Hard | {difficulty["Hard"]} |

### Acceptance

**{acceptance_rate}%**

| Status | Count |
|---|---:|
| ✅ Accepted | {statuses["Accepted"]} |
| ❌ Wrong Answer | {statuses["Wrong Answer"]} |
| ⏱️ Time Limit Exceeded | {statuses["Time Limit Exceeded"]} |
| 💾 Memory Limit Exceeded | {statuses["Memory Limit Exceeded"]} |
| ⚠️ Runtime Error | {statuses["Runtime Error"]} |
| 🔧 Compile Error | {statuses["Compile Error"]} |
| Other | {statuses["Other"]} |

## 💻 Languages

| Language | Problems |
|---|---:|
{language_rows}

## 🧩 Problems

| # | Problem | Difficulty | Language | Runtime | Memory | Status |
|---:|---|---|---|---:|---:|---|
{problem_rows}

## 📁 Repository Structure

```text
DSA-LeetCode-Practice/
│
├── 0001-problem-name/
│   ├── Question.md
│   └── solution.java
│
├── ...
│
├── metrics/
│   ├── submissions.json
│   └── stats.json
│
├── scripts/
│   └── sync_leetcode.py
│
└── README.md
🎯 Goal

Consistently practice Data Structures & Algorithms and maintain a record of my problem-solving progress.
"""
    readme_file.write_text(
        content,
        encoding="utf-8"
    )

    print(
        f"[SAVED] {readme_file}"
    )

# ============================================================
# Main
# ============================================================

def main():

    print()
    print(
        "=========================================="
    )
    print(
        "       LeetCode Repository Sync"
    )
    print(
        "=========================================="
    )
    print()

    # --------------------------------------------------------
    # 1. Find GitHub problems
    # --------------------------------------------------------

    github_problems = (
        get_github_problems()
    )

    print(
        f"GitHub problems found: "
        f"{len(github_problems)}"
    )

    print()

    # --------------------------------------------------------
    # 2. Fetch question information
    # --------------------------------------------------------

    print(
        "Fetching question information..."
    )

    questions = {}

    for slug, problem in (
        github_problems.items()
    ):

        try:

            question = fetch_question(
                slug
            )

            if not question:

                print(
                    f"[ERROR] Question not found: "
                    f"{slug}"
                )

                continue

            questions[slug] = question

            create_question_file(
                problem["folder"],
                question,
            )

        except Exception as error:

            print(
                f"[ERROR] {slug}: "
                f"{error}"
            )

    print()

    # --------------------------------------------------------
    # 3. Fetch submissions
    # --------------------------------------------------------

    print(
        "Fetching submission history..."
    )

    required_slugs = set(
        github_problems.keys()
    )
    
    submissions = fetch_submissions(
        required_slugs
    )

    print(
        f"Submissions received: "
        f"{len(submissions)}"
    )

    print()

    # --------------------------------------------------------
    # 4. Get latest submission
    # --------------------------------------------------------

    latest = get_latest_submissions(
        github_problems,
        submissions,
    )

    print(
        f"GitHub problems with submissions: "
        f"{len(latest)}"
    )

    print()

    # --------------------------------------------------------
    # 5. Load existing metrics
    # --------------------------------------------------------

    existing = (
        load_existing_submissions()
    )

    # --------------------------------------------------------
    # 6. Update metrics
    # --------------------------------------------------------

    for slug, submission in (
        latest.items()
    ):

        question = questions.get(
            slug
        )

        if not question:

            print(
                f"[SKIP] No question data: "
                f"{slug}"
            )

            continue

        problem = github_problems[
            slug
        ]

        existing[slug] = (
            build_submission_record(
                slug,
                question,
                submission,
                problem,
            )
        )

        print(
            f"[UPDATED] "
            f"#{problem['number']:04d} "
            f"{question['title']}"
        )

    # --------------------------------------------------------
    # 7. Remove problems no longer in GitHub
    # --------------------------------------------------------

    github_slugs = set(
        github_problems.keys()
    )

    existing = {
        slug: record
        for slug, record in (
            existing.items()
        )
        if slug in github_slugs
    }

    # --------------------------------------------------------
    # 8. Save submissions.json
    # --------------------------------------------------------

    save_submissions(
        existing
    )

    # --------------------------------------------------------
    # 9. Generate stats.json
    # --------------------------------------------------------

    stats = generate_stats(
        existing
    )

    save_stats(
        stats
    )
    
    generate_readme(
        existing,
        stats
    )

    # --------------------------------------------------------
    # Done
    # --------------------------------------------------------

    print()
    print(
        "=========================================="
    )
    print(
        "              Sync Complete"
    )
    print(
        "=========================================="
    )
    print()


if __name__ == "__main__":
    main()