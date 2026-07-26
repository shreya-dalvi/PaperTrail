import os
import uuid
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from news_scraper import fetch_news, fetch_article_text
from extractor import extract_incident

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def get_existing_urls():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT source_url FROM incidents"))
        return set(row[0] for row in result)

def run_research_agent():
    existing_urls = get_existing_urls()
    articles = fetch_news()
    new_count = 0

    for article in articles:
        if article["link"] in existing_urls:
            continue  # already have this one, skip

        article["full_text"] = fetch_article_text(article["link"])
        data = extract_incident(article)

        if not data or not data.get("is_paper_leak"):
            continue

        # skip if extraction is too thin to be useful
        useful_fields = [data.get("exam_name"), data.get("state"), data.get("conducting_body")]
        if all(f is None for f in useful_fields):
            continue

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO incidents (
                    incident_id, incident_date, exam_name, conducting_body,
                    area, state_clean, leak_status, action_taken, note,
                    source_name, source_url, confidence, detected_at
                ) VALUES (
                    :incident_id, :incident_date, :exam_name, :conducting_body,
                    :area, :state_clean, :leak_status, :action_taken, :note,
                    :source_name, :source_url, :confidence, now()
                )
            """), {
                "incident_id": f"PL-AUTO-{uuid.uuid4().hex[:8]}",
                "incident_date": data.get("date"),
                "exam_name": data.get("exam_name"),
                "conducting_body": data.get("conducting_body"),
                "area": data.get("state"),
                "state_clean": data.get("state"),
                "leak_status": data.get("leak_status"),
                "action_taken": data.get("action_taken"),
                "note": data.get("note"),
                "source_name": "Google News (auto-detected)",
                "source_url": article["link"],
                "confidence": "Auto-Detected"
            })
            conn.commit()
        new_count += 1

    print(f"Research agent run complete. {new_count} new incidents added.")

if __name__ == "__main__":
    run_research_agent()