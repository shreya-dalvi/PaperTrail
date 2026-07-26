import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

EXTRACTION_PROMPT = """You are extracting structured data about an Indian exam paper leak incident from a news article.

The article was published on: {published_date}
If the article text mentions a specific incident date, use that. If not, use the published date above as your best estimate for "date" — do not return null for date unless absolutely no date information exists at all.

Return ONLY valid JSON, no markdown, no explanation, matching this exact structure:
{{
  "is_paper_leak": true or false,
  "date": "YYYY-MM-DD or null only if truly no date is available",
  "exam_name": "string or null",
  "conducting_body": "string or null",
  "state": "string or null",
  "leak_status": "Confirmed/Alleged/Denied/Suspected or null",
  "action_taken": "string or null",
  "note": "one sentence summary"
}}

News title: {title}
Article content: {content}
"""

def extract_incident(article):
    content = article.get("full_text") or article.get("summary", "")
    published_date = article.get("published_date") or "unknown"
    prompt = EXTRACTION_PROMPT.format(
        title=article["title"],
        content=content,
        published_date=published_date
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    text = text.strip("```json").strip("```").strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return None

    # code-level fallback: if LLM still returned null, use the RSS published date
    if not result.get("date") and article.get("published_date"):
        result["date"] = article["published_date"]

    return result