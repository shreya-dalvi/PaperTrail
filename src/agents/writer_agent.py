import os
import json
from datetime import date
from groq import Groq
from dotenv import load_dotenv
from analyst_agent import run_analysis

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

REPORT_PROMPT = """You are writing a short, honest policy-brief style report about exam paper leak incidents in India, based on the structured data below.

Data:
{data}

Write a report with these sections:
1. **Overview** — total incidents tracked, and the overall trend
2. **State-wise Hotspots** — which states show the most incidents, and any plausible context
3. **Policy Impact: The 2024 Public Examinations Act** — present the before/after numbers honestly, including the sample-size caveat provided in the data. Do NOT overstate causality — explicitly note that the drop in confirmed-rate could reflect either fewer verified leaks or more incidents still under investigation.
4. **Outlook** — the forecast numbers, framed as a directional estimate, not a precise prediction.

Keep it factual, concise (under 400 words), and avoid sensationalism. Do not invent any numbers not present in the data.
"""

def generate_report():
    data = run_analysis()
    prompt = REPORT_PROMPT.format(data=json.dumps(data, indent=2, default=str))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    report_text = response.choices[0].message.content.strip()

    today = date.today().isoformat()
    filename = f"reports/policy_brief_{today}.md"
    os.makedirs("reports", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# PaperTrail Policy Brief — {today}\n\n")
        f.write(report_text)

    print(f"Report saved to {filename}")
    return filename

if __name__ == "__main__":
    generate_report()