import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

EXTRACTION_PROMPT = """You are extracting structured data about an Indian exam paper leak incident from a news article.
Return ONLY valid JSON, no markdown, no explanation, matching this exact structure:
{{
  "is_paper_leak": true or false,
  "date": "YYYY-MM-DD or null if unknown",
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
    prompt = EXTRACTION_PROMPT.format(title=article["title"], content=content)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    text = text.strip("```json").strip("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None