import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))
df = pd.read_csv('data/processed/incidents_clean.csv')
df = df.rename(columns={'date': 'incident_date'})
df.to_sql('incidents', engine, if_exists='append', index=False)
print(f"Loaded {len(df)} rows into Supabase.")