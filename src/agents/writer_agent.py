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
2. **State-wise Hotspots** — which states show the most incidents
3. **Leak Mechanisms** — the breakdown of how leaks occurred, noting many cases are unspecified due to limited source detail
4. **Conducting Bodies** — which exam bodies appear most often
5. **Scale of Impact** — highlight the top 2-3 highest-impact incidents by aspirants affected
6. **UPA vs NDA Era Comparison** — present the average incidents/year for each era, normalized by years, and note that rising media/reporting attention over time could also explain part of the difference, not just underlying leak frequency
7. **Policy Impact: The 2024 Public Examinations Act** — present the before/after numbers honestly, including the sample-size caveat. Do NOT overstate causality.
8. **Outlook** — the forecast numbers, framed as a directional estimate.

Keep it factual, concise (under 550 words), and avoid sensationalism. Do not invent any numbers not present in the data.
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