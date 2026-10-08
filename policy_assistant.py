import os
import csv
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Setup ----------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

POLICY_FILE = "ai_policy.md"
LOG_FILE = "policy_audit_log.csv"

policy_text = Path(POLICY_FILE).read_text(encoding="utf-8")

SYSTEM_PROMPT = f"""You are SIRDC's AI Governance Assistant.
Answer ONLY using the policy below. Cite section numbers like [Section 4.1].
If the answer is not in the policy, say:
"This is not covered in the policy. Recommend escalating to the AI Review Board."
Never invent rules. Keep answers under 120 words.

POLICY:
{policy_text}
"""


def log_interaction(question: str, answer: str) -> None:
    """Append every Q&A to a CSV audit log."""
    new_file = not Path(LOG_FILE).exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "question", "answer"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            question.replace("\n", " "),
            answer.replace("\n", " "),
        ])


def ask(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
    )
    answer = response.choices[0].message.content.strip()
    log_interaction(question, answer)
    return answer


if __name__ == "__main__":
    print("SIRDC AI Governance Assistant — type 'exit' to quit.\n")
    while True:
        q = input("You: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        try:
            print(f"\nAssistant: {ask(q)}\n")
        except Exception as e:
            print(f"\n[Error] {e}\n")